"""Run installed exact-version embedded SDK in a fresh offline namespace, not a source repo."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'benchmark'))
import batch48 as batch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact-dir', type=Path, required=True)
    parser.add_argument('--mode', choices=['prompt','failure-matrix'], default='prompt')
    args = parser.parse_args(); artifact = args.artifact_dir.resolve()
    if not artifact.is_relative_to(ROOT/'demos/artifacts'):parser.error('Fresh demos artifact directory required')
    project = ROOT/'.local/demo-sdk-2.2.5'
    sdk = project/'node_modules/@opencode/sdk/package.json'; assert json.loads(sdk.read_text())['version']=='2.2.5'
    artifact.mkdir(parents=True, exist_ok=False)
    spec = next(s for s in json.loads((ROOT/'demos/artifacts/PREP-20261106-01/preparation.json').read_text())['releases'] if s['tool']=='opencode-v2')
    cid='BP48-SDK-'+hashlib.sha256(artifact.name.encode()).hexdigest()[:20]
    spec,root,nonce,command,cli=batch.prepare(spec,cid,'B-02')
    item={'type':'message','id':'msg_sdk_demo','role':'assistant','status':'completed',
          'content':[{'type':'output_text','text':'REPORT_SDK_ASSISTANT_MARKER','annotations':[]}]}
    (root/'sdk-response.sse').write_bytes(batch.native.sse([item],1))
    command=command[:command.index('/usr/bin/python3')]
    bun=Path(shutil.which('bun')).resolve();harness=ROOT/'demos/sdk_runtime_inside.ts'
    command+=['--ro-bind',str(bun),'/opt/research/bun','--ro-bind',str(project),'/opt/research/sdk',
              '--ro-bind',str(harness),'/opt/research/sdk_runtime_inside.ts',
              '--ro-bind',str(ROOT/'demos/failure_matrix.ts'),'/opt/research/failure_matrix.ts',
              '/opt/research/bun','/opt/research/sdk_runtime_inside.ts',args.mode]
    (artifact/'source').mkdir();shutil.copyfile(harness,artifact/'source/sdk_runtime_inside.ts');shutil.copyfile(Path(__file__),artifact/'source/sdk_runtime.py')
    shutil.copyfile(ROOT/'demos/failure_matrix.ts',artifact/'source/failure_matrix.ts')
    execution=batch.native.execute(command,root,timeout=120)
    (artifact/'stdout.txt').write_text(execution.pop('stdout').replace(nonce,'[LOCAL-TOKEN]'))
    (artifact/'stderr.txt').write_text(execution.pop('stderr').replace(nonce,'[LOCAL-TOKEN]'))
    if(root/'sdk-result.json').exists():shutil.copyfile(root/'sdk-result.json',artifact/'sdk-result.json')
    packages={str(p.relative_to(project)):batch.digest(p) for p in (project/'node_modules').rglob('package.json') if p.is_file()}
    batch.native.write(artifact/'manifest.json',{'scope':'embedded SDK2.2.5 offline; no real provider, no source repo changes',
        'provider_requests':0,'credential_reads':0,'sdk_version':'2.2.5','package_json_sha256':packages,
        'harness_sha256':batch.digest(harness),'bun_sha256':batch.digest(bun),'spec':spec,'execution':execution,
        'supervisor_pid_absent':not Path('/proc',str(execution['supervisor_host_pid'])).exists(),
        'lifecycle_scripts_during_install':False})
    print(json.dumps({'exit_code':execution['exit_code'],'timeout':execution['timed_out'],'result_present':(artifact/'sdk-result.json').exists()}))


if __name__=='__main__':main()
