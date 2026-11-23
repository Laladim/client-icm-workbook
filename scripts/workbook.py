#!/usr/bin/env python3
"""Install and check private client ICM workspaces. No network or publishing actions."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
from datetime import datetime, timezone
from uuid import uuid4
from urllib.parse import urlsplit, parse_qs

from context_pages import (AREA_JOBS, PAGE_JOBS, ROUTES, SOURCE_MARK, area_page,
                           brand_status, client_map, routes_for, worker_brief)

ROOT = Path(__file__).resolve().parents[1]
AREAS = tuple(AREA_JOBS)
BASIS = ('supplied-fact','evidence','interpretation','human-decision','unknown','not-applicable')
ANSWERS = Path('onboarding/01_scope/output/answers.json')
BRIEF = Path('onboarding/03_brief/output/client-brief.md')
BRIEF_STATE = Path('onboarding/03_brief/output/brief-state.json')
BRIEF_APPROVAL = Path('onboarding/03_brief/output/brief-approval.json')
MANIFEST = Path('onboarding/04_workspace/output/workspace-manifest.json')
ACCEPTANCE = Path('onboarding/05_handoff/output/workspace-acceptance.json')
class Problem(ValueError):
    pass

def now():return datetime.now(timezone.utc).isoformat(timespec='seconds')
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def canonical(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def require(ok,message):
    if not ok:raise Problem(message)
def safe(value):
    text=json.dumps(value,ensure_ascii=False)
    if re.search(r'(?i)(?:password|api[_ -]?key|access[_ -]?token|client[_ -]?secret)\s*[:=]\s*[\"\x27]?(?!redacted\b|none\b|not\b)[^\s\"\x27,}]{6,}',text):raise Problem('Possible credential value. Use a secure invitation/store and record only its non-secret reference.')
    if re.search(r'\bgh[pousr]_[A-Za-z0-9]{20,}|\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}|-----BEGIN .*PRIVATE KEY-----',text):raise Problem('Possible secret detected; do not store it in the workbook.')
    for url in re.findall(r'https?://[^\s\"<>]+',text):
        u=urlsplit(url)
        require(not u.username and not u.password,'Do not store credentials in URLs.')
        require(not any(k.lower() in {'token','access_token','api_key','secret','password','signature'} for k in parse_qs(u.query)),'Remove access-bearing query parameters from source references.')
def write(path,text,history=True):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    if p.exists() and p.read_text(encoding='utf-8')==text:return
    if p.exists() and history:
        h=p.parent/'history';h.mkdir(exist_ok=True,mode=0o700)
        shutil.copyfile(p,h/(p.name+'.'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'.'+uuid4().hex[:8]))
    temp=p.with_name('.'+p.name+'.'+uuid4().hex+'.tmp');temp.write_text(text,encoding='utf-8');temp.chmod(0o600);os.replace(temp,p)
def jwrite(path,value,history=True):write(path,json.dumps(value,indent=2,ensure_ascii=False)+'\n',history)
def path_for(root,raw):
    p=Path(raw).expanduser()
    return p if p.is_absolute() else root/p

def bank(root):return load(root/'_shared/questions.json')
def flat(root):return {q['id']:{**q,'group':g['id'],'channel':g['channel'],'area':g['area']} for g in bank(root)['groups'] for q in g['questions']}
def answers(root):return load(root/ANSWERS) if (root/ANSWERS).is_file() else {'schema_version':1,'answers':{}}
def selected(root,a=None):
    record=(a or answers(root))['answers'].get('channels.active')
    return record['value'] if record and isinstance(record['value'],list) else []
def applicable(root,include_optional=True):
    channels=selected(root)
    return [q for q in flat(root).values() if (not q['channel'] or q['channel'] in channels) and (include_optional or q['required'])]
def missing(root,include_optional=False):
    a=answers(root)['answers']
    return [q for q in applicable(root,include_optional) if q['id'] not in a]
def identity(root):
    p=root/'client.json';require(p.is_file(),'This is not an installed client. Use init from the public template, or choose --workspace.')
    c=load(p);require(c.get('schema_version')==1 and c.get('mode')=='local-only','Client identity or local-only boundary is invalid.');return c

def init_client(args):
    require((ROOT/'_templates/client').is_dir(),'Install a new client from the public template repository, not another client workspace.')
    require(re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',args.id) is not None,'Use a lowercase kebab-case client ID.')
    require(args.id.lower() not in {'con','prn','aux','nul',*[f'com{i}' for i in range(1,10)],*[f'lpt{i}' for i in range(1,10)]},'Choose a portable client ID, not a reserved system name.')
    require(args.name.strip() and '\n' not in args.name,'Supply the actual client name on one line.');safe(args.name)
    target=Path(args.destination).expanduser().resolve()
    require(not target.exists() and not target.is_symlink(),'Destination already exists. Nothing was changed; choose a new empty private location.')
    require(not target.is_relative_to(ROOT) and not ROOT.is_relative_to(target),'Keep the private client outside the public template repository.')
    for parent in target.parents:
        require(not (parent/'client.json').exists(),'Do not nest one client inside another client workspace.')
        require(not (parent/'.git').exists(),'Choose a client destination outside an existing Git repository; no repository visibility is assumed.')
        require(not (parent/'AGENTS.md').exists() and not (parent/'CLAUDE.md').exists(),'This parent already has an operational owner. Bind that workflow or choose a separate approved client location.')
    target.mkdir(parents=True,mode=0o700)
    shutil.copytree(ROOT/'_templates/client',target,dirs_exist_ok=True)
    for file in ['SETUP.md','FILE-BUILD-MAP.csv','NEW-CLIENT-DISCOVERY.md']:
        shutil.copyfile(ROOT/file,target/file)
    shutil.copytree(ROOT/'docs',target/'docs')
    shutil.copytree(ROOT/'deploy',target/'deploy')
    (target/'scripts').mkdir(exist_ok=True)
    for filename in ('workbook.py', 'context_pages.py'):
        shutil.copyfile(ROOT/'scripts'/filename, target/'scripts'/filename)
    shutil.copyfile(ROOT/'_shared/questions.json',target/'_shared/questions.json')
    version=(ROOT/'VERSION').read_text().strip()
    jwrite(target/'client.json',{'schema_version':1,'id':args.id,'name':args.name.strip(),'mode':'local-only','template_version':version,'created_at':now()},False)
    jwrite(target/'_shared/template-source.json',{'version':version,'question_bank_sha256':sha(ROOT/'_shared/questions.json'),'scope':'Portable public template only; no other client data or operating authority copied.'},False)
    jwrite(target/ANSWERS,{'schema_version':1,'answers':{}},False)
    for p in target.rglob('*'):
        if p.is_file():p.chmod(0o600)
        elif p.is_dir():p.chmod(0o700)
    print('Installed private client workspace:',target)
    print('Next: open this private folder and run python3 scripts/workbook.py interview')
    return 0

def record_answer(root,args):
    identity(root);qs=flat(root);require(args.question in qs,'Unknown question ID. Use interview or the canonical discovery workbook.')
    q=qs[args.question];safe([args.value,args.source,args.by,args.reason])
    value=args.value
    if q['type'] in {'list','channels'}:
        try:value=json.loads(value)
        except json.JSONDecodeError:raise Problem('The agent must encode this answer as a JSON list; the person does not need to write JSON.')
        require(isinstance(value,list) and all(isinstance(v,str) and v.strip() for v in value),'Use a list of nonempty source references or channel IDs.')
        if q['type']=='channels':require(len(value)==len(set(value)) and set(value)<=set(bank(root)['channels']),'Use unique channel IDs from the question bank.')
    else:require(value.strip(),'An answer cannot be blank.')
    if args.basis in {'unknown','not-applicable'}:require(args.reason and args.reason.strip(),'Record why this is unknown/not applicable and the next source or owner to check.')
    if args.basis=='evidence':require(args.source and args.source.strip(),'Evidence needs an exact source reference; a plausible fact is not evidence.')
    if q['decision']:require(args.basis in {'human-decision','unknown','not-applicable'},'This is a human decision; record the actual decision or an explicit unresolved state.')
    a=answers(root);a['answers'][args.question]={'value':value,'basis':args.basis,'source':args.source or None,'supplied_by':args.by,'reason':args.reason or None,'recorded_at':now()};jwrite(root/ANSWERS,a)
    print('Recorded',args.question,'as',args.basis)

def show_interview(root,args):
    identity(root);pending=missing(root,args.include_optional)
    if not pending:print('Core discovery is recorded. Generate the reviewable brief; optional detail remains available with --include-optional.');return
    group=pending[0]['group'];qs=[q for q in pending if q['group']==group][:3]
    print('Read supplied context first. Ask only these missing questions, at most three:')
    for q in qs:
        print(q['id']+': '+q['prompt']);print('Why:',q['why'])
        if q['type']=='channels':print('Channel IDs:',', '.join(bank(root)['channels']))

def as_text(value):
    if isinstance(value,list):return '\n'.join('- '+str(v) for v in value) or 'None selected.'
    return str(value)
def section(q,record):
    if not record:return '## '+q['id']+'\n\nNot supplied. Read the owning source or ask for missing context before using this field.\n'
    lines=['## '+q['id'],'',q['prompt'],'','Basis: '+record['basis']+'. Supplied by: '+record['supplied_by']+'.','',as_text(record['value'])]
    if record.get('source'):lines+=['','Source reference: '+record['source']]
    if record.get('reason'):lines+=['','Reason / next source: '+record['reason']]
    return '\n'.join(lines)+'\n'
def core_requirements(root):
    pending=missing(root)
    require(not pending,'Missing core context: '+', '.join(q['id'] for q in pending))
    approver=answers(root)['answers'].get('engagement.approver',{})
    require(approver.get('basis')=='human-decision' and isinstance(approver.get('value'),str) and approver['value'].strip(),'Name the real onboarding approver; an unknown approver cannot accept a brief.')

def create_brief(root,args):
    c=identity(root);core_requirements(root);a=answers(root);parts=['# '+c['name']+': client brief','','Client ID: '+c['id']+'. Scope: local-only onboarding; no live-action authority is activated.','','Unknowns and interpretations remain labeled. Approval of this brief accepts its exact context and gaps, not their factual correctness or production permission.','']
    for q in applicable(root):
        if q['id'] in a['answers']:parts.append(section(q,a['answers'][q['id']]))
    jwrite(root/'onboarding/02_evidence/output/source-register.json',initial_sources(root))
    write(root/BRIEF,'\n'.join(parts))
    jwrite(root/BRIEF_STATE,{'schema_version':1,'client_sha256':sha(root/'client.json'),'answers_sha256':sha(root/ANSWERS),'question_bank_sha256':sha(root/'_shared/questions.json'),'brief_sha256':sha(root/BRIEF),'created_at':now()})
    print('Brief:',root/BRIEF);print('SHA-256:',sha(root/BRIEF));print('Stop for the named human to approve or revise this exact brief.')

def validate_brief(root,approved=False):
    core_requirements(root);require((root/BRIEF).is_file() and (root/BRIEF_STATE).is_file(),'Generate the exact client brief first.')
    state=load(root/BRIEF_STATE)
    require(state.get('client_sha256')==sha(root/'client.json'),'Client identity changed since the brief; do not reuse another client approval.')
    require(state['answers_sha256']==sha(root/ANSWERS),'Answers changed after brief creation. Regenerate and obtain approval of the new exact brief.')
    require(state['question_bank_sha256']==sha(root/'_shared/questions.json'),'Question bank changed after the brief. Review before proceeding.')
    require(state['brief_sha256']==sha(root/BRIEF),'Brief bytes changed. Regenerate its evidence and obtain the human approval again.')
    if approved:
        require((root/BRIEF_APPROVAL).is_file(),'The exact client brief needs the named human approval before build.')
        r=load(root/BRIEF_APPROVAL);require(r.get('brief_sha256')==sha(root/BRIEF) and r.get('answers_sha256')==sha(root/ANSWERS),'Brief approval is stale.')
        require(r.get('approved_by')==answers(root)['answers']['engagement.approver']['value'] and r.get('statement'),'Approval must name the recorded human and preserve their genuine statement.')
    return state

def approve_brief(root,args):
    identity(root);validate_brief(root);require(args.sha256==sha(root/BRIEF),'Displayed digest does not match the exact current brief.')
    require(args.by==answers(root)['answers']['engagement.approver']['value'],'Use the approver named in the client brief.')
    require(args.statement.strip() and args.statement.lower().strip() not in {'pending','silence','auto-approved','unknown'},'Record the actual explicit human approval statement.')
    safe(args.statement);jwrite(root/BRIEF_APPROVAL,{'schema_version':1,'brief_sha256':sha(root/BRIEF),'answers_sha256':sha(root/ANSWERS),'approved_by':args.by,'statement':args.statement,'recorded_at':now(),'brand_decisions':brand_events(root)})
    print('Recorded exact-brief human approval. Next: build the local workspace.')

def workspace_digest(root,manifest):
    refs={rel:sha(root/rel) for rel in manifest['files'] if (root/rel).is_file()}
    require(len(refs)==len(manifest['files']),'A generated workspace file is missing.')
    return canonical({'brief_approval_sha256':sha(root/BRIEF_APPROVAL),'files':refs})
def brand_events(root):
    """Extend the existing receipt only when an explicit brand decision changes."""
    previous = load(root / BRIEF_APPROVAL) if (root / BRIEF_APPROVAL).exists() else {}
    events = list(previous.get('brand_decisions', []))
    latest = {event['question']: event for event in events}
    current = answers(root)['answers']
    for question in applicable(root):
        if question['area'] != 'brand':
            continue
        key = question['id']
        record = current.get(key, {})
        prior = latest.get(key)
        decided = record.get('basis') == 'human-decision'
        if not decided and (not prior or prior['wording'] is None):
            continue
        wording = record['value'] if decided else None
        participant = record.get('supplied_by')
        source = record.get('source')
        if prior and (wording, participant, source) == (prior['wording'], prior['by'], prior['source']):
            continue
        events.append({'question': key, 'wording': wording, 'by': participant, 'source': source,
                       'captured_at': record.get('recorded_at'), 'approved_at': now(),
                       'brief_sha256': sha(root / BRIEF), 'replaces': prior['wording'] if prior else None,
                       'basis': record.get('basis', 'unanswered')})
    return events


def decision_log(approval):
    lines = ['# Brand decisions', '<!-- Generated from onboarding/03_brief/output/brief-approval.json. -->', '',
             'Newest changes first. The [approval record](../onboarding/03_brief/output/brief-approval.json) retains the dated entries.', '']
    for event in reversed(approval.get('brand_decisions', [])):
        value = event['wording']
        text = value if value is not None else 'Previous decision withdrawn. Current basis: ' + event['basis'] + '.'
        lines += [f"## {event['approved_at']} | {event['question']}", '', text, '',
                  'Recorded by ' + str(event.get('by') or 'Unspecified') + '.',
                  'Source: ' + str(event['source'] or ('Interview answer ' + event['question'])) + '.',
                  'Approved brief: ' + event['brief_sha256'] + '.', '']
        if event.get('replaces') is not None:
            lines += ['Replaces the prior wording:', '', event['replaces'], '']
    if not approval.get('brand_decisions'):
        lines.append('No explicit brand decision has been recorded in an approved brief.')
    return '\n'.join(lines) + '\n'


def reference_page(name, destination, questions, records, channels):
    title = Path(destination).stem.replace('-', ' ')
    parts = [f'# {name} | {title}', SOURCE_MARK, '']
    if destination.startswith('brand/'):
        parts.extend([brand_status(questions, records), ''])
    if destination.startswith('channels/') and Path(destination).stem in channels:
        parts.append(worker_brief(Path(destination).stem, records))
    elif destination in PAGE_JOBS:
        parts.extend([PAGE_JOBS[destination], ''])
    missing = []
    for question in questions:
        key = question['id']
        if key in records:
            parts.append(section(question, records[key]))
        else:
            missing.append(key)
    if missing:
        parts.append('Still to collect: ' + ', '.join(missing) + '.\n')
    return '\n'.join(parts)


def build(root, args):
    client = identity(root)
    validate_brief(root, approved=True)
    records = answers(root)['answers']
    channels = selected(root)
    by_destination = {}
    for question in applicable(root):
        by_destination.setdefault(question['destination'], []).append(question)

    old = load(root / MANIFEST)['files'] if (root / MANIFEST).exists() else {}
    for rel, expected in old.items():
        require((root / rel).is_file() and sha(root / rel) == expected,
                'A generated context file was edited: ' + rel + '. Preserve it and reconcile the change before regenerating.')

    pages = {dest: reference_page(client['name'], dest, group, records, channels)
             for dest, group in by_destination.items()}
    pages.update({area + '/CONTEXT.md': area_page(area, by_destination) for area in AREAS})
    pages['CONTEXT.md'] = client_map(client['name'], channels)
    pages['brand/decisions.md'] = decision_log(load(root / BRIEF_APPROVAL))
    # The previous approved worker may still be bookmarked. Keep its old bytes
    # in history and replace the active instructions with the current scope.
    for channel in bank(root)['channels']:
        rel = 'channels/' + channel + '.md'
        if rel in old and rel not in pages:
            pages[rel] = f'# {channel} outside current scope\n{SOURCE_MARK}\n\nRead [channel scope](strategy.md) before starting work.\n'
    for rel, body in pages.items():
        write(root / rel, body)

    inventory = root / 'monitoring/sources.json'
    if not inventory.exists():
        jwrite(inventory, load(root / 'onboarding/02_evidence/output/source-register.json'))
    bound = ['client.json', 'AGENTS.md', 'CLAUDE.md', '_shared/context-contract.md']
    files = {rel: sha(root / rel) for rel in [*pages, *bound]}
    manifest = {'schema_version': 1, 'layout_version': 2, 'files': files,
                'brief_approval_sha256': sha(root / BRIEF_APPROVAL), 'built_at': now()}
    manifest['workspace_sha256'] = workspace_digest(root, manifest)
    jwrite(root / MANIFEST, manifest)
    print('Generated seven-area local workspace. SHA-256:', manifest['workspace_sha256'])
    print('Run check, walk the routes, then stop for exact workspace acceptance.')


def slug(value):
    require(re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',value) is not None,'Use a lowercase kebab-case record ID.')
    return value

def input_file(root,raw):
    path=path_for(root,raw).resolve()
    require(path.is_file(),'Source/evidence file is unavailable: '+str(path))
    lowered=path.name.lower()
    require(not (lowered=='.env' or lowered.startswith('.env.') or path.suffix.lower() in {'.pem','.key','.p12','.pfx','.kdbx'} or any(w in lowered for w in ('credential','oauth-token','private-key','cookies'))),'Do not read credential-like files as marketing evidence. Use a non-secret account/reference note.')
    return path

def initial_sources(root):
    a=answers(root)['answers'];record=a.get('sources.locations',{});locators=record.get('value',[])
    owner=a.get('sources.owners',{}).get('value','Unassigned; confirm the actual source owner.')
    rows=[]
    for i,locator in enumerate(locators if isinstance(locators,list) else []):
        safe(locator);is_url=bool(re.match(r'https?://',locator));p=path_for(root,locator)
        observed=None
        if not is_url and p.is_file():observed=sha(input_file(root,locator))
        rows.append({'id':f'source-{i+1:02d}','locator':locator,'owner':owner,'cadence':'Confirm owner-specific refresh rule from the interview.','sensitivity':'unreviewed-private','public_use':'Not established; obtain actual source/consent review.','status':'unreviewed','observed_sha256':observed,'metadata_observed_at':now(),'review_receipt':None})
    return {'schema_version':1,'scope':'Source pointers supplied during discovery; metadata availability is separate from current-data/claim/permission review.','sources':rows}

def register_source(root,args):
    check(root);slug(args.id);safe([args.locator,args.owner,args.cadence,args.sensitivity,args.public_use])
    is_url=bool(re.match(r'https?://',args.locator));observed=None
    if not is_url:observed=sha(input_file(root,args.locator))
    row={'id':args.id,'locator':args.locator,'owner':args.owner,'cadence':args.cadence,'sensitivity':args.sensitivity,'public_use':args.public_use,'status':'unreviewed','observed_sha256':observed,'metadata_observed_at':now(),'review_receipt':None}
    path=root/'monitoring/sources.json';data=load(path);data['sources']=[r for r in data['sources'] if r['id']!=args.id]+[row];jwrite(path,data)
    print('Registered source pointer:',args.id,'Current use remains unreviewed.')

def review_source(root,args):
    check(root);slug(args.id);path=root/'monitoring/sources.json';data=load(path);rows=[r for r in data['sources'] if r['id']==args.id]
    require(len(rows)==1,'Register this exact source ID first.');source=rows[0];ep=input_file(root,args.evidence);e=load(ep);safe(e)
    require(e.get('source_id')==source['id'] and e.get('locator')==source['locator'],'Owner readback is for a different source or locator.')
    require(e.get('result')=='pass' and e.get('owner')==args.by and args.by==source['owner'],'A passing readback must name the registered source owner; do not invent owner review.')
    require(e.get('review_note') and valid_timestamp(e.get('checked_at')),'Readback needs observed date and substantive relevance/limits note.')
    is_url=bool(re.match(r'https?://',source['locator']))
    if not is_url:require(e.get('source_sha256')==sha(input_file(root,source['locator'])),'Source bytes differ from the owner readback.')
    else:require(e.get('status_code')==200 and re.fullmatch('[a-f0-9]{64}',e.get('content_sha256','')) is not None,'URL source needs actual response/content evidence, not only a URL.')
    if e.get('freshness_kind')=='decision-controlled':
        require(e.get('decision_source') and e.get('decision_sha256')==sha(input_file(root,e['decision_source'])),'Decision-controlled evidence needs the exact actual decision source and hash.')
    else:require(e.get('freshness_kind')=='time-window' and valid_timestamp(e.get('valid_until'),future=True),'Time-sensitive evidence needs an owner-defined unexpired validity window.')
    receipt={**e,'evidence_path':str(ep),'evidence_sha256':sha(ep)}
    rel=Path('monitoring/receipts')/source['id']/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid4().hex[:8]+'.json');jwrite(root/rel,receipt)
    source.update(status='reviewed',review_receipt=rel.as_posix());jwrite(path,data)
    print('Recorded source review:',source['id'],'Evidence remains subject to source changes and its validity rule.')

def record_update(root,args):
    check(root,True);slug(args.id);source=input_file(root,args.source);safe([args.fact_owner,args.title]);surfaces=load(input_file(root,args.surfaces));require(isinstance(surfaces,list) and surfaces,'Select actual surfaces and receiving owners; do not assume every channel is needed.')
    for surface in surfaces:
        require(isinstance(surface,dict) and surface.get('name') and surface.get('owner'),'Every selected surface needs its name and actual receiving owner.')
        require(surface.get('state','needs-review')=='needs-review','A new update starts needs-review, not published.')
        surface.update(state='needs-review',receipt=None)
    path=root/'records/updates'/args.id/'record.json';require(not path.exists(),'This update already has a record. Continue it; do not overwrite its source identity.')
    jwrite(path,{'schema_version':1,'id':args.id,'title':args.title,'source':str(source),'source_sha256':sha(source),'fact_owner':args.fact_owner,'recorded_at':now(),'surfaces':surfaces},False)
    print('Recorded update; selected surfaces need owner work and actual live evidence:',path)

def study_pack(root,args):
    check(root,True);slug(args.id);spec=load(input_file(root,args.manifest));safe(spec)
    require(spec.get('question') and isinstance(spec.get('window'),dict) and all(spec['window'].get(k) for k in ['start','end','timezone']),'Name one study question and exact date window/timezone.')
    require(spec.get('sources') and isinstance(spec['sources'],list),'Select bounded actual source outputs for this study.')
    output=root/'outputs/studies'/args.id;require(not output.exists(),'Study record exists. Use a new named revision; preserve prior evidence.')
    rows=[]
    for r in spec['sources']:
        require(all(r.get(k) for k in ['channel','metric','definition','unit','window_start','window_end','source_file','locator','owner','limits']),'Each source needs channel, metric definition/unit/window, exact file/range, owner and interpretation limits.')
        source=input_file(root,r['source_file']);rows.append({**r,'source_file':str(source),'source_sha256':sha(source)})
    output.mkdir(parents=True,mode=0o700)
    jwrite(output/'manifest.json',{'schema_version':1,'question':spec['question'],'window':spec['window'],'sources':rows,'captured_at':now(),'scope':'Bounded source-output index; source data stays authoritative. No metrics or causal conclusions were invented or automatically combined.'},False)
    lines=['# '+spec['question'],'','Window: '+json.dumps(spec['window'])+'.','', 'Each item below defines its own unit, denominator/aggregation and evidence window. Match those before comparing; do not add percentages or infer revenue causation. This pack indexes actual owner outputs rather than copying entire client data stores.','']
    for r in rows:lines+=['## '+r['channel']+': '+r['metric'],'',r['definition'],'','Unit: '+r['unit']+'. Window: '+r['window_start']+' to '+r['window_end']+'.','', 'Source: '+r['source_file']+'; locator: '+r['locator']+'. Owner: '+r['owner']+'.','', 'Limits: '+r['limits'],'']
    write(output/'STUDY.md','\n'.join(lines),False);print('Study pack:',output/'STUDY.md')

def valid_timestamp(value,future=False):
    try:
        dt=datetime.fromisoformat(value.replace('Z','+00:00'))
        return dt.tzinfo is not None and ((dt>datetime.now(timezone.utc)) if future else (dt<=datetime.now(timezone.utc)))
    except (ValueError,TypeError,AttributeError):return False

def source_health(root):
    p=root/'monitoring/sources.json';findings=[]
    if not p.is_file():return ['Source inventory has not been generated.']
    rows=load(p).get('sources',[])
    if not rows:return ['No source inventory is established; current data cannot be claimed.']
    for s in rows:
        if s.get('status')!='reviewed':findings.append(s.get('id','source')+': not reviewed for current use');continue
        ref=s.get('review_receipt');p=path_for(root,ref) if ref else None
        if not p or not p.is_file():findings.append(s['id']+': missing owner readback receipt');continue
        r=load(p)
        evidence=path_for(root,r.get('evidence_path',''))
        if not evidence.is_file() or r.get('evidence_sha256')!=sha(evidence):findings.append(s['id']+': owner readback evidence missing or changed');continue
        if r.get('result')!='pass' or r.get('source_id')!=s['id'] or r.get('locator')!=s['locator'] or r.get('owner')!=s.get('owner') or not r.get('review_note') or not valid_timestamp(r.get('checked_at')):findings.append(s['id']+': incomplete owner/source/date/relevance evidence');continue
        loc=path_for(root,s['locator'])
        if not re.match(r'https?://',s['locator']) and (not loc.is_file() or r.get('source_sha256')!=sha(loc)):findings.append(s['id']+': source bytes changed or unavailable')
        if r.get('freshness_kind')=='decision-controlled':
            decision=path_for(root,r.get('decision_source',''))
            if not decision.is_file() or r.get('decision_sha256')!=sha(decision):findings.append(s['id']+': decision source missing or changed')
        elif r.get('freshness_kind')!='time-window' or not valid_timestamp(r.get('valid_until'),future=True):findings.append(s['id']+': validity window missing or expired')
    return findings

def update_health(root):
    errors=[];gaps=[];records=list((root/'records/updates').glob('*/record.json'))
    for p in records:
        r=load(p);safe(r);uid=r.get('id');source=path_for(root,r.get('source',''))
        if not uid or not source.is_file() or not r.get('fact_owner'):errors.append(str(p)+': missing update identity, source or fact owner');continue
        if r.get('source_sha256')!=sha(source):errors.append(uid+': update source changed; obtain a new source-owner assessment');continue
        for s in r.get('surfaces',[]):
            label=uid+'/'+s.get('name','surface');state=s.get('state')
            if not s.get('owner'):errors.append(label+': no receiving owner')
            if state in {'needs-review','in-progress','blocked'}:gaps.append(label+': '+state)
            elif state=='not-required':
                if not s.get('reason') or not s.get('decision_source') or not path_for(root,s['decision_source']).is_file():errors.append(label+': not-required needs a reason and decision source')
            elif state=='verified-live':
                ref=s.get('receipt');rp=path_for(root,ref) if ref else None
                if not rp or not rp.is_file():errors.append(label+': live claim has no owner receipt');continue
                v=load(rp);url=urlsplit(v.get('public_url',''))
                if v.get('update_id')!=uid or v.get('surface')!=s.get('name') or v.get('owner')!=s.get('owner') or v.get('source_sha256')!=sha(source) or v.get('status_code')!=200 or v.get('expected_content_present') is not True or not re.fullmatch('[a-f0-9]{64}',v.get('content_sha256','')) or not valid_timestamp(v.get('checked_at')) or not valid_timestamp(v.get('valid_until'),future=True) or url.scheme!='https' or not url.netloc:errors.append(label+': invalid, changed or expired live evidence')
            else:errors.append(label+': unknown surface state')
        if not r.get('surfaces'):gaps.append(uid+': no selected-surface assessment')
    return errors,gaps,len(records)

def check(root,accepted=False,brief_only=False,require_current=False,require_online=False):
    identity(root);validate_brief(root,True)
    if brief_only:return {'scope':'approved brief only','status':'pass'}
    require((root/MANIFEST).is_file(),'Build the seven-area workspace after brief approval.')
    m=load(root/MANIFEST);require(m.get('brief_approval_sha256')==sha(root/BRIEF_APPROVAL),'Brief approval changed since workspace build.')
    require(workspace_digest(root,m)==m.get('workspace_sha256'),'Generated context changed after build; review and rebind it before acceptance.')
    for area in AREAS:require((root/area/'CONTEXT.md').is_file(),'Missing area contract: '+area)
    current_routes = routes_for(selected(root))
    for topic, (_, entry) in current_routes.items():
        require((root / entry).is_file(), 'Missing concern route: ' + topic)
    require('@AGENTS.md' in (root/'CLAUDE.md').read_text(),'Claude entry must import the shared AGENTS authority.')
    for channel in selected(root):
        worker=root/'channels'/f'{channel}.md'
        content = worker.read_text(encoding='utf-8') if worker.is_file() else ''
        if m.get('layout_version', 1) >= 2:
            require(worker_brief(channel, answers(root)['answers']) in content, 'Worker audience/reviewer differs from the approved answers: ' + channel)
        else:
            require('../brand/strategy/positioning.md' in content and 'declared channel reviewer' in content, 'Missing legacy worker context: ' + channel)
    if accepted:
        require((root/ACCEPTANCE).is_file(),'Workspace needs the named human acceptance of the displayed digest.')
        r=load(root/ACCEPTANCE);require(r.get('workspace_sha256')==m['workspace_sha256'] and r.get('brief_approval_sha256')==sha(root/BRIEF_APPROVAL) and r.get('accepted_by')==answers(root)['answers']['engagement.approver']['value'] and r.get('statement'),'Workspace acceptance is stale or incomplete.')
    for p in [root/'client.json',root/ANSWERS,root/BRIEF]:safe(p.read_text())
    errors,gaps,count=update_health(root);require(not errors,'; '.join(errors))
    freshness=source_health(root)
    if require_current:require(not freshness,'; '.join(freshness))
    if require_online:require(count>0 and not gaps,'No complete assessed online update inventory: '+'; '.join(gaps))
    return {'scope':'local client structure, shared entries, exact context/approval integrity and recorded evidence rules','status':'pass','accepted':accepted,'concern_routes':len(ROUTES),'areas':len(AREAS),'source_findings':freshness,'update_records':count,'online_coverage_gaps':gaps,'limits':'No current external data, audience validity, human identity, strategy success, installed automation or production authority is established by this check.'}

def accept_workspace(root,args):
    check(root);m=load(root/MANIFEST)
    require(args.sha256==m['workspace_sha256'],'Displayed digest differs from the generated workspace.')
    require(args.by==answers(root)['answers']['engagement.approver']['value'],'Use the recorded human onboarding approver.')
    require(args.statement.strip() and args.statement.lower().strip() not in {'pending','silence','unknown','auto-approved'},'Record the actual explicit human acceptance statement.')
    jwrite(root/ACCEPTANCE,{'schema_version':1,'workspace_sha256':m['workspace_sha256'],'brief_approval_sha256':sha(root/BRIEF_APPROVAL),'accepted_by':args.by,'statement':args.statement,'recorded_at':now()})
    print('Recorded exact workspace acceptance. Local-only remains in force. Run check --accepted.')

def status(root,args):
    c=identity(root);result={'client':c['name'],'mode':c['mode'],'missing_core_questions':[q['id'] for q in missing(root)]}
    result['next']='01_scope: capture core context' if result['missing_core_questions'] else '02_evidence / 03_brief: inspect source gaps and generate brief'
    try:
        validate_brief(root,False);result['brief_sha256']=sha(root/BRIEF);result['next']='03_brief: obtain human approval of exact brief'
        validate_brief(root,True);result['next']='04_workspace: generate and walk the seven-area map'
        if (root/MANIFEST).exists():
            check(root);m=load(root/MANIFEST);result['workspace_sha256']=m['workspace_sha256'];result['next']='05_handoff: obtain exact human workspace acceptance'
            if (root/ACCEPTANCE).exists():check(root,True);result['next']='Accepted local setup; enter the selected area/owner. Source freshness and live integration remain separate.'
    except (Problem,OSError,KeyError,json.JSONDecodeError) as e:result['gate_finding']=str(e)
    print(json.dumps(result,indent=2))

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',type=Path,help='installed private client root; defaults to this script\'s workspace')
    subs=p.add_subparsers(dest='command',required=True)
    q=subs.add_parser('init',help='install a new isolated private client outside the public template');q.add_argument('--id',required=True);q.add_argument('--name',required=True);q.add_argument('--destination',required=True)
    q=subs.add_parser('interview',help='show up to three unanswered questions');q.add_argument('--include-optional',action='store_true')
    q=subs.add_parser('answer',help='record a labeled interview answer');q.add_argument('--question',required=True);q.add_argument('--value',required=True);q.add_argument('--basis',choices=BASIS,required=True);q.add_argument('--by',required=True);q.add_argument('--source');q.add_argument('--reason')
    subs.add_parser('brief',help='render the exact reviewable brief from current answers')
    for name in ['approve-brief','accept-workspace']:
        q=subs.add_parser(name,help='record a genuine explicit human response for the displayed digest');q.add_argument('--sha256',required=True);q.add_argument('--by',required=True);q.add_argument('--statement',required=True)
    subs.add_parser('build',help='generate seven areas only after exact brief approval')
    q=subs.add_parser('check',help='check local setup; freshness and live coverage are separate opt-in requirements');q.add_argument('--brief-only',action='store_true');q.add_argument('--accepted',action='store_true');q.add_argument('--require-current',action='store_true');q.add_argument('--require-online',action='store_true')
    subs.add_parser('status',help='derive the next onboarding gate from files')
    q=subs.add_parser('route',help='find the actual entry for a client concern');q.add_argument('--topic',choices=sorted(ROUTES),required=True)
    q=subs.add_parser('register-source',help='register an actual source pointer without claiming current use');q.add_argument('--id',required=True);q.add_argument('--locator',required=True);q.add_argument('--owner',required=True);q.add_argument('--cadence',required=True);q.add_argument('--sensitivity',required=True);q.add_argument('--public-use',required=True)
    q=subs.add_parser('review-source',help='record a passing actual owner readback with source hash and validity');q.add_argument('--id',required=True);q.add_argument('--evidence',required=True);q.add_argument('--by',required=True)
    q=subs.add_parser('record-update',help='record one source-backed offer change and selected receiving surfaces');q.add_argument('--id',required=True);q.add_argument('--title',required=True);q.add_argument('--source',required=True);q.add_argument('--fact-owner',required=True);q.add_argument('--surfaces',required=True)
    q=subs.add_parser('study-pack',help='index bounded owner outputs with metric definitions, units and date windows');q.add_argument('--id',required=True);q.add_argument('--manifest',required=True)
    a=p.parse_args(argv);root=(a.workspace or ROOT).expanduser().resolve()
    try:
        if a.command=='init':return init_client(a)
        if a.command=='interview':show_interview(root,a)
        elif a.command=='answer':record_answer(root,a)
        elif a.command=='brief':create_brief(root,a)
        elif a.command=='approve-brief':approve_brief(root,a)
        elif a.command=='build':build(root,a)
        elif a.command=='accept-workspace':accept_workspace(root,a)
        elif a.command=='status':status(root,a)
        elif a.command=='register-source':register_source(root,a)
        elif a.command=='review-source':review_source(root,a)
        elif a.command=='record-update':record_update(root,a)
        elif a.command=='study-pack':study_pack(root,a)
        elif a.command=='check':print(json.dumps(check(root,a.accepted,a.brief_only,a.require_current,a.require_online),indent=2))
        elif a.command=='route':
            check(root,True);area,entry=routes_for(selected(root))[a.topic];print(json.dumps({'topic':a.topic,'area':area,'entry':str(root/entry),'next':'Read this entry and actual owner; check evidence, consent and authority before use.'},indent=2))
        return 0
    except (Problem,OSError,KeyError,TypeError,json.JSONDecodeError) as e:
        print('CLIENT WORKBOOK CHECK FAILED: '+str(e),file=sys.stderr);return 1

if __name__=='__main__':sys.exit(main())
