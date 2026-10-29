"""Install isolated API-authenticated Agent SDKs (never uses globally installed CLIs)."""
from pathlib import Path
import shutil
import subprocess
root=Path(__file__).resolve().parents[1]
dest=root/'runtime/agent-runtime';dest.mkdir(parents=True,exist_ok=True)
for name in ('package.json','package-lock.json'):shutil.copyfile(root/'configs/agent-runtime'/name,dest/name)
subprocess.run(['npm','ci','--prefix',str(dest)],check=True)
