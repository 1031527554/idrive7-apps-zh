#!/usr/bin/env python3
"""Write this fork's mgu-repo.json.

The fork lists every app in mgu-repo.json's `components` (one entry each, so
each can carry its own Store-list texts) and builds Chinese on the unit:

    "args": ["{id}", "--language", "zh-CN"]

Titles come from upstream's own zh-CN catalog (kit/runtime/locales/zh-CN.json,
untouched). Descriptions come from fork-tools/zh-CN-descriptions.json, which is
this fork's own addition - see its _note. Nothing else is invented: build comes
from the upstream mgu-repo.json; requires and mguHmi are merged from it with each
app's own app.json (upstream moved the dependencies there on 2026-11-16) and are
left out when empty, so the Store reads the app's own declaration instead of an
empty object of ours shadowing it.

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
    base_requires = dict(apps_spec.get('requires') or {})
    base_hmi = apps_spec.get('mguHmi')

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
        entry = {
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
            'build': build,
        }
        # Dependencies moved into each app.json upstream (2026-11-16). The Store reads them as
        # `entry[k] !== undefined ? entry[k] : app[k]` (sources.js pick()), so writing our own
        # empty object here SHADOWS the app's own declaration and the apps would install
        # without idrive7-renderd / mgu-inputgate. Merge both, and only write a non-empty key.
        requires = dict(base_requires)
        requires.update(app.get('requires') or {})
        if requires:
            entry['requires'] = requires
        # same for mguHmi: absent upstream's block, leave it to the app.json (ID7 and ID8)
        hmi = base_hmi if base_hmi is not None else app.get('mguHmi')
        if hmi:
            entry['mguHmi'] = list(hmi)
        components.append(entry)

    doc = {'schema': 1, 'components': components, 'tools': upstream.get('tools', [])}
    for k, v in upstream.items():
        if k not in ('schema', 'apps', 'components', 'tools'):
            doc[k] = v
    (root / 'mgu-repo.json').write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                                        encoding='utf-8', newline='\n')

    print(f'mgu-repo.json written: {len(components)} app components, {len(doc["tools"])} tools')
    print(f'build.args = {build["args"]}   output = {build.get("output")}')
    deps = sorted({k for c in components for k in (c.get('requires') or {})})
    print(f'requires   = {deps if deps else "none written: each app.json declares its own"}')
    print(f'mguHmi     = {sorted({h for c in components for h in (c.get("mguHmi") or [])}) or "not written: the app.json has it"}')
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
