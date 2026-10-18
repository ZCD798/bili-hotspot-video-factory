import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "production"))
from validate_inputs import validate

EXAMPLE = ROOT / "production/examples/deepseek"

class InputValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        shutil.copyfile(EXAMPLE / "story.json", self.root / "story.json")
        shutil.copyfile(EXAMPLE / "hotsearch_snapshot.json", self.root / "hotsearch_snapshot.json")
        manifest = json.loads((EXAMPLE / "assets_manifest.json").read_text(encoding="utf-8"))
        for asset in manifest["assets"]:
            (self.root / "assets").mkdir(exist_ok=True)
            (self.root / asset["path"]).write_bytes(b"fixture")
            asset.pop("sha256", None)
        (self.root / "assets_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_checked_in_story_and_rights_manifest_validate(self):
        story, manifest, assets, snapshot = validate(
            self.root / "story.json", self.root / "assets_manifest.json"
        )
        self.assertEqual(story["language"], "zh-CN")
        self.assertEqual(len(assets), 3)
        self.assertTrue(snapshot.is_file())

    def test_unreviewed_asset_is_rejected(self):
        manifest_path = self.root / "assets_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["assets"][0]["rights_reviewed"] = False
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "explicit human rights review"):
            validate(self.root / "story.json", manifest_path)

    def test_asset_path_traversal_is_rejected(self):
        manifest_path = self.root / "assets_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["assets"][0]["path"] = "../../escape.jpg"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "path escapes the manifest directory"):
            validate(self.root / "story.json", manifest_path)

if __name__ == "__main__":
    unittest.main()
