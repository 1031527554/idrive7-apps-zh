#!/usr/bin/env python3
"""Write this fork's mgu-repo.json.

The fork lists every app in mgu-repo.json's `components` (one entry each, so
each can carry its own Store-list texts) and builds Chinese on the unit:

    "args": ["{id}", "--language", "zh-CN"]

Titles come from upstream's own zh-CN catalog (kit/runtime/locales/zh-CN.json,
untouched). Descriptions come from fork-tools/zh-CN-descriptions.json, which is
this fork's own addition - see its _note. Nothing else is invented: build,
requires, mguHmi and the tools come from the upstream mgu-repo.json.

    python fork-tools/gen_mgu_repo.py [<fork-dir>]
"""
import json
import pathlib
import re
import sys

SEMVER = re.compile(r'^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$')
FORK_DIR = pathlib.Path(__file__).resolve().parent.parent
UPSTREAM = FORK_DIR / 'mgu-repo.json.upstream'


def main():
    root = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else FORK_DIR
    source = UPSTREAM if UPSTREAM.exists() else root / 'mgu-repo.json'
    upstream = json.loads(source.read_text(encoding='utf-8'))
    zh = json.loads((root / 'kit/runtime/locales/zh-CN.json').read_text(encoding='utf-8'))
    desc_zh = json.loads((FORK_DIR / 'fork-tools/zh-CN-descriptions.json').read_text(encoding='utf-8'))

    apps_spec = upstream['apps']
    assert isinstance(apps_spec, dict), 'expected the upstream object form of "apps"'
    build = dict(apps_spec['build'])
    build['args'] = ['{id}', '--language', 'zh-CN']
    requires = dict(apps_spec.get('requires') or {})
    hmi = list(apps_spec.get('mguHmi') or ['ID7'])

    components, problems = [], []
    for d in sorted((root / 'apps').iterdir()):
        if not d.is_dir():
            continue
        app = json.loads((d / 'app.json').read_text(encoding='utf-8'))
        if app.get('id') != d.name:
            problems.append(f'{d.name}: app.json id is {app.get("id")!r}')
        if not SEMVER.match(str(app.get('version', ''))):
            problems.append(f'{d.name}: version {app.get("version")!r} is not x.y.z')
        title = app.get('title') or d.name
        components.append({
            'id': d.name,
            'kind': 'app',
            'path': f'apps/{d.name}',
            'manifest': 'app.json',
            'title': title,
            'description': app.get('description') or '',
            'texts': {'zh-CN': {
                'title': zh.get(title, title),
                'description': desc_zh.get(d.name) or app.get('description') or '',
            }},
            'mguHmi': hmi,
            'requires': requires,
            'build': build,
        })

    doc = {'schema': 1, 'components': components, 'tools': upstream.get('tools', [])}
    for k, v in upstream.items():
        if k not in ('schema', 'apps', 'components', 'tools'):
            doc[k] = v
    (root / 'mgu-repo.json').write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                                        encoding='utf-8', newline='\n')

    print(f'mgu-repo.json written: {len(components)} app components, {len(doc["tools"])} tools')
    print(f'build.args = {build["args"]}   output = {build.get("output")}')
    print(f'requires   = {requires}')
    missing = [c['id'] for c in components if not desc_zh.get(c['id'])]
    if missing:
        print('no fork description for: ' + ', '.join(missing))
    for c in components:
        print(f'  {c["id"]:<18} {c["version"] if "version" in c else ""}  {c["title"]!r} -> {c["texts"]["zh-CN"]["title"]!r}')
    if problems:
        print('\nPROBLEMS:')
        for p in problems:
            print('  ' + p)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
