"""Install a checksum-pinned official VeriFast distribution in project runtime."""
import hashlib,json,platform,tarfile,tempfile,urllib.request
from pathlib import Path
VERSION='26.10'
ASSETS={
 ('Darwin','arm64'):('macos-aarch','65570fca1aca14c5372c4f5e0ff5b5e6b6325021f011f84bda851754771d82c3'),
 ('Linux','x86_64'):('linux','5ad2a65997457fd5996a27f93107ef7e52c90c0d12b63b6e67f7acbc73e90efd'),
}

def main():
    system=(platform.system(),platform.machine())
    if system not in ASSETS:raise SystemExit('Use the linux/amd64 Docker service for this platform.')
    asset,digest=ASSETS[system];root=Path(__file__).resolve().parents[1]/'runtime/tools/verifast';root.mkdir(parents=True,exist_ok=True)
    target=root/('verifast-'+VERSION)
    if (target/'bin/verifast').is_file():print(target/'bin/verifast');return
    url=f'https://github.com/verifast/verifast/releases/download/{VERSION}/verifast-{VERSION}-{asset}.tar.gz'
    with tempfile.TemporaryDirectory(dir=root) as temp:
        archive=Path(temp)/'release.tar.gz';print('Downloading official VeriFast '+VERSION,flush=True)
        with urllib.request.urlopen(url,timeout=120) as response,archive.open('wb') as out:
            while chunk:=response.read(1024*1024):out.write(chunk)
        with archive.open('rb') as payload:actual=hashlib.file_digest(payload,'sha256').hexdigest()
        if actual!=digest:raise SystemExit('Release checksum mismatch')
        with tarfile.open(archive) as source:source.extractall(root,filter='data')
    if not (target/'bin/verifast').is_file():raise SystemExit('Unexpected release layout; binary missing')
    (root/'installation.json').write_text(json.dumps({'version':VERSION,'source':url,'sha256':digest},indent=2))
    print(target/'bin/verifast')

if __name__=='__main__':main()
