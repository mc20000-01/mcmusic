# Purging build binaries from git history (not performed)

`builds/` binaries are no longer tracked at HEAD (commit `276dfeb`), but the old
bytes are still reachable from older commits. As of that commit the repository
has about **3.0 GiB** of loose objects, roughly **3.17 GiB** of historical
blobs under `builds/`/`apps/`, and **82** `Update published builds` bot commits.
Only a history rewrite reclaims that space. **No rewrite has been run**, no
history has been rewritten, and nothing has been force-pushed.

This document is the runbook for a *future, separately approved* maintenance
window. It must be coordinated: rewriting public history changes every commit
SHA and every tag, including `v4.3.0` and the rolling `latest` tag.

## Before you start

1. Freeze pushes to `mc20000-01/mcmusic` and tell every maintainer, fork owner
   and open-PR author. Everyone must re-clone afterwards; `git pull` is not
   enough.
2. Save a full backup outside the working repository:

   ```bash
   git clone --mirror git@github.com:mc20000-01/mcmusic.git \
     ~/mcmusic-history-backup.git
   du -sh ~/mcmusic-history-backup.git
   ```

3. Confirm the current release data is safe independently of git:

   ```bash
   gh release list --limit 50
   gh api repos/mc20000-01/mcmusic/releases/latest \
     -q '.assets[] | [.name, .digest, .size] | @tsv'
   gh api repos/mc20000-01/mcmusic/releases --paginate \
     -q '[.[].assets[].name] | unique | length'
   ```

   Every tracked binary from the old `builds/` snapshot was backfilled into a
   non-latest GitHub Release before those files were untracked. Verify this
   again before a rewrite; a release asset is the only surviving copy of an
   old APK.

4. Work in a **fresh clone**, not in the daily checkout. `git filter-repo`
   refuses dirty or non-fresh repositories unless forced.

   ```bash
   git clone --no-local git@github.com:mc20000-01/mcmusic.git \
     ~/mcmusic-history-purge
   cd ~/mcmusic-history-purge
   python3 -m pip install --user git-filter-repo
   ```

## Exact rewrite command

This removes binary paths from every commit while preserving the three small
tracked text files under `builds/`:

```bash
git filter-repo --force --replace-refs delete-no-add \
  --filename-callback '
import os
name = filename.decode("utf-8", "replace").lstrip("/")
if name.startswith(("apps/", "web/apps/", "releases/")):
    return b""
if name.startswith("builds/") and name not in (
    "builds/README.md",
    "builds/SHA256SUMS",
    "builds/release-manifest.json",
):
    return b""
return filename
'
```

`--filename-callback` returns an empty path to drop a file from each tree;
returning the original filename keeps it. Empty commits and empty merges are
pruned automatically. Do not add `--prune-degenerate never` unless you
deliberately want empty commits left behind.

If you do not need the text files in old commits, the simpler form is:

```bash
git filter-repo --force --replace-refs delete-no-add \
  --path builds/ --path apps/ --path web/apps/ --path releases/ \
  --invert-paths
```

In that case recreate `builds/README.md`, `builds/SHA256SUMS` and
`builds/release-manifest.json` on top of the rewritten `main` (for example with
`python3 scripts/write_release_manifest.py` plus the README from the backup)
and commit them again.

## Verify before publishing the rewrite

```bash
git count-objects -vH
du -sh .git
git ls-tree -r --name-only HEAD builds apps
git log --oneline -5
git tag --list | sort -V
git log --all --pretty=format: --name-only -- builds apps web/apps releases \
  | grep -E '\.(apk|deb|AppImage|dmg|exe|msi|zip)$' | sort -u
./scripts/check-repo-size.sh
./tests/test_check_versions.sh
./tests/test_publish_release.sh
python3 -m pytest tests -q \
  --ignore=tests/test_qt_ui.py \
  --ignore=tests/test_qt_client.py \
  --ignore=tests/test_qt_icons.py \
  --ignore=tests/test_widgets.py \
  --ignore=tests/test_no_qt_shadowing.py \
  --ignore=tests/test_qt_selftest.py \
  --ignore=tests/test_updates.py
```

The binary `grep` must print nothing. `check-repo-size.sh` should report a tree
of a few MiB, and `.git` should drop from ~3.0 GiB to tens of MiB. Compare the
current release manifest against the GitHub API output from step 3.

## Publishing the rewritten history

Only after verification and explicit approval:

```bash
git remote set-url origin git@github.com:mc20000-01/mcmusic.git
git push --force --all origin
git push --force --tags origin
```

GitHub Releases are **not** rewritten by this: their assets and asset digests
stay where they are, but the release `target_commitish` values point at the old
commit SHAs. Decide deliberately whether to edit each release target or leave
the historical pointer as-is. The rolling `latest` tag is also force-pushed by
`scripts/publish-release.sh`; re-run or verify that workflow after the rewrite
so `releases/latest` still resolves to tag `latest`.

## Consequences

- Every commit SHA changes, including the `v4.3.0` tag and all older tags.
  Documentation, issue links and pinned dependencies referencing old SHAs
  become stale.
- Every existing clone, fork and open pull request is based on the old history.
  Contributors must back up local work, delete their clone and re-clone; open
  PRs should be re-created from the new history.
- `git pull` in an old clone can reintroduce the removed objects or produce a
  confusing unrelated-history error. Do not mix old and new commits.
- GitHub Release assets, `apps/` caches and downloaded client binaries are
  unaffected. They are the authoritative artifact store.
- If anything looks wrong, stop and restore from `~/mcmusic-history-backup.git`.
  Restoring means force-pushing the original refs, which requires the same
  coordination as the rewrite.
- This rewrite does not change the current tree: `builds/` remains an ignored
  staging directory and CI still enforces the 25 MiB / 100 MiB guard.
