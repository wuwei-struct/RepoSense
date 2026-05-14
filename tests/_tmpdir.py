import os
import uuid
from pathlib import Path


def get_test_temp_root() -> Path:
    """
    Return stable writable temp root under repo workspace.
    """
    root = Path(os.getcwd()) / ".tmp_test_runs" / "temp"
    root.mkdir(parents=True, exist_ok=True)
    return root


def make_test_temp_dir(prefix: str = "tmp_") -> Path:
    """
    Create unique writable temp directory under test temp root.
    """
    base = get_test_temp_root()
    path = base / f"{prefix}{uuid.uuid4().hex[:10]}"
    path.mkdir(parents=False, exist_ok=False)
    return path


def make_temp_dir(prefix: str) -> str:
    """
    Backward-compatible helper returning str path.
    """
    return str(make_test_temp_dir(prefix=prefix))
