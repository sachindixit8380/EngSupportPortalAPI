"""Tests for tendril manifest"""

import unittest
import json


class TendrilManifestTests(unittest.TestCase):
    """Tests of tendril manifest"""

    manifest_file = 'tendril/conf/manifest.json.template'

    def setUp(self):
        """Set up tasks."""
        self.manifest = open(self.manifest_file)

    def tearDown(self):
        """Tear down tasks."""
        self.manifest.close()

    def test_tendril_manifest_valid(self):
        """Is the file tendril/conf/manifest.json.template valid?"""
        try:
            manifest_data = json.load(self.manifest)
        except ValueError:
            assert False, self.manifest_file + " is not valid json"

        assert type(manifest_data) is dict, "loaded manifest json is not a dict"

if __name__ == '__main__':
    unittest.main()
