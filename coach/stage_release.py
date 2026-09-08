"""Stage a committed local release and launchd definition; never start a consumer.

Run after committing and checking the source. The PM separately verifies timezone,
OpenClaw ownership, Telegram offset, then bootstraps the prepared launch agent.
"""
import argparse
import io
import os
from pathlib import Path
import plistlib
import subprocess
import sys
import tarfile

LABEL='com.briqtraining.coach'

def stage(runtime):
    repo=Path(__file__).resolve().parents[1]
    if subprocess.check_output(['git','status','--porcelain','--','coach'],cwd=repo,text=True).strip():
        raise SystemExit('Commit the coach source before staging a release')
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
    runtime=runtime.expanduser().resolve()
    for name in ('','releases','state','backups','workspace'):
        folder=runtime/name;folder.mkdir(parents=True,exist_ok=True);folder.chmod(0o700)
    destination=runtime/'releases'/revision
    if not destination.exists():
        archive=subprocess.check_output(['git','archive',revision,'coach'],cwd=repo)
        destination.mkdir(mode=0o700)
        with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
            for member in bundle.getmembers():
                target=(destination/member.name).resolve()
                if not str(target).startswith(str(destination)+'/') or not (member.isdir() or member.isfile()):
                    raise SystemExit('Unexpected archive member')
            bundle.extractall(destination)
    plist={
        'Label':LABEL,
        'ProgramArguments':['/usr/bin/caffeinate','-i',sys.executable,str(destination/'coach/service.py'),'--runtime',str(runtime)],
        'WorkingDirectory':str(runtime/'workspace'),
        'RunAtLoad':True,'KeepAlive':True,'ThrottleInterval':30,
        'StandardOutPath':str(runtime/'state/service.log'),
        'StandardErrorPath':str(runtime/'state/service.log'),
        'EnvironmentVariables':{'HOME':str(Path.home()),'PATH':'/usr/bin:/bin:/usr/local/bin','PYTHONUNBUFFERED':'1'},
        'Umask':0o077,
    }
    path=runtime/(LABEL+'.plist')
    path.write_bytes(plistlib.dumps(plist));path.chmod(0o600)
    (runtime/'staged-release.txt').write_text(revision+'\n')
    print('Staged release '+revision+'; launch agent prepared but not loaded: '+str(path))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--runtime',type=Path,default=Path.home()/'.local/share/briq-coach')
    stage(parser.parse_args().runtime)
