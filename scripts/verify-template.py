#!/usr/bin/env python3
"""Audit reusable public source and question-to-file consistency; never inspect client instances."""
from pathlib import Path
import ast
import csv
import json
import re
import sys

ROOT=Path(__file__).resolve().parents[1]

def audit():
    errors=[]
    required=['README.md','START-HERE.md','SETUP.md','AGENTS.md','CLAUDE.md','CONTEXT.md','VERSION','FILE-BUILD-MAP.csv','NEW-CLIENT-DISCOVERY.md','docs/FOLDER-GUIDE.md','docs/OWNER-BINDINGS.md','docs/SECURITY-AND-PRIVACY.md','docs/SOURCE-RECEIPTS.md','deploy/HANDOFF.md','_shared/questions.json','scripts/workbook.py','scripts/smoke-test.py','tests/test_workbook.py','LICENSE-CODE','LICENSE-CONTENT']
    for n in required:
        if not (ROOT/n).is_file():errors.append('Missing public source: '+n)
    if errors:return errors
    bank=json.loads((ROOT/'_shared/questions.json').read_text());questions=[q for g in bank['groups'] for q in g['questions']];ids=[q['id'] for q in questions]
    if len(ids)!=len(set(ids)):errors.append('Question IDs must be unique')
    if len(ids)<80:errors.append('The workbook no longer covers the agreed full-service discovery scope')
    maps=list(csv.DictReader((ROOT/'FILE-BUILD-MAP.csv').open(newline='')))
    mapping={r['question_id']:r for r in maps}
    if set(mapping)!=set(ids) or len(maps)!=len(ids):errors.append('Question-to-file map is incomplete or duplicated')
    text=(ROOT/'NEW-CLIENT-DISCOVERY.md').read_text()
    for g in bank['groups']:
        if g['channel'] and g['channel'] not in bank['channels']:errors.append('Unknown channel condition: '+g['id'])
        for q in g['questions']:
            row=mapping.get(q['id'],{})
            if row.get('destination')!=q['destination'] or row.get('required')!=str(q['required']).lower() or row.get('channel_condition')!=(g['channel'] or 'always'):errors.append('Answer mapping drift: '+q['id'])
            if '**'+q['id']+'**' not in text or q['prompt'] not in text or q['destination'] not in text:errors.append('Discovery text drift: '+q['id'])
            if Path(q['destination']).is_absolute() or '..' in Path(q['destination']).parts:errors.append('Unsafe question destination: '+q['id'])
    for name in ['CLAUDE.md','_templates/client/CLAUDE.md']:
        if '@AGENTS.md' not in (ROOT/name).read_text():errors.append('Claude entry lacks shared authority: '+name)
    for stage in ['01_scope','02_evidence','03_brief','04_workspace','05_handoff']:
        p=ROOT/'_templates/client/onboarding'/stage
        if not (p/'CONTEXT.md').is_file() or not (p/'output').is_dir():errors.append('Missing onboarding contract/output: '+stage)
    forbidden=[r'/Users/[A-Za-z0-9_-]+/',r'[A-Za-z]:\\Users\\[A-Za-z0-9_-]+',r'Life'+'-Dashboard',r'cobalt'+r'intelligence\.(?:com|slack\.com)',r'Beyond'+' Banks',r'\bgh[pousr]_[A-Za-z0-9]{20,}',r'\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}',r'-----BEGIN [A-Z ]*PRIVATE KEY-----']
    files=[p for p in ROOT.rglob('*') if p.is_file() and '.git' not in p.relative_to(ROOT).parts and '__pycache__' not in p.parts]
    for p in files:
        rel=p.relative_to(ROOT)
        if p.is_symlink():errors.append('Public template must remain portable without symlinks: '+str(rel))
        if p.name=='.env' or p.suffix.lower() in {'.pem','.key','.p12','.pfx','.sqlite','.db'}:errors.append('Private/secret artifact in public source: '+str(rel))
        try:body=p.read_text(encoding='utf-8')
        except UnicodeDecodeError:errors.append('Unexpected binary artifact: '+str(rel));continue
        for pattern in forbidden:
            if re.search(pattern,body,re.I):errors.append('Private path/client/secret pattern: '+str(rel)+' '+pattern)
        if '\u2014' in body:errors.append('Authored em dash: '+str(rel))
        if p.suffix=='.py':
            try:ast.parse(body,filename=str(rel))
            except SyntaxError as e:errors.append(str(e))
        if p.suffix=='.md':
            for target in re.findall(r'\]\(([^)]+)\)',body):
                raw=target.strip('<>').split('#',1)[0]
                if not raw or re.match(r'^[a-z]+:',raw):continue
                if not (p.parent/raw).exists():errors.append('Broken public documentation link: '+str(rel)+' -> '+target)
    if (ROOT/'client.json').exists() or any((ROOT/p).exists() for p in ['clients','workspaces','private','outputs']):errors.append('Real/generated client storage must not exist inside the public template')
    if str(len(questions))+'-question' not in (ROOT/'README.md').read_text():errors.append('README question count differs from actual bank')
    return errors

if __name__=='__main__':
    errors=audit()
    if errors:
        print('PUBLIC TEMPLATE AUDIT FAILED')
        for error in errors:print('- '+error)
        sys.exit(1)
    count=sum(len(g['questions']) for g in json.loads((ROOT/'_shared/questions.json').read_text())['groups'])
    print(f'PUBLIC TEMPLATE AUDIT PASS: {count} questions, answer/file mapping, shared entries, portable template, local links and selected privacy patterns.')
    print('Scope: source integrity and selected pattern detection, not semantic privacy certification or client production reliability.')
