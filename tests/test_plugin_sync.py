"""Tests for scripts/sync_plugin.py — canonical → plugin mirroring and drift check."""

import importlib.util
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

spec = importlib.util.spec_from_file_location("sync_plugin", REPO_ROOT / "scripts" / "sync_plugin.py")
sync_plugin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync_plugin)


def _make_tree(root: Path) -> Path:
    skills = root / "src" / "agile_backlog" / "bundled_skills" / "demo-skill"
    skills.mkdir(parents=True)
    (skills / "SKILL.md").write_text("---\nname: demo-skill\n---\nbody\n")
    hooks = root / "src" / "agile_backlog" / "bundled_hooks"
    hooks.mkdir(parents=True)
    (hooks / "post-tool-logger.sh").write_text("#!/usr/bin/env bash\necho hook\n")
    (root / ".claude" / "hooks").mkdir(parents=True)
    (root / ".claude" / "hooks" / "post-tool-logger.sh").write_text("#!/usr/bin/env bash\necho hook\n")
    (root / "plugin" / "skills" / "backlog").mkdir(parents=True)  # plugin-only skill, preserved
    (root / "plugin" / "skills" / "backlog" / "SKILL.md").write_text("stub\n")
    return root


class TestSync:
    def test_sync_mirrors_and_check_passes(self, tmp_path: Path):
        root = _make_tree(tmp_path)
        changed = sync_plugin.sync(root)
        assert (root / "plugin" / "skills" / "demo-skill" / "SKILL.md").exists()
        assert (root / "plugin" / "hooks" / "scripts" / "post-tool-logger.sh").exists()
        assert (root / "plugin" / "skills" / "backlog" / "SKILL.md").exists()  # preserved
        assert changed
        assert sync_plugin.check(root) == []
        assert sync_plugin.sync(root) == []  # idempotent

    def test_check_detects_drift_and_stale_skill(self, tmp_path: Path):
        root = _make_tree(tmp_path)
        sync_plugin.sync(root)
        (root / "plugin" / "skills" / "demo-skill" / "SKILL.md").write_text("tampered\n")
        assert sync_plugin.check(root) != []
        sync_plugin.sync(root)
        stale = root / "plugin" / "skills" / "removed-skill"
        stale.mkdir()
        (stale / "SKILL.md").write_text("x\n")
        assert sync_plugin.check(root) != []

    def test_check_detects_dogfood_hook_drift(self, tmp_path: Path):
        root = _make_tree(tmp_path)
        sync_plugin.sync(root)
        (root / ".claude" / "hooks" / "post-tool-logger.sh").write_text("#!/usr/bin/env bash\necho drift\n")
        assert sync_plugin.check(root) != []


class TestRepoIsInSync:
    def test_repo_plugin_matches_canonical(self):
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "sync_plugin.py"), "--check"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0, f"plugin/ drifted from canonical:\n{result.stdout}{result.stderr}"
