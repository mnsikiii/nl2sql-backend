"""Backward-compatible wrapper. Use scripts/run_summary_eval.py."""
from pathlib import Path
import runpy

if __name__ == "__main__":
    script_path = Path(__file__).resolve().parent / "scripts" / "run_summary_eval.py"
    runpy.run_path(str(script_path), run_name="__main__")
