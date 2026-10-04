"""Run with:  streamlit run app/review_queue/review_ui.py"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st  # noqa: E402

from app.review_queue import queue_manager as qm  # noqa: E402
from app.storage.models import init_db  # noqa: E402

init_db()
st.set_page_config(page_title="Extraction Review", layout="wide")
st.title("Extraction review queue")

pending = qm.list_pending()
if not pending:
    st.success("Nothing to review.")
    st.stop()

st.sidebar.metric("Pending", len(pending))
labels = {f"{r['doc_type']} | {r['id'][:8]} | conf {r['confidence']:.2f}": r for r in pending}
rec = labels[st.sidebar.selectbox("Record", list(labels))]

if rec["flags"]:
    st.warning("Flags:\n\n" + "\n".join(f"- {f}" for f in rec["flags"]))

left, right = st.columns(2)
left.subheader("Source text")
left.text_area("source", rec["source_text"], height=550, disabled=True,
               key=f"src-{rec['id']}", label_visibility="collapsed")
right.subheader("Extracted data (editable)")
edited = right.text_area("data", json.dumps(rec["data"], indent=2), height=550,
                         key=f"data-{rec['id']}", label_visibility="collapsed")

approve_col, reject_col, _ = st.columns([1, 1, 4])
if approve_col.button("Approve", type="primary"):
    try:
        qm.approve(rec["id"], json.loads(edited), reviewer="streamlit")
        st.rerun()
    except (ValueError, json.JSONDecodeError) as exc:
        st.error(f"Cannot approve: {exc}")
if reject_col.button("Reject"):
    qm.reject(rec["id"], reason="rejected in UI")
    st.rerun()