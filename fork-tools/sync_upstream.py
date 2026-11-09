#!/usr/bin/env python3
"""Sync this fork with a newer upstream tree, keeping the fork's own changes.

The fork is a snapshot (no shared git history with upstream), so the sync is:
take the new upstream tree, put this fork's files back on top, re-apply the
package_version() patch, and regenerate mgu-repo.json.

    python fork-tools/sync_upstream.py <new-upstream-dir> [<fork-dir>]

Prints what changed in the catalogs (app versions, descriptions) so stale
fork-authored Chinese descriptions can be spotted.
"""
import json
import pathlib
import shutil
import subprocess
import sys

new = pathlib.Path(sys.argv[1])
fork = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path(__file__).resolve().parent.parent
old = pathlib.Path(sys.argv[3]) if len(sys.argv) > 3 else None
SKIP_TOP = {'.git'}


def app_jsons(root):
    out = {}
    for d in sorted((root / 'apps').iterdir()):
        f = d / 'app.json'
        if d.is_dir() and f.exists():
            out[d.name] = json.loads(f.read_text(encoding='utf-8'))
    return out


# 1. our patched block, before the copy overwrites it
loc = (fork / 'kit/tools/localize.py').read_text(encoding='utf-8')
our_block = loc[loc.index('def package_version('):loc.index('def localize_spec(')]
up_loc = (new / 'kit/tools/localize.py').read_text(encoding='utf-8')
up_block = up_loc[up_loc.index('def package_version('):up_loc.index('def localize_spec(')]
if our_block == up_block:
    sys.exit('the fork patch is not in the working copy - refusing to sync blindly')
if "language == 'zh-CN'" not in our_block:
    sys.exit('the fork patch does not look like ours - refusing to sync blindly')

# 2. copy the new upstream tree over the fork (upstream removes nothing here)
copied = 0
for p in new.rglob('*'):
    rel = p.relative_to(new)
    if rel.parts and rel.parts[0] in SKIP_TOP:
        continue
    dest = fork / rel
    if p.is_dir():
        dest.mkdir(parents=True, exist_ok=True)
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dest)
        copied += 1
print(f'copied {copied} files from {new}')

# 3. the upstream manifest this fork was generated from
shutil.copy2(new / 'mgu-repo.json', fork / 'mgu-repo.json.upstream')

# 4. re-apply the fork patch
loc2 = (fork / 'kit/tools/localize.py').read_text(encoding='utf-8')
if loc2.count(up_block) != 1:
    sys.exit('upstream package_version() changed shape - merge by hand')
(fork / 'kit/tools/localize.py').write_text(loc2.replace(up_block, our_block), encoding='utf-8', newline='\n')
print('re-applied the fork patch to kit/tools/localize.py')

# 5. what the catalogs say now
if old:
    o, n = app_jsons(old), app_jsons(new)
    print('\napp versions: old -> new')
    for k in sorted(set(o) | set(n)):
        ov, nv = (o.get(k) or {}).get('version'), (n.get(k) or {}).get('version')
        tag = 'NEW APP' if k not in o else ('same' if ov == nv else 'UPDATE')
        print(f'  {k:<18} {str(ov):<8} -> {str(nv):<8} {tag}')
    changed = [(k, o[k].get('description', ''), n[k].get('description', ''))
               for k in sorted(n) if k in o and o[k].get('description') != n[k].get('description')]
    print(f'\ndescriptions changed upstream: {len(changed)} (the fork Chinese text may be stale)')
    for k, a, b in changed:
        print(f'  {k}:\n    old EN: {a[:150]}\n    new EN: {b[:150]}')
    tchanged = [(k, o[k].get('title', ''), n[k].get('title', '')) for k in sorted(n)
                if k in o and o[k].get('title') != n[k].get('title')]
    if tchanged:
        print('\ntitles changed upstream:')
        for k, a, b in tchanged:
            print(f'  {k}: {a!r} -> {b!r}')

# 6. regenerate the fork manifest
subprocess.run([sys.executable, str(fork / 'fork-tools/gen_mgu_repo.py'), str(fork)], check=True)
