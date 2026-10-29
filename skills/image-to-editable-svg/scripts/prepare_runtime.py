#!/usr/bin/env python3
"""Prepare an isolated versioned runtime, preserving any existing environment."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python', default=sys.executable)
    args = parser.parse_args()
    requirements = Path(__file__).resolve().parents[1] / 'requirements.txt'
    digest = hashlib.sha256(requirements.read_bytes()).hexdigest()[:16]
    codex_dir = Path(os.environ.get('CODEX_HOME', Path.home() / '.codex')).expanduser()
    target = codex_dir / 'skill-toolboxes/runtimes/image-to-editable-svg' / digest / 'venv'
    executable = target / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    desired = dict(line.split('==') for line in requirements.read_text().splitlines() if line.strip())
    check = ('import sys,json,importlib.metadata as m; assert sys.version_info >= (3,11); '
             'print(json.dumps({k:m.version(k) for k in ' + repr(list(desired)) + '}))')
    reused = target.exists()
    if not reused:
        subprocess.run([args.python, '-c', 'import sys; assert sys.version_info >= (3,11)'], check=True)
        target.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([args.python, '-m', 'venv', str(target)], check=True)
        subprocess.run([str(executable), '-m', 'pip', 'install', '-r', str(requirements)], check=True)
    installed = json.loads(subprocess.check_output([str(executable), '-c', check], text=True))
    if installed != desired:
        raise ValueError('Existing environment differs; preserve it and review before repair.')
    print(json.dumps({'python': str(executable), 'reused': reused, 'versions': installed}))


if __name__ == '__main__':
    main()
