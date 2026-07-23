"""Mirror canonical package content into plugin/ (and the dogfood .claude hook copy).

Canonical sources:
  src/agile_backlog/bundled_skills/  -> plugin/skills/        (plugin-only skills in KEEP are preserved)
  src/agile_backlog/bundled_hooks/   -> plugin/hooks/scripts/
  src/agile_backlog/bundled_hooks/post-tool-logger.sh -> .claude/hooks/post-tool-logger.sh (dogfood copy)

Usage: python scripts/sync_plugin.py [--check]
  --check: exit 1 listing drifted paths instead of writing.
"""

import argparse
import filecmp
import shutil
import sys
from pathlib import Path

KEEP = {"backlog"}  # plugin-only skills, not synced from the package


def _pairs(root: Path) -> list[tuple[Path, Path]]:
    pkg = root / "src" / "agile_backlog"
    pairs = []
    for skill in sorted((pkg / "bundled_skills").iterdir()):
        if skill.is_dir():
            pairs.append((skill, root / "plugin" / "skills" / skill.name))
    for hook in sorted((pkg / "bundled_hooks").iterdir()):
        if hook.is_file():
            pairs.append((hook, root / "plugin" / "hooks" / "scripts" / hook.name))
            pairs.append((hook, root / ".claude" / "hooks" / hook.name))
    return pairs


def _stale_skills(root: Path) -> list[Path]:
    plugin_skills = root / "plugin" / "skills"
    if not plugin_skills.exists():
        return []
    canonical = {p.name for p in (root / "src" / "agile_backlog" / "bundled_skills").iterdir() if p.is_dir()}
    return [p for p in sorted(plugin_skills.iterdir()) if p.is_dir() and p.name not in canonical | KEEP]


def _files_under(path: Path) -> list[Path]:
    return sorted(p for p in path.rglob("*") if p.is_file())


def _differs(src: Path, dest: Path) -> bool:
    if src.is_file():
        return not dest.exists() or not filecmp.cmp(src, dest, shallow=False)
    src_files = _files_under(src)
    if not dest.exists():
        return True
    if [p.relative_to(src) for p in src_files] != [p.relative_to(dest) for p in _files_under(dest)]:
        return True
    return any(not filecmp.cmp(f, dest / f.relative_to(src), shallow=False) for f in src_files)


def check(root: Path) -> list[str]:
    drifted = [str(dest.relative_to(root)) for src, dest in _pairs(root) if _differs(src, dest)]
    drifted += [f"{p.relative_to(root)} (stale — not in bundled_skills)" for p in _stale_skills(root)]
    return drifted


def sync(root: Path) -> list[str]:
    changed = []
    for src, dest in _pairs(root):
        if not _differs(src, dest):
            continue
        if src.is_file():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
        else:
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(src, dest)
        changed.append(str(dest.relative_to(root)))
    for stale in _stale_skills(root):
        shutil.rmtree(stale)
        changed.append(f"{stale.relative_to(root)} (removed)")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Report drift without writing; exit 1 if drifted.")
    args = parser.parse_args()
    root = Path(__file__).parent.parent
    if args.check:
        drifted = check(root)
        if drifted:
            print("plugin/ is out of sync — run: python scripts/sync_plugin.py")
            for path in drifted:
                print(f"  {path}")
            return 1
        print("plugin/ is in sync.")
        return 0
    changed = sync(root)
    print(f"Synced {len(changed)} path(s)." if changed else "Already in sync.")
    for path in changed:
        print(f"  {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
