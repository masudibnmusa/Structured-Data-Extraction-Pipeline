"""Confidence scoring.

Main signal: *source grounding* - does each extracted value actually appear in the
source text? Penalties are then applied for business-rule issues and schema errors.
LLM self-reported confidence is deliberately NOT used as the primary signal.
"""
import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation

# Fields the model legitimately paraphrases / normalises, so they can't be string-matched.
GROUNDING_EXEMPT = {"currency", "category", "summary", "action_items",
                    "payment_terms", "termination_summary", "role"}

_DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")


@dataclass
class ConfidenceReport:
    score: float
    grounded_ratio: float
    flags: list[str] = field(default_factory=list)


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def _date_variants(d: date) -> set[str]:
    out = {
        d.isoformat(),
        f"{d.day:02d}/{d.month:02d}/{d.year}", f"{d.month:02d}/{d.day:02d}/{d.year}",
        f"{d.day}/{d.month}/{d.year}", f"{d.month}/{d.day}/{d.year}",
        f"{d.day:02d}-{d.month:02d}-{d.year}", f"{d.day:02d}.{d.month:02d}.{d.year}",
    }
    for m in (d.strftime("%B").lower(), d.strftime("%b").lower()):
        out |= {f"{m} {d.day}, {d.year}", f"{m} {d.day} {d.year}", f"{d.day} {m} {d.year}",
                f"{d.day} {m}, {d.year}", f"{m} {d.day:02d}, {d.year}"}
    return out


def _number_variants(n: Decimal) -> set[str]:
    return {format(n.normalize(), "f"), f"{n:.2f}", f"{n:.1f}", f"{n:.0f}"}


def _leaves(obj, path=""):
    """Yield (path, key, value) for every scalar in a nested dict/list."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _leaves(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _leaves(v, f"{path}[{i}]")
    else:
        key = re.sub(r"\[\d+\]", "", path).split(".")[-1]
        yield path, key, obj


def _is_grounded(value, src: str, src_nocomma: str) -> bool:
    if isinstance(value, (int, float)):
        try:
            variants = _number_variants(Decimal(str(value)))
        except InvalidOperation:
            return True
        return any(re.search(rf"(?<![\d.]){re.escape(v)}(?!\d)", src_nocomma) for v in variants)

    text = str(value)
    m = _DATE_RE.match(text)
    if m:
        try:
            d = date(int(m[1]), int(m[2]), int(m[3]))
            return any(v in src for v in _date_variants(d))
        except ValueError:
            pass
    return _norm(text) in src


def score_confidence(data: dict, source_text: str, issues: list[str],
                     schema_errors: list[str]) -> ConfidenceReport:
    src = _norm(source_text)
    src_nocomma = src.replace(",", "")

    checked, grounded, flags = 0, 0, []
    for path, key, value in _leaves(data):
        if value is None or isinstance(value, bool) or key in GROUNDING_EXEMPT:
            continue
        checked += 1
        if _is_grounded(value, src, src_nocomma):
            grounded += 1
        else:
            flags.append(f"ungrounded:{path}")

    ratio = grounded / checked if checked else 0.0
    score = ratio - 0.15 * len(issues) - (0.30 if schema_errors else 0.0)
    return ConfidenceReport(score=round(max(0.0, min(1.0, score)), 3),
                            grounded_ratio=round(ratio, 3), flags=flags)