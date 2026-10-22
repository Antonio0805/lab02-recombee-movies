"""Verificări locale; nu trimit cereri către Recombee și nu modifică dataset-ul."""

import contextlib
import hashlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
from recombee_api_client.api_requests import AddItemProperty, ListItemProperties

import recombee_properties as app


class DatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = pd.read_csv(app.PATH_DATASET, dtype=str, keep_default_na=False)

    def setUp(self):
        self.output = contextlib.redirect_stdout(io.StringIO())
        self.output.__enter__()
        self.addCleanup(self.output.__exit__, None, None, None)
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)

    def write_sample(self, df):
        path = Path(self.temporary.name) / "sample.csv"
        df.to_csv(path, index=False)
        return path

    def test_original_dataset_and_files_unchanged(self):
        df = app.load_dataset()
        self.assertEqual(len(df), 4803)
        self.assertEqual(len(df.columns), 20)
        self.assertEqual(df.iloc[0]["title"], "Avatar")
        expected_hashes = {
            "tmdb_5000_movies.csv": "1e0584a8dd374120e4ed4f2b81f0d2bd0eb95a554708e4a350d00ed5c46d2825",
            "tmdb_5000_credits.csv": "9d0050599ff88d40366c4841204b1489862bca346bfa46c20b05a65d14508435",
        }
        for name, expected in expected_hashes.items():
            self.assertEqual(hashlib.sha256((app.PATH_DATASET.parent / name).read_bytes()).hexdigest(), expected)

    def test_row_limits(self):
        for size in (99, 10001):
            sample = self.original.iloc[[0] * size].copy()
            with self.subTest(size=size), self.assertRaisesRegex(ValueError, "100–10.000"):
                app.load_dataset(self.write_sample(sample))

    def test_duplicate_ids_rejected(self):
        sample = self.original.head(100).copy()
        sample.loc[1, "id"] = sample.loc[0, "id"]
        with self.assertRaisesRegex(ValueError, "duplicați"):
            app.load_dataset(self.write_sample(sample))

    def test_missing_required_column_rejected(self):
        sample = self.original.head(100).drop(columns="title")
        with self.assertRaisesRegex(ValueError, "Lipsesc coloanele"):
            app.load_dataset(self.write_sample(sample))

    def test_invalid_numeric_values_rejected(self):
        for column, value in (("budget", "1.5"), ("revenue", "-1"),
                              ("popularity", "inf"), ("vote_average", "10.1")):
            sample = self.original.head(100).copy()
            sample.loc[0, column] = value
            with self.subTest(column=column), self.assertRaises(ValueError):
                app.load_dataset(self.write_sample(sample))

    def test_optional_empty_columns_and_zero_budget_preserved(self):
        sample = self.original.head(100).copy()
        sample.loc[0, "budget"] = "0"
        sample.loc[0, "homepage"] = ""
        sample.loc[0, "tagline"] = ""
        df = app.load_dataset(self.write_sample(sample))
        self.assertEqual(df.loc[0, "budget"], "0")
        self.assertEqual(df.loc[0, "homepage"], "")

    def test_dry_run_never_initializes_api_client(self):
        with patch.object(app, "RecombeeClient") as client, patch.object(app, "get_config") as config:
            self.assertEqual(app.main(["--dry-run"]), 0)
        client.assert_not_called()
        config.assert_not_called()


class ApiTests(unittest.TestCase):
    def setUp(self):
        output = contextlib.redirect_stdout(io.StringIO())
        output.__enter__()
        self.addCleanup(output.__exit__, None, None, None)

    def test_create_only_missing_properties_and_skip_native_id(self):
        client = Mock()
        client.send.return_value = [app.PROPRIETATI_CATALOG[0]]
        app.set_properties(client)
        requests = [call.args[0] for call in client.send.call_args_list]
        self.assertIsInstance(requests[0], ListItemProperties)
        self.assertEqual(len(requests[1:]), 6)
        self.assertTrue(all(isinstance(request, AddItemProperty) for request in requests[1:]))
        self.assertEqual({request.property_name for request in requests[1:]},
                         {p["name"] for p in app.PROPRIETATI_CATALOG[1:]})
        self.assertNotIn("id", {p["name"] for p in app.PROPRIETATI_CATALOG})

    def test_second_run_creates_nothing(self):
        client = Mock()
        client.send.return_value = app.PROPRIETATI_CATALOG
        app.set_properties(client)
        self.assertEqual(client.send.call_count, 1)
        self.assertIsInstance(client.send.call_args.args[0], ListItemProperties)

    def test_type_conflict_prevents_all_writes(self):
        client = Mock()
        client.send.return_value = [{"name": "vote_count", "type": "string"}]
        with self.assertRaisesRegex(ValueError, "vote_count"):
            app.set_properties(client)
        self.assertEqual(client.send.call_count, 1)

    def test_remote_verification_rejects_incomplete_schema(self):
        client = Mock()
        client.send.return_value = app.PROPRIETATI_CATALOG[:-1]
        with self.assertRaisesRegex(ValueError, "Lipsește"):
            app.verify(client)

    def test_supported_regions_use_real_sdk(self):
        for name, region in app.REGIONS.items():
            client = app.RecombeeClient("test-database", "test-token", region=region)
            self.assertEqual(client.base_uri, f"rapi-{name}.recombee.com")


if __name__ == "__main__":
    unittest.main()
