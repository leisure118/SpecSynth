"""Explicit tool location profiles; model credentials stay in private .env."""
from pathlib import Path
from dotenv import load_dotenv
ROOT=Path(__file__).resolve().parents[2]

def apply_runtime_profile(name):
    if name not in ('local','server'):raise ValueError('Runtime profile must be local or server')
    # Load credentials first; override only the public, fixed tool selectors.
    load_dotenv(ROOT/'.env',override=False)
    path=ROOT/'configs/runtime'/(name+'.env')
    if not path.is_file():raise FileNotFoundError(path)
    load_dotenv(path,override=True)
