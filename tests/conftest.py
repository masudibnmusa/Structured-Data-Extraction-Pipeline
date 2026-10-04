import os
import tempfile

# Must be set BEFORE app.config is imported
_tmp = tempfile.mkdtemp()
os.environ["DATA_DIR"] = _tmp
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["CONFIDENCE_THRESHOLD"] = "0.85"
os.environ["LLM_API_KEY"] = "test-key"

import pytest  # noqa: E402

from app.storage.models import init_db  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _database():
    init_db()