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


# 1. the fork's patched localize.py, before the copy overwrites it. Every
#    top-level function that differs from upstream's is re-applied after the
#    copy, so a second patched function (load_locale) survives as well.
def blocks(text):
    """{name: chunk} for a module's top-level defs, the header under ''."""
    out, name, buf = {}, '', []
    for line in text.splitlines(keepends=True):
        if line.startswith('def '):
            out[name] = ''.join(buf)
            name = line[4:line.index('(')].strip()
            buf = [line]
        else:
            buf.append(line)
    out[name] = ''.join(buf)
    return out


up_text = (new / 'kit/tools/localize.py').read_text(encoding='utf-8')
our_text = (fork / 'kit/tools/localize.py').read_text(encoding='utf-8')
up_blocks, our_blocks = blocks(up_text), blocks(our_text)
patched = [n for n in our_blocks if n and n in up_blocks and our_blocks[n] != up_blocks[n]]
vanished = [n for n in our_blocks if n and n not in up_blocks]
if not patched:
    sys.exit('the fork patch is not in the working copy - refusing to sync blindly')
if vanished:
    sys.exit(f'upstream no longer has {", ".join(vanished)}() - merge by hand')
for n in patched:
    if 'zh-CN' not in our_blocks[n]:
        sys.exit(f'the fork patch to {n}() does not look like ours - refusing to sync blindly')
print('fork-patched functions: ' + ', '.join(f'{n}()' for n in patched))

# 2. copy the new upstream tree over the fork; with <old> given, also drop the
#    files upstream removed (a fork-only file is never in an upstream tree, so
#    this can only touch files upstream itself had)
copied = deleted = 0
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
if old:
    for p in old.rglob('*'):
        if not p.is_file():
            continue
        rel = p.relative_to(old)
        if rel.parts and rel.parts[0] in SKIP_TOP:
            continue
        if (new / rel).exists():
            continue
        gone = fork / rel
        if gone.exists():
            gone.unlink()
            deleted += 1
            print(f'  dropped (upstream removed it): {rel}')
    for d in sorted((x for x in fork.rglob('*') if x.is_dir()), key=lambda x: -len(x.parts)):
        rel = d.relative_to(fork)
        if rel.parts and (rel.parts[0] in SKIP_TOP or rel.parts[0] == 'fork-tools'):
            continue
        try:
            d.rmdir()  # only if the dropped files had left it empty
        except OSError:
            pass
print(f'deleted {deleted} files upstream dropped')

# 3. the upstream manifest this fork was generated from
shutil.copy2(new / 'mgu-repo.json', fork / 'mgu-repo.json.upstream')

# 4. re-apply every fork-patched function
loc2 = (fork / 'kit/tools/localize.py').read_text(encoding='utf-8')
for n in patched:
    if loc2.count(up_blocks[n]) != 1:
        sys.exit(f'upstream {n}() changed shape - merge by hand')
    loc2 = loc2.replace(up_blocks[n], our_blocks[n])
(fork / 'kit/tools/localize.py').write_text(loc2, encoding='utf-8', newline='\n')
print('re-applied the fork patch: ' + ', '.join(f'{n}()' for n in patched))

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
