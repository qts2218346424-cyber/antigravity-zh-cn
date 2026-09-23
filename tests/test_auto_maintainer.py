import unittest
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from auto_maintainer import (
    extract_ui_strings_from_bundle,
    get_default_install_path,
    get_local_version_and_patch_state,
    perform_maintenance,
)

class TestAutoMaintainer(unittest.TestCase):
    def test_extract_ui_strings_from_bundle(self):
        sample_code = """
        z.createElement(Button, { title: "Open Settings", label: "Save Changes" }, "Submit Form");
        const x = { tooltip: "View Details", placeholder: "Search here...", text: "Cancel Operation" };
        """
        extracted = extract_ui_strings_from_bundle(sample_code)
        self.assertIn("Open Settings", extracted)
        self.assertIn("Save Changes", extracted)
        self.assertIn("Submit Form", extracted)
        self.assertIn("View Details", extracted)
        self.assertIn("Search here...", extracted)
        self.assertIn("Cancel Operation", extracted)

    def test_local_version_detection(self):
        install_dir = get_default_install_path()
        if install_dir and install_dir.is_dir():
            ver, is_patched = get_local_version_and_patch_state(install_dir)
            self.assertRegex(ver, r"^[0-9.]+$")
            self.assertTrue(is_patched)

    def test_dry_run_maintenance(self):
        res = perform_maintenance(dry_run=True)
        self.assertTrue(res)

if __name__ == '__main__':
    unittest.main()
