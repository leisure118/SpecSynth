"""Install the workflow's pinned official Verus release with SHA256 verification."""
import hashlib
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile
import zipfile

VERSION = '0.2026.01.10.531beb1'
ASSETS = {
    ('Darwin', 'arm64'): ('arm64-macos', 'cd3b283f11208dcf2e0d164b2f9f5d1474ab89d9fef6e704a5c5a06a2304b909', '1.92.0-aarch64-apple-darwin'),
    ('Darwin', 'x86_64'): ('x86-macos', '0235955601f0cd457b961139a81df51da338498f55f737bf8a398823162ce23d', '1.92.0-x86_64-apple-darwin'),
    ('Linux', 'x86_64'): ('x86-linux', '884533edf6a76954fe645bf261855c41b035004eb263767c4b3aa68cacad17f9', '1.92.0-x86_64-unknown-linux-gnu'),
    ('Windows', 'AMD64'): ('x86-win', '686e5a762975ae6690c2983ba859e683a6f1efd326532fe735ffed8b596f529f', '1.92.0-x86_64-pc-windows-msvc'),
}


def main():
    asset = ASSETS.get((platform.system(), platform.machine()))
    if not asset:
        raise SystemExit('该平台无此固定版本的预编译工具，请自行安装并设置 VERUS_EXECUTABLE。')
    target, digest, toolchain = asset
    if not shutil.which('rustup') or not shutil.which('curl'):
        raise SystemExit('请先安装 rustup 和 curl，再运行此脚本。')
    destination = Path(__file__).resolve().parents[1] / 'tools' / 'verus' / VERSION
    url = f'https://github.com/verus-lang/verus/releases/download/release/{VERSION}/verus-{VERSION}-{target}.zip'
    with tempfile.TemporaryDirectory() as directory:
        archive = Path(directory) / 'verus.zip'
        subprocess.run(['curl', '-fL', '--retry', '2', '--connect-timeout', '20', '--max-time', '600', '-o', str(archive), url], check=True)
        if hashlib.sha256(archive.read_bytes()).hexdigest() != digest:
            raise SystemExit('官方发布包 SHA256 不一致，停止安装。')
        with zipfile.ZipFile(archive) as bundle:
            for entry in bundle.infolist():
                output = (destination / entry.filename).resolve()
                if not output.is_relative_to(destination.resolve()):
                    raise SystemExit('发布包路径无效。')
                bundle.extract(entry, destination)
                mode = entry.external_attr >> 16
                if mode and os.name != 'nt':
                    output.chmod(mode)
    subprocess.run(['rustup', 'toolchain', 'install', toolchain, '--profile', 'minimal'], check=True)
    executable = destination / ('verus-' + target) / ('verus.exe' if os.name == 'nt' else 'verus')
    subprocess.run([str(executable), '--version'], check=True)
    print('Verus 安装完成。')


if __name__ == '__main__':
    main()
