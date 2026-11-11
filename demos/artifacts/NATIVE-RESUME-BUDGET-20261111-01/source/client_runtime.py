"""Export pinned Promise Client source and run it with a private native v2 server offline."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'benchmark'))
import batch48 as batch

SHA = '9bbb8ce18c80f099e0e448775f59d965ead40a21'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact-dir', type=Path, required=True)
    parser.add_argument('--plugin-case', choices=['v1','v2'])
    parser.add_argument('--mode', choices=['lifecycle','permission','background-tool','background-error','background-restart','background-service-restart','compaction','subagent','subagent-service-restart','budget-service-restart'], default='lifecycle')
    args = parser.parse_args(); artifact = args.artifact_dir.resolve()
    if not artifact.is_relative_to(ROOT / 'demos/artifacts'):parser.error('Fresh demos artifact path required')
    artifact.mkdir(parents=True, exist_ok=False)
    spec = next(s for s in json.loads((ROOT / 'demos/artifacts/PREP-20261106-01/preparation.json').read_text())['releases'] if s['tool'] == 'opencode-v2')
    config_id = 'BP48-CL-' + hashlib.sha256(artifact.name.encode()).hexdigest()[:20]
    spec, root, nonce, command, cli = batch.prepare(spec, config_id, 'B-02')
    if args.plugin_case:
        from native_demo_round1 import configure
        configure(root, {'tool':'opencode-v2','plugin':args.plugin_case})
    if args.mode.startswith('subagent'):
        config_path=root/'xdg-config/opencode/opencode.json';cfg=json.loads(config_path.read_text())
        cfg['permissions'].append({'action':'subagent','resource':'*','effect':'allow'})
        cfg['agents']={'report_child':{'mode':'subagent','description':'Bounded scripted research child',
            'system':'Return the fixed research child marker; do not use tools.',
            'permissions':[{'action':'*','resource':'*','effect':'deny'}]}}
        batch.native.write(config_path,cfg)
    shutil.copyfile(ROOT/'demos/fixtures/background_worker.py', root/'background_worker.py')
    shutil.copyfile(ROOT/'demos/fixtures/background_worker.py', root/'project/background_worker.py')
    source = root / 'client-source'; source.mkdir()
    repo = ROOT.parent / 'opencode-v2'
    paths = subprocess.check_output(['git','ls-tree','-r','--name-only',SHA,'packages/client/src'],cwd=repo,text=True).splitlines()
    source_hashes = {}
    for name in paths:
        relative = Path(name).relative_to('packages/client/src')
        target = source / relative; target.parent.mkdir(parents=True, exist_ok=True)
        data = subprocess.check_output(['git','show',SHA+':'+name],cwd=repo); target.write_bytes(data)
        source_hashes[name] = hashlib.sha256(data).hexdigest()
    marker = {'type':'message','id':'msg_client_demo','role':'assistant','status':'completed',
              'content':[{'type':'output_text','text':'REPORT_CLIENT_ASSISTANT_MARKER','annotations':[]}]}
    (root / 'response.sse').write_bytes(batch.native.sse([marker], 1))
    call = {'type':'function_call','id':'fc_client_plugin','call_id':'call_client_plugin','status':'completed',
            'name':'report_marker','arguments':'{}'}
    (root / 'plugin-call.sse').write_bytes(batch.native.sse([call], 2))
    call['name'] = 'execute'
    call['arguments'] = json.dumps({'code':'return await tools.report_marker()'})
    (root / 'plugin-execute.sse').write_bytes(batch.native.sse([call], 3))
    call['name']='shell'
    worker_command='python3 -u background_worker.py --steps 30'
    if args.mode=='background-error':worker_command+=' --mode error'
    call['arguments']=json.dumps({'command':worker_command,'background':True})
    (root/'background-call.sse').write_bytes(batch.native.sse([call],4))
    summary_text='## Objective\n- REPORT_COMPACT_SUMMARY\n\n## Requirements\n- invariant=REPORT_RETAIN_ME\n\n## Decisions\n- (none)\n\n## Work State\n### Completed\n- Native fixture prompt\n### Active\n- (none)\n### Blocked\n- (none)\n\n## Next Move\n1. Continue\n\n## Relevant Files\n- (none)\n\n## Important Context\n- REPORT_CLIENT_USER_SEED'
    summary_marker={**marker,'id':'msg_compaction_fixture','content':[{'type':'output_text',
        'text':summary_text,'annotations':[]}]}
    (root/'compaction.sse').write_bytes(batch.native.sse([summary_marker],5))
    call['name']='subagent';call['arguments']=json.dumps({'agent':'report_child','description':'Scripted independent child',
        'prompt':'REPORT_SUBAGENT_CHILD_SEED','background':True})
    (root/'subagent-call.sse').write_bytes(batch.native.sse([call],6))
    child_marker={**marker,'id':'msg_child_fixture','content':[{'type':'output_text','text':'REPORT_SUBAGENT_CHILD_MARKER','annotations':[]}]}
    (root/'subagent-response.sse').write_bytes(batch.native.sse([child_marker],7))
    # Replace bridge/CLI launcher with an owned client/private-server controller.
    at = command.index('/usr/bin/python3'); command = command[:at]
    bun = Path(shutil.which('bun') or '').resolve(); assert bun.is_file()
    harness = ROOT / 'demos/client_runtime_inside.ts'
    (artifact/'source').mkdir()
    shutil.copyfile(harness,artifact/'source/client_runtime_inside.ts')
    shutil.copyfile(Path(__file__),artifact/'source/client_runtime.py')
    command += ['--ro-bind',str(bun),'/opt/research/bun','--ro-bind',str(source),'/opt/research/client',
        '--ro-bind',str(harness),'/opt/research/client_runtime_inside.ts',
        '/opt/research/bun','/opt/research/client_runtime_inside.ts',cli[0],args.mode]
    execution = batch.native.execute(command, root, timeout=60 if args.mode=='background-service-restart' else 120)
    (artifact / 'stdout.txt').write_text(execution.pop('stdout').replace(nonce,'[LOCAL-TOKEN]'))
    (artifact / 'stderr.txt').write_text(execution.pop('stderr').replace(nonce,'[LOCAL-TOKEN]'))
    if (root/'client-result.json').exists():
        shutil.copyfile(root/'client-result.json',artifact/'client-result.json')
    for name in ['client-server.log','demo-progress.json']:
        if (root/name).exists():(artifact/name).write_bytes((root/name).read_bytes())
    batch.native.write(artifact/'manifest.json',{'scope':'offline native TypeScript Promise Client, not embedded SDK',
        'provider_requests':0,'credential_reads':0,'source_commit':SHA,'source_hashes':source_hashes,'spec':spec,
        'bun_sha256':batch.digest(bun),'harness_sha256':batch.digest(harness),'execution':execution,
        'supervisor_pid_absent':not Path('/proc',str(execution['supervisor_host_pid'])).exists(),
        'no_dependencies_installed':True,'source_repos_read_only':True})
    print(json.dumps({'exit_code':execution['exit_code'],'timeout':execution['timed_out'],
                     'result_present':(artifact/'client-result.json').exists()}))


if __name__ == '__main__':
    main()
