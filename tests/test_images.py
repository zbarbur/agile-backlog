import yaml

from agile_backlog.models import BacklogItem


class TestImagesField:
    def test_backlog_item_has_images_field(self):
        item = BacklogItem(id="test", title="Test", priority="P2", category="feature")
        assert item.images == []

    def test_images_field_stores_dict_entries(self):
        item = BacklogItem(
            id="test",
            title="Test",
            priority="P2",
            category="feature",
            images=[{"filename": "screenshot-1.png", "created": "2026-03-23"}],
        )
        assert len(item.images) == 1
        assert item.images[0]["filename"] == "screenshot-1.png"
        assert item.images[0]["created"] == "2026-03-23"

    def test_images_roundtrip_yaml_dict(self):
        images = [
            {"filename": "shot1.png", "created": "2026-03-23"},
            {"filename": "shot2.jpg", "created": "2026-03-22"},
        ]
        item = BacklogItem(
            id="roundtrip",
            title="Roundtrip",
            priority="P1",
            category="bug",
            images=images,
        )
        d = item.to_yaml_dict()
        yaml_str = yaml.dump(d, default_flow_style=False)
        loaded = yaml.safe_load(yaml_str)
        loaded["id"] = "roundtrip"
        restored = BacklogItem(**loaded)
        assert restored.images == images

    def test_images_directory_creation(self, tmp_path):
        item_id = "my-test-item"
        images_dir = tmp_path / "backlog" / "images" / item_id
        assert not images_dir.exists()
        images_dir.mkdir(parents=True, exist_ok=True)
        assert images_dir.exists()
        assert images_dir.is_dir()
        # Write a dummy file to verify the directory is usable
        test_file = images_dir / "test.png"
        test_file.write_bytes(b"\x89PNG\r\n\x1a\n")
        assert test_file.exists()
