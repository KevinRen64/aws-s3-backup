import subprocess
import sys

def test_module_help_runs():
  r = subprocess.run(
    [sys.executable, "-m", "s3_backup", "--help"],
    capture_output=True,
    text=True,
  )
  assert r.returncode == 0, r.stderr
