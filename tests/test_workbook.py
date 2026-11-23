"""Real CLI fixtures. All clients, answers and approval statements here are fictional."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO=Path(__file__).resolve().parents[1]
SCRIPT=REPO/'scripts/workbook.py'

def cli(root,*args,ok=True):
    cmd=[sys.executable,str(SCRIPT)]
    if root:cmd+=['--workspace',str(root)]
    r=subprocess.run(cmd+list(args),capture_output=True,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
    if ok and r.returncode:raise AssertionError(r.stdout+r.stderr)
    if not ok and r.returncode==0:raise AssertionError('Expected refusal: '+str(args)+'\n'+r.stdout)
    return r

def jwrite(p,value):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,indent=2)+'\n')
def read(p):return json.loads(p.read_text())
def build_fixture(parent,cid,channels):
    client=parent/cid
    cli(None,'init','--id',cid,'--name','Fictional '+cid,'--destination',str(client))
    source=parent/(cid+'-owner-export.csv');source.write_text('date,channel,visits\n2026-01-01,website,12\n2026-01-02,website,15\n')
    bank=read(REPO/'_shared/questions.json')
    for g in bank['groups']:
        if g['channel'] and g['channel'] not in channels:continue
        for q in g['questions']:
            if not q['required']:continue
            value='Fictional supplied context for '+q['id']+'. No real client claim or live-action permission.'
            if q['id']=='engagement.approver':value='Example Reviewer'
            elif q['id']=='audience.primary':value='Household customers seeking this fictional local service.'
            elif q['id']=='authority.actions':value='Local research and drafts only; Example Reviewer retains all live actions.'
            elif q['id']=='channels.reviewers':value='Example Reviewer reviews audience fit and facts for each selected channel. Missing review blocks release.'
            elif q['id']=='sources.locations':value=json.dumps([str(source)])
            elif q['id']=='sources.owners':value='Example Data Owner'
            elif q['type']=='channels':value=json.dumps(channels)
            elif q['type']=='list':value=json.dumps(['Manual local procedure; no existing integration or external write authority.'])
            cli(client,'answer','--question',q['id'],'--value',value,'--basis','human-decision' if q['decision'] else 'supplied-fact','--by','Example Reviewer')
    cli(client,'brief');digest=read(client/'onboarding/03_brief/output/brief-state.json')['brief_sha256']
    cli(client,'approve-brief','--sha256',digest,'--by','Example Reviewer','--statement','I approve this fictional test brief.')
    cli(client,'build');digest=read(client/'onboarding/04_workspace/output/workspace-manifest.json')['workspace_sha256']
    cli(client,'accept-workspace','--sha256',digest,'--by','Example Reviewer','--statement','I accept this fictional test workspace.')
    cli(client,'check','--accepted')
    return client,source

class WorkbookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='client-icm-tests-')
        cls.base=Path(cls.temp.name)
        cls.accepted,cls.source=build_fixture(cls.base,'fictional-harbor',['website','social'])
        cls.other,cls.other_source=build_fixture(cls.base,'fictional-maple',['blog','newsletter','youtube','linkedin'])
        cls.third,cls.third_source=build_fixture(cls.base,'fictional-orchard',['paid','seo','email','events'])
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def setUp(self):
        self.root=Path(tempfile.mkdtemp(prefix='case-',dir=self.base))/'client'
        shutil.copytree(self.accepted,self.root)
    def test_installed_tool_runs_without_template_repo(self):
        r=subprocess.run([sys.executable,str(self.root/'scripts/workbook.py'),'check','--accepted'],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(json.loads(r.stdout)['areas'],7)
        self.assertTrue((self.root/'deploy/HANDOFF.md').is_file())
        self.assertTrue((self.root/'monitoring/source-readback.template.json').is_file())
        self.assertTrue((self.root/'records/updates/live-receipt.template.json').is_file())
    def test_distinct_clients_have_distinct_context(self):
        self.assertNotEqual(read(self.accepted/'client.json')['id'],read(self.other/'client.json')['id'])
        self.assertFalse((self.accepted/'channels/newsletter.md').exists())
        self.assertTrue((self.other/'channels/newsletter.md').exists())
        self.assertNotIn('fictional-maple',(self.accepted/'onboarding/03_brief/output/client-brief.md').read_text())
    def test_every_concern_routes_to_real_owner_context(self):
        spec=importlib.util.spec_from_file_location('workbook_fixture',SCRIPT);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        for topic in m.TOPICS:
            r=json.loads(cli(self.root,'route','--topic',topic).stdout);self.assertTrue(Path(r['entry']).is_file())
    def test_selected_worker_reads_brand_and_reviewer(self):
        s=(self.other/'channels/newsletter.md').read_text();self.assertIn('../brand/strategy/positioning.md',s);self.assertIn('declared channel reviewer',s)
    def test_all_ten_channel_branches_build(self):
        for client,channels in [(self.accepted,['website','social']),(self.other,['blog','newsletter','youtube','linkedin']),(self.third,['paid','seo','email','events'])]:
            for channel in channels:self.assertTrue((client/'channels'/f'{channel}.md').is_file())
    def test_interview_limit_and_channel_branching(self):
        dest=self.base/('new-'+os.urandom(4).hex());cli(None,'init','--id','new-client','--name','Fictional New','--destination',str(dest))
        r=cli(dest,'interview').stdout
        self.assertLessEqual(len([x for x in r.splitlines() if x.startswith(('company.','engagement.'))]),3)
        self.assertNotIn('channels.youtube',r)
    def test_nonempty_target_is_preserved(self):
        dest=self.base/('occupied-'+os.urandom(4).hex());dest.mkdir();sentinel=dest/'keep.txt';sentinel.write_text('Keep this unrelated file.')
        cli(None,'init','--id','occupied','--name','Fictional','--destination',str(dest),ok=False);self.assertEqual(sentinel.read_text(),'Keep this unrelated file.')
    def test_public_repo_target_and_nested_client_refused(self):
        cli(None,'init','--id','private-client','--name','Fictional','--destination',str(REPO/'clients'/'must-not-exist'),ok=False)
        cli(None,'init','--id','nested-client','--name','Fictional','--destination',str(self.root/'nested'),ok=False)
        self.assertFalse((self.root/'nested').exists())
    def test_no_build_without_exact_brief_approval(self):
        (self.root/'onboarding/03_brief/output/brief-approval.json').unlink();cli(self.root,'build',ok=False)
    def test_changed_answers_and_brief_invalidate_approval(self):
        p=self.root/'onboarding/01_scope/output/answers.json';a=read(p);a['answers']['audience.primary']['value']='A materially different audience';jwrite(p,a)
        cli(self.root,'check','--accepted',ok=False)
    def test_client_identity_cannot_reuse_another_brief(self):
        p=self.root/'client.json';a=read(p);a['name']='Different fictional client';jwrite(p,a);cli(self.root,'check','--accepted',ok=False)
    def test_workspace_acceptance_and_manual_edits_preserved(self):
        p=self.root/'brand/identity/message.md';p.write_text(p.read_text()+'\nManual correction to preserve.\n');cli(self.root,'check','--accepted',ok=False);cli(self.root,'build',ok=False);self.assertIn('Manual correction',p.read_text())
    def test_wrong_approver_and_digest_refused(self):
        cli(self.root,'approve-brief','--sha256','0'*64,'--by','Another reviewer','--statement','I approve.',ok=False)
    def test_unknown_and_evidence_labels_need_context(self):
        cli(self.root,'answer','--question','brand.vision','--value','Unknown','--basis','unknown','--by','Example Reviewer',ok=False)
        cli(self.root,'answer','--question','brand.vision','--value','An assertion','--basis','evidence','--by','Example Reviewer',ok=False)
    def test_secret_value_and_secret_source_refused(self):
        secret='gh'+'p_'+'x'*38
        cli(self.root,'answer','--question','brand.vision','--value',secret,'--basis','supplied-fact','--by','Example Reviewer',ok=False)
        p=self.root/'.env';p.write_text('test fixture only; no real secret')
        cli(self.root,'register-source','--id','secret','--locator',str(p),'--owner','Example','--cadence','on change','--sensitivity','restricted','--public-use','never',ok=False)
    def review_source(self):
        local=self.root/'private/owner-export.csv';local.parent.mkdir(exist_ok=True);shutil.copyfile(self.source,local)
        cli(self.root,'register-source','--id','source-01','--locator',str(local),'--owner','Example Data Owner','--cadence','daily','--sensitivity','private','--public-use','aggregate only after review')
        import hashlib
        dt=datetime.now(timezone.utc);evidence=self.root/'private/owner-readback.json'
        r={'schema_version':1,'source_id':'source-01','locator':str(local),'owner':'Example Data Owner','result':'pass','checked_at':(dt-timedelta(minutes=1)).isoformat(),'valid_until':(dt+timedelta(days=1)).isoformat(),'freshness_kind':'time-window','review_note':'Read the actual fictional CSV fixture: two rows, website visits, exact dates shown; no real business outcome.','source_sha256':hashlib.sha256(local.read_bytes()).hexdigest()}
        jwrite(evidence,r);cli(self.root,'review-source','--id','source-01','--evidence',str(evidence),'--by','Example Data Owner');return local,evidence
    def test_freshness_can_turn_current_with_actual_local_receipt(self):
        cli(self.root,'check','--require-current',ok=False);self.review_source();r=json.loads(cli(self.root,'check','--accepted','--require-current').stdout);self.assertEqual(r['source_findings'],[])
    def test_source_changes_and_changed_receipt_reopen_check(self):
        local,evidence=self.review_source();local.write_text(local.read_text()+'2026-01-03,website,9\n');cli(self.root,'check','--require-current',ok=False)
    def test_changed_owner_readback_reopens_check(self):
        local,evidence=self.review_source();r=read(evidence);r['review_note']='Changed after recording';jwrite(evidence,r)
        cli(self.root,'check','--require-current',ok=False)
    def test_decision_change_reopens_check_without_arbitrary_expiry(self):
        import hashlib
        local,evidence=self.review_source();decision=self.root/'private/decision.md';decision.write_text('Fictional decision: use this fixture only for its test scope.')
        r=read(evidence);r.update(freshness_kind='decision-controlled',valid_until=None,decision_source=str(decision),decision_sha256=hashlib.sha256(decision.read_bytes()).hexdigest());jwrite(evidence,r)
        cli(self.root,'review-source','--id','source-01','--evidence',str(evidence),'--by','Example Data Owner');cli(self.root,'check','--require-current')
        decision.write_text('Fictional revised decision: previous use withdrawn.');cli(self.root,'check','--require-current',ok=False)
    def test_expired_owner_window_refused(self):
        local,evidence=self.review_source();r=read(evidence);r['valid_until']='2020-01-01T00:00:00+00:00';jwrite(evidence,r)
        cli(self.root,'review-source','--id','source-01','--evidence',str(evidence),'--by','Example Data Owner',ok=False)
    def test_update_record_is_pending_and_false_live_refused(self):
        surfaces=self.root/'private/surfaces.json';jwrite(surfaces,[{'name':'Website offer page','owner':'Example Website Owner'}])
        source=self.root/'private/release.md';source.write_text('Fictional service change for local workflow test. Not a real release.')
        cli(self.root,'record-update','--id','service-change','--title','Fictional service change','--source',str(source),'--fact-owner','Example Offer Owner','--surfaces',str(surfaces))
        cli(self.root,'check','--require-online',ok=False)
        p=self.root/'records/updates/service-change/record.json';r=read(p);r['surfaces'][0]['state']='verified-live';jwrite(p,r);cli(self.root,'check',ok=False)
    def test_missing_update_inventory_cannot_pass_online(self):cli(self.root,'check','--require-online',ok=False)
    def test_bounded_study_pack_keeps_metric_window_and_source(self):
        local,evidence=self.review_source();manifest=self.root/'private/study-input.json'
        jwrite(manifest,{'question':'Which website evidence is available for this fictional window?','window':{'start':'2026-01-01','end':'2026-01-02','timezone':'UTC'},'sources':[{'channel':'website','metric':'visits','definition':'Count of recorded visits; not unique prospects, qualified leads or revenue.','unit':'visits','window_start':'2026-01-01','window_end':'2026-01-02','source_file':str(local),'locator':'rows 2-3, visits column','owner':'Example Data Owner','limits':'Two-row fictional fixture. No causal business conclusion.'}]})
        cli(self.root,'study-pack','--id','first-study','--manifest',str(manifest));p=self.root/'outputs/studies/first-study/manifest.json';r=read(p);self.assertEqual(r['sources'][0]['unit'],'visits');self.assertTrue(Path(r['sources'][0]['source_file']).samefile(local));self.assertTrue((p.parent/'STUDY.md').is_file())

if __name__=='__main__':unittest.main(verbosity=2)
