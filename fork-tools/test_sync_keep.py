#!/usr/bin/env python3
"""Acceptance test for the protected paths of sync_upstream.py.

It builds everything under a scratch directory and runs the sync against a
throw-away COPY of the fork, so the real fork (and especially its apps/) is
never written to. The scratch directory is deleted first if it exists.

    python fork-tools/test_sync_keep.py <scratch-dir> <real-11-11-upstream-dir> [<fork-dir>]

What it checks, on a mutated upstream tree in the scratch dir:

  * a non-protected file is overwritten, a non-protected file upstream dropped
    is deleted from the fork copy;
  * a protected file is left byte-identical even though upstream changed it;
  * a protected file upstream dropped is NOT deleted;
  * a protected file upstream added is NOT copied in;
  * upstream's added/modified/deleted files under the protected path are
    reported, and the per-file `kept (protected)` log plus the skip counts are
    printed;
  * with only two arguments it prints the "cannot compare" note;
  * a second run with <old> == <new> leaves the whole fork copy byte-identical
    (idempotence) while still re-applying load_locale(), package_version().
"""
import hashlib
import os
import pathlib
import shutil
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')  # the log holds zh-CN text

if len(sys.argv) < 3:
    sys.exit(__doc__.strip())

SCRATCH = pathlib.Path(sys.argv[1])
UPSTREAM_11_11 = pathlib.Path(sys.argv[2])
FORK = pathlib.Path(sys.argv[3]) if len(sys.argv) > 3 else pathlib.Path(__file__).resolve().parent.parent
MUT_UPSTREAM = SCRATCH / 'upstream-mutated'
FORK_COPY = SCRATCH / 'fork-copy'

# the test mutations: two under the protected prefix, two outside it, plus a
# sibling directory whose name merely starts with the protected one (must NOT
# be protected: the entry ends in '/')
PROTECTED_MODIFIED = 'apps/ambient_config/main.js'
PROTECTED_DELETED = 'apps/ambient_config/scenes.js'
PROTECTED_ADDED = 'apps/ambient_config/protected_new_file.js'
PLAIN_MODIFIED = 'apps/redline/main.js'
PLAIN_DELETED = 'apps/dyno/main.js'
SIBLING = 'apps/ambient_config_extra.js'  # same string prefix, different path (a dir sibling
# would be read by gen_mgu_repo.py as a 16th app, which is not what we are testing)

FAILURES = []


def check(label, ok, detail=''):
    print(f'  [{"PASS" if ok else "FAIL"}] {label}' + (f' - {detail}' if detail and not ok else ''))
    if not ok:
        FAILURES.append(label)


def read(p):
    return pathlib.Path(p).read_bytes()


def manifest(root):
    out = {}
    for p in sorted(pathlib.Path(root).rglob('*')):
        if p.is_file() and '.git' not in p.parts:
            out[p.relative_to(root).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def run_sync(new, fork, old=None):
    cmd = [sys.executable, str(fork / 'fork-tools/sync_upstream.py'), str(new), str(fork)]
    if old is not None:
        cmd.append(str(old))
    print(f'\n$ {" ".join(cmd)}')
    env = dict(os.environ, PYTHONIOENCODING='utf-8')
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', env=env)
    print(r.stdout.rstrip())
    if r.stderr.strip():
        print('stderr: ' + r.stderr.strip())
    if r.returncode != 0:
        check('sync_upstream.py exits 0', False, f'exit {r.returncode}')
    return r.stdout.replace('\\', '/')


def main():
    for name, path in (('11-11 upstream', UPSTREAM_11_11), ('fork', FORK)):
        if not path.exists():
            sys.exit(f'{name} does not exist: {path}')
    if SCRATCH in (UPSTREAM_11_11, FORK):
        sys.exit('the scratch directory must not be a source tree')
    if not SCRATCH.parent.exists():
        sys.exit(f'the scratch parent does not exist: {SCRATCH.parent}')

    print(f'scratch          : {SCRATCH}')
    print(f'real fork        : {FORK} (never written to; only the copy below is)')
    print(f'11-11 upstream   : {UPSTREAM_11_11} (read-only, used as <old>)')
    shutil.rmtree(SCRATCH, ignore_errors=True)
    SCRATCH.mkdir(parents=True)

    # 1. the fork copy we are allowed to damage
    print('\ncopying the fork (without .git) ...')
    shutil.copytree(FORK, FORK_COPY, ignore=shutil.ignore_patterns('.git'))
    plain_before = read(FORK_COPY / PLAIN_MODIFIED)
    protected_before = read(FORK_COPY / PROTECTED_MODIFIED)

    # 2. a mutated upstream tree: real 11-11 plus the six test differences
    print('copying the 11-11 upstream tree and mutating it ...')
    shutil.copytree(UPSTREAM_11_11, MUT_UPSTREAM, ignore=shutil.ignore_patterns('.git'))
    for rel in (PROTECTED_MODIFIED, PLAIN_MODIFIED):
        p = MUT_UPSTREAM / rel
        p.write_bytes(read(p) + b'\n/* temp upstream change - sync_upstream test */\n')
    for rel in (PROTECTED_DELETED, PLAIN_DELETED):
        (MUT_UPSTREAM / rel).unlink()
    (MUT_UPSTREAM / PROTECTED_ADDED).write_bytes(b'/* added upstream inside a protected path */\n')
    # the sibling exists in both trees with different content: it must be
    # overwritten, i.e. the "apps/ambient_config/" prefix must not leak into it
    (MUT_UPSTREAM / SIBLING).write_bytes(b'upstream sibling\n')
    (FORK_COPY / SIBLING).write_bytes(b'fork sibling\n')

    # 3. first sync: <old> is the pristine real 11-11 tree
    out = run_sync(MUT_UPSTREAM, FORK_COPY, UPSTREAM_11_11)
    print('\n-- assertions after the first sync --')
    check('non-protected file was overwritten by upstream',
          read(FORK_COPY / PLAIN_MODIFIED) == read(MUT_UPSTREAM / PLAIN_MODIFIED)
          and read(FORK_COPY / PLAIN_MODIFIED) != plain_before)
    check('non-protected file upstream dropped was deleted',
          not (FORK_COPY / PLAIN_DELETED).exists())
    check('protected file upstream modified is untouched',
          read(FORK_COPY / PROTECTED_MODIFIED) == protected_before
          and protected_before != read(MUT_UPSTREAM / PROTECTED_MODIFIED))
    check('protected file upstream dropped still exists',
          (FORK_COPY / PROTECTED_DELETED).exists())
    check('protected file upstream added was not copied',
          not (FORK_COPY / PROTECTED_ADDED).exists())
    check('per-file protected log line', f'kept (protected): {PROTECTED_MODIFIED}' in out)
    check('protected-drop log line', f'kept (protected, upstream removed it): {PROTECTED_DELETED}' in out)
    kept_n = sum(1 for p in (UPSTREAM_11_11 / 'apps/ambient_config').iterdir() if p.is_file())
    check(f'protected skip count is visible ({kept_n} files)',
          f'kept {kept_n} protected files (not copied): apps/ambient_config/' in out)
    check('upstream-added under protected path is reported',
          'upstream added (1):' in out and f'+ {PROTECTED_ADDED}' in out)
    check('upstream-modified under protected path is reported',
          'upstream modified (1):' in out and f'~ {PROTECTED_MODIFIED}' in out)
    check('upstream-deleted under protected path is reported',
          'upstream deleted (1):' in out and f'- {PROTECTED_DELETED}' in out)
    check('non-protected drop is still logged',
          f'dropped (upstream removed it): {PLAIN_DELETED}' in out)
    check('fork patch functions were recognised',
          'fork-patched functions: load_locale(), package_version()' in out
          and 're-applied the fork patch: load_locale(), package_version()' in out)
    check('a same-prefix sibling path is NOT protected',
          read(FORK_COPY / SIBLING) == b'upstream sibling\n'
          and f'kept (protected): {SIBLING}' not in out)
    check('the protected list of the log names every entry',
          out.count('protected paths (fork-tools/keep.json): apps/ambient_config/') == 1)

    # 4. two arguments only: the "cannot compare" note, no deletion pass
    print('\n-- no <old> baseline --')
    check('cannot-compare note', '无法比较，未检查保护路径的上游改动' in run_sync(MUT_UPSTREAM, FORK_COPY))

    # 5. <old> == <new>: the sync must be a no-op on the whole tree
    print('\n-- idempotence: <old> == <new> --')
    before = manifest(FORK_COPY)
    out = run_sync(MUT_UPSTREAM, FORK_COPY, MUT_UPSTREAM)
    after = manifest(FORK_COPY)
    check('a second sync changes no file at all',
          before == after,
          'changed: ' + ', '.join(sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))))
    check('idempotent run still names both patched functions',
          're-applied the fork patch: load_locale(), package_version()' in out)
    check('idempotent run reports no protected changes',
          'none - upstream did not touch the protected paths' in out)

    # 6. a working copy without keep.json must refuse to run rather than sync blind
    print('\n-- missing keep.json --')
    lonely = SCRATCH / 'no-keep'
    lonely.mkdir()
    shutil.copy2(FORK / 'fork-tools/sync_upstream.py', lonely / 'sync_upstream.py')
    r = subprocess.run([sys.executable, str(lonely / 'sync_upstream.py'), str(MUT_UPSTREAM), str(FORK_COPY)],
                       capture_output=True, text=True, encoding='utf-8', errors='replace',
                       env=dict(os.environ, PYTHONIOENCODING='utf-8'))
    err = (r.stdout + r.stderr).strip()
    print(err)
    check('a missing keep.json refuses to sync', r.returncode != 0 and 'is missing' in err)

    print(f'\n{"ALL CHECKS PASSED" if not FAILURES else "FAILED: " + ", ".join(FAILURES)}')
    print(f'(scratch kept for inspection: {SCRATCH})')
    return 1 if FAILURES else 0


if __name__ == '__main__':
    raise SystemExit(main())
