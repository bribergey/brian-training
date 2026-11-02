"""Copy and verify an installed CLI package; never modify config or start Coach."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ENTRY = Path('CodexCLI.app/Contents/MacOS/codex')


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''): result.update(chunk)
    return result.hexdigest()


def inventory(folder):
    result = {}
    for path in sorted(folder.rglob('*')):
        if path.is_symlink():
            raise ValueError('Runtime package must not depend on external symlinks')
        if path.is_file(): result[str(path.relative_to(folder))] = digest(path)
    return result


def verify(binary, runtime):
    binary = Path(binary).expanduser().resolve()
    runtimes = Path(runtime).expanduser().resolve() / 'runtimes'
    relative = binary.relative_to(runtimes)
    release = runtimes / relative.parts[0]
    manifest = json.loads((release / 'manifest.json').read_text())
    package = release / 'codex-cli'
    if binary != package / ENTRY or inventory(package) != manifest['files']:
        raise ValueError('Pinned runtime integrity verification failed')
    return manifest


def pin(source, runtime):
    source = Path(source).expanduser().resolve()
    if not (source / ENTRY).is_file(): raise ValueError('Select the installed codex-cli package directory')
    version = subprocess.check_output([str(source / ENTRY), '--version'], text=True, timeout=20).strip()
    files = inventory(source)
    package_hash = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()
    identifier = re.sub(r'[^A-Za-z0-9._-]', '-', version) + '-' + package_hash[:16]
    runtimes = Path(runtime).expanduser().resolve() / 'runtimes'
    runtimes.mkdir(parents=True, exist_ok=True, mode=0o700)
    destination = runtimes / identifier
    if not destination.exists():
        temporary = Path(tempfile.mkdtemp(prefix='.pin-', dir=runtimes))
        try:
            shutil.copytree(source, temporary / 'codex-cli')
            if inventory(temporary / 'codex-cli') != files:
                raise ValueError('Installed CLI changed during copy; retry after its update finishes')
            manifest = {'version': version, 'package_sha256': package_hash, 'files': files}
            (temporary / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
            (temporary / 'manifest.json').chmod(0o600)
            temporary.rename(destination)
        finally:
            if temporary.exists(): shutil.rmtree(temporary)
    binary = destination / 'codex-cli' / ENTRY
    verify(binary, runtime)
    copied_version = subprocess.check_output([str(binary), '--version'], text=True, timeout=20).strip()
    if copied_version != version: raise ValueError('Copied runtime version differs')
    return binary, version


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--runtime', type=Path, default=Path.home()/'.local/share/briq-coach')
    args = parser.parse_args()
    binary, version = pin(args.source, args.runtime)
    print(json.dumps({'codex_binary': str(binary), 'version': version}))
