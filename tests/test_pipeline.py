import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PipelineTests(unittest.TestCase):
    def test_example_config_starts_safe(self):
        config = json.loads((ROOT / "config.example.json").read_text(encoding="utf-8"))
        self.assertFalse(config["safety"]["sending_enabled"])
        self.assertTrue(config["safety"]["dry_run"])
        self.assertFalse(config["safety"]["withdraw_invites_enabled"])
        self.assertIn("[PLACEHOLDER", config["copy"]["open_profile_dm"]["body"])
        self.assertIn("[PLACEHOLDER", config["copy"]["post_connect_dm"]["body"])

    def test_example_pipeline_builds_a_dry_batch(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            shutil.copytree(ROOT / "scripts", work / "scripts")
            shutil.copytree(ROOT / "data", work / "data")
            (work / "state" / "daily").mkdir(parents=True)
            shutil.copy(ROOT / "config.example.json", work / "config.json")
            shutil.copy(work / "data" / "leads.example.csv", work / "data" / "leads.csv")

            for script in ("build_state.py", "select_batch.py", "report.py"):
                subprocess.run(
                    [sys.executable, str(work / "scripts" / script)],
                    cwd=work,
                    check=True,
                    capture_output=True,
                    text=True,
                )

            leads = json.loads((work / "state" / "leads.json").read_text(encoding="utf-8"))
            batches = list((work / "state" / "daily").glob("batch_*.json"))
            self.assertEqual(6, len(leads))
            self.assertEqual(1, len(batches))
            batch = json.loads(batches[0].read_text(encoding="utf-8"))
            self.assertFalse(batch["sending_enabled"])
            self.assertEqual(6, len(batch["outreach_candidates"]))


if __name__ == "__main__":
    unittest.main()
