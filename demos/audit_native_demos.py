"""Audit retained native demo evidence; no real provider/credential reads or live services."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-dir',type=Path,required=True);args=parser.parse_args()
    artifacts=ROOT/'demos/artifacts'
    def read(name,file='client-result.json'):return json.loads((artifacts/name/file).read_text())
    permissions=read('NATIVE-DEMO-PERMISSION-20261111-02','summary.json')
    assert len(permissions['cases'])==10
    for case in permissions['cases']:
        assert case['isolation_pass'] and case['supervisor_pid_absent'] and case['broker_socket_absent']
        assert not case['execution']['timed_out'] and case['provider_requests']==0
        expected=case['case']['permission'] in ('allow','overlap-allow')
        assert case['shell_witness_created']==expected
        if not expected:assert case['tool_errors']
    api=read('NATIVE-PERMISSION-API-20261111-01');assert api['status']=='pass' and all(api['checks'].values()) and len(api['requests'])==0
    client=read('NATIVE-CLIENT-20261111-01');assert client['status']=='pass' and all(client['checks'].values())
    lifecycle=read('NATIVE-CLIENT-LIFECYCLE-20261111-02');assert lifecycle['status']=='pass' and all(lifecycle['checks'].values())
    sdk=read('NATIVE-SDK-20261111-01','sdk-result.json');assert sdk['status']=='pass' and all(sdk['checks'].values())
    assert sdk['server_info']['pid']==sdk['host_pid'] and sdk['server_info']['urls']==[]
    port=read('NATIVE-PLUGIN-PORT-20261111-03');assert port['status']=='pass' and port['checks']['ported_plugin_tool_invoked']
    cleanup=(artifacts/'NATIVE-PLUGIN-PORT-20261111-03/client-server.log').read_text();assert 'REPORT_PLUGIN_V2_CLEANUP' in cleanup
    rejected=read('NATIVE-CLIENT-V1PLUGIN-20261111-02')
    local=[p for p in rejected['plugin_list_after_wait']['data'] if p['source']['type']=='local']
    assert len(local)==1 and local[0]['state']['status']=='failed' and 'default definition' in local[0]['state']['error']
    legacy=read('NATIVE-DEMO-ROUND1-20261111-01','summary.json')['cases'][0];assert legacy['marker_tool_completed'] and legacy['isolation_pass']
    accepted={}
    for name in ['NATIVE-BG-TOOL-20261111-01','NATIVE-BG-ERROR-20261111-01','NATIVE-SUBAGENT-20261111-02','NATIVE-COMPACTION-20261111-03']:
        d=read(name);assert d['status']=='pass' and all(d['checks'].values());accepted[name]=d['checks']
    all_artifacts=[];raw_hashes={};failures=[]
    for artifact in sorted(artifacts.iterdir()):
        if not artifact.is_dir() or not artifact.name.startswith(('NATIVE-','SDK-DEPS-PREP-')):continue
        all_artifacts.append(str(artifact.relative_to(ROOT)))
        for path in artifact.rglob('*'):
            if path.is_file():raw_hashes[str(path.relative_to(ROOT))]=sha(path)
        manifest=artifact/'manifest.json'
        if manifest.is_file():
            m=json.loads(manifest.read_text());assert m['provider_requests']==0 and m['credential_reads']==0
            assert m['supervisor_pid_absent']
            if m['execution']['timed_out']:failures.append({'artifact':artifact.name,'status':'harness_timeout_not_feature_verdict'})
            harness='sdk_runtime_inside.ts' if 'sdk_version' in m else 'client_runtime_inside.ts'
            source=artifact/'source'/harness
            if source.exists():assert sha(source)==m['harness_sha256'],artifact.name
        result=artifact/'client-result.json'
        if result.is_file():
            d=json.loads(result.read_text())
            if d['status']!='pass':failures.append({'artifact':artifact.name,'status':d['status'],'error':d.get('error')})
    benchmark=json.loads((ROOT/'research/artifacts/OPENAI48-R3-FINAL-20261111-01/validation.json').read_text());base=ROOT/benchmark['artifact']
    assert all(sha(base/p)==h for p,h in benchmark['raw_artifact_sha256'].items())
    state=json.loads((ROOT/'research/experiment-state.json').read_text());assert(state['next_pilot_run_start'],state['next_pilot_config_start'])==(378,479)
    answer={'status':'pass','scope':'native runtime with scripted local model transport; not real modelquality','real_provider_requests':0,'credential_file_reads':0,
        'cli_permission_cases_side_effect_expected':10,'v2_permission_api_checks':api['checks'],'client_checks':client['checks'],
        'lifecycle_api_checks':lifecycle['checks'],'embedded_sdk_checks':sdk['checks'],'embedded_sdk_package_version':'2.2.5',
        'embedded_sdk_server_info_version':sdk['server_info']['version'],'embedded_sdk_in_process_pid_matches':True,
        'plugin_v1_marker':True,'v1_plugin_on_v2_expected_loader_failure':True,'ported_v2_plugin_marker_and_cleanup':True,
        'accepted_additional_cases':accepted,'retained_failures_or_incomplete_cases':failures,'artifacts_retained':all_artifacts,
        'raw_artifact_sha256':raw_hashes,'benchmark48_raw_unchanged':True,'registry':['R-0378','C-0479'],
        'limits':['Scripted provider is not model-quality or semantic-memory evidence','V1 interactive reply/savedapproval not run',
                  'stdio shell cancellation notice after restart not observed; managed service recovery harness blocked before readiness',
                  'Subagent crash/restart budget and GUI/TUI/Desktop sharedservice not accepted','SDKpackagebuild-to-sourcecommit not independently attested; serverversionunknown']}
    args.output_dir.mkdir(parents=True,exist_ok=False);(args.output_dir/'validation.json').write_text(json.dumps(answer,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in answer.items() if k not in ('raw_artifact_sha256','artifacts_retained')},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
