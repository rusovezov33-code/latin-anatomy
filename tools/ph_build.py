# -*- coding: utf-8 -*-
import subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
for name in ("ph_data_gen.py", "ph_patch.py", "ph_verify.py"):
    print("==>", name)
    subprocess.check_call([sys.executable, str(HERE / name)])
