"""Render the 2048x2048 preview of the entry.

The bounty gate caps the submitted file at 1024x1024 and 1 MiB, so
entry.png stays 1024x1024 and is the file main.py copies to the
output. This script only makes a larger preview (entry-2048.png) for
viewing, by upscaling the 1024 render with LANCZOS. It is not part
of the submission.
"""

from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
src = Image.open(HERE / "entry.png")
assert src.size == (1024, 1024), src.size
preview = src.resize((2048, 2048), Image.LANCZOS)
preview.save(HERE / "entry-2048.png", optimize=True)
print("saved", HERE / "entry-2048.png",
      (HERE / "entry-2048.png").stat().st_size, "bytes")
