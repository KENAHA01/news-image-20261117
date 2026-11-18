"""Render the 2048x2048 preview of the entry, natively.

The bounty gate caps the submitted file at 1024x1024 and 1 MiB, so
entry.png stays 1024x1024 and is the file main.py copies to the
output. This script renders the same layout natively at 2048x2048
by running make_image.py with MAKEFUN_SCALE=2 (the layout code works
in 1024 units and a ScaledDraw wrapper draws it at 2x resolution).
It is not an upscale, and it is not part of the submission.
"""

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
env = dict(os.environ, MAKEFUN_SCALE="2")
r = subprocess.run([sys.executable, str(HERE / "make_image.py")],
                   env=env, check=False)
sys.exit(r.returncode)
