import os
from pathlib import Path

path = Path("./")

with open(path / "test.py", mode='w+') as f:
  f.write("Hello world")
  f.write("Test program")

