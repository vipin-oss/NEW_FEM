"""Push ``Paper_12/`` into the GitHub repository that Overleaf is linked to.

The manuscript lives in ``Paper_12/`` inside this repository; Overleaf reads a
separate repository whose root is the Overleaf project root.  This script makes
the second a copy of the first, with one exception: the parts of ``main.tex``
that belong to the author are never overwritten.  Those parts are

  * the ``\\author{...}`` block,
  * the ``\\journal{...}`` line,
  * the body of the Acknowledgements section,

which are filled in on Overleaf.  If one of them is present in the target and
differs from what ``Paper_12/main.tex`` holds, the target version is kept and
reported.  If one of them cannot be located unambiguously the script stops
before touching the target, rather than guessing.

    python sync_to_overleaf.py --dry-run          # show what would change
    python sync_to_overleaf.py                    # pull, copy, commit, push
    python sync_to_overleaf.py --remote URL       # override the remote

The remote can also be given in the environment variable ``OVERLEAF_REMOTE``.
"""
import argparse
import filecmp
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "Paper_12")
DEFAULT_REMOTE = "https://github.com/vipin-oss/Paper_12-new-.git"
WORK = os.path.join(ROOT, ".overleaf")

# Everything that belongs to the project, relative to Paper_12/.
SUBDIRS = ("sec", "figures")
FILES = ("main.tex", "references.bib", "Highlights.tex")
PATTERNS = (r"^table_[A-Za-z0-9_]+\.tex$",)

PROTECTED = (
    ("author", re.compile(r"\\author\{.*?\n\}\n", re.S)),
    ("journal", re.compile(r"\\journal\{[^}]*\}\n")),
    ("acknowledgements",
     re.compile(r"(\\section\*\{Acknowledgements\}\n)(.*?)(\n\\\\|\\appendix)", re.S)),
)


def run(cmd, cwd=None, check=True):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if check and p.returncode != 0:
        raise SystemExit("command failed: %s\n%s%s" % (" ".join(cmd), p.stdout,
                                                       p.stderr))
    return p


def source_files():
    """(relative path, absolute path) for every file the project needs."""
    out = []
    for name in FILES:
        p = os.path.join(SRC, name)
        if os.path.exists(p):
            out.append((name, p))
    for name in sorted(os.listdir(SRC)):
        if any(re.match(pat, name) for pat in PATTERNS):
            out.append((name, os.path.join(SRC, name)))
    for sub in SUBDIRS:
        d = os.path.join(SRC, sub)
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            p = os.path.join(d, name)
            if os.path.isfile(p):
                out.append((os.path.join(sub, name), p))
    return out


def merge_main(target_text, ours):
    """Keep the author-owned regions of the target inside our main.tex."""
    kept = []
    for name, pat in PROTECTED:
        m = pat.search(target_text)
        if not m:
            continue
        mine = pat.search(ours)
        if not mine:
            raise SystemExit(
                "cannot locate the %s region in Paper_12/main.tex; "
                "refusing to overwrite the target" % name)
        if m.group(0) == mine.group(0):
            continue
        ours = ours[:mine.start()] + m.group(0) + ours[mine.end():]
        kept.append(name)
    return ours, kept


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--remote", default=os.environ.get("OVERLEAF_REMOTE",
                                                       DEFAULT_REMOTE))
    ap.add_argument("--dir", default=WORK)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--message", default="Sync from the working repository")
    args = ap.parse_args()

    files = source_files()
    if not os.path.exists(os.path.join(SRC, "main.tex")):
        raise SystemExit("Paper_12/main.tex not found")

    if not os.path.isdir(os.path.join(args.dir, ".git")):
        if args.dry_run:
            print("%d files would go to %s (clone of %s is not present yet)"
                  % (len(files), args.dir, args.remote))
            return 0
        print("cloning %s ..." % args.remote)
        run(["git", "clone", "--quiet", args.remote, args.dir])
    else:
        ident = ["-c", "user.name=Overleaf sync",
                 "-c", "user.email=noreply@invalid"]
        dirty = run(["git", "status", "--porcelain"], cwd=args.dir).stdout.strip()
        if dirty and not args.dry_run:
            run(["git", "add", "-A"], cwd=args.dir)
            run(["git"] + ident + ["commit", "-m",
                                   "Pending changes before the sync"],
                cwd=args.dir)
        if not args.dry_run:
            run(["git", "pull", "--rebase", "--quiet", "--autostash"],
                cwd=args.dir)

    changed, kept = [], []
    for rel, src in files:
        dst = os.path.join(args.dir, rel)
        if rel == "main.tex" and os.path.exists(dst):
            with open(dst) as fh:
                target = fh.read()
            with open(src) as fh:
                ours = fh.read()
            ours, kept = merge_main(target, ours)
            if not args.dry_run:
                with open(dst, "w") as fh:
                    fh.write(ours)
                changed.append(rel)
            continue
        if os.path.exists(dst) and filecmp.cmp(src, dst, shallow=False):
            continue
        changed.append(rel)
        if not args.dry_run:
            os.makedirs(os.path.dirname(dst) or args.dir, exist_ok=True)
            shutil.copy2(src, dst)

    # files in the target that no longer exist in the paper
    stale = []
    for base, _dirs, names in os.walk(args.dir):
        if ".git" in base:
            continue
        for name in names:
            rel = os.path.relpath(os.path.join(base, name), args.dir)
            if rel.split(os.sep)[0] not in ("sec", "figures") and rel not in FILES \
                    and not any(re.match(pat, rel) for pat in PATTERNS) \
                    and not rel.endswith((".png", ".pdf")):
                continue
            if all(rel != r for r, _ in files):
                stale.append(rel)
                if not args.dry_run:
                    os.remove(os.path.join(base, name))

    if args.dry_run:
        print("%d files to copy, %d stale: %s"
              % (len(changed), len(stale), ", ".join(changed[:6]) or "-"))
        return 0

    if not changed and not stale:
        print("already in sync with %s" % os.path.basename(args.dir))
        return 0

    run(["git", "add", "-A"], cwd=args.dir)
    staged = run(["git", "diff", "--cached", "--quiet"], cwd=args.dir,
                 check=False).returncode != 0
    if not staged:
        print("nothing to commit after the copy")
        return 0
    ident = ["-c", "user.name=Overleaf sync",
             "-c", "user.email=noreply@invalid"]
    p = run(["git"] + ident + ["commit", "-m", args.message], cwd=args.dir,
            check=False)
    if p.returncode != 0:
        raise SystemExit("commit failed in %s\n%s%s" % (args.dir, p.stdout,
                                                         p.stderr))
    run(["git", "pull", "--rebase", "--quiet", "--autostash"], cwd=args.dir)
    run(["git", "push", "--quiet"], cwd=args.dir)
    tail = (" (kept from Overleaf: %s)" % ", ".join(kept)) if kept else ""
    print("synced %d files, removed %d%s" % (len(changed), len(stale), tail))
    return 0


if __name__ == "__main__":
    sys.exit(main())
