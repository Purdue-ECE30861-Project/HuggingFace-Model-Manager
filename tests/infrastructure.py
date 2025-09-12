import unittest
import os

from database import *


class TestDatabaseAccess(unittest.TestCase):
    def setUp(self):
        self.test_db = Path("test.db")
        self.maxDiff = None
        # normal schema
        self.schema1: list[FloatMetric | DictMetric] = [
            FloatMetric("size", 0.3, 10),
            FloatMetric("setup", 0.2, 30),
            DictMetric("compatibility", {"windows": 0.5, "mac": 0.2, "linux": 0.8}, 29),
        ]
        self.schema2: list[FloatMetric | DictMetric] = [
            FloatMetric("size", 0.3, 10),
            FloatMetric("setup", 0.2, 30),
            FloatMetric("speed", 0.7, 49),
            FloatMetric("accuracy", 0.1, 10),
            FloatMetric("setup", 0.2, 30),
            DictMetric("compatibility", {"windows": 0.5, "mac": 0.2, "linux": 0.8}, 29),
            FloatMetric("team_size", 0.9, 9),
            FloatMetric("team_balance", 0.6, 41),
            FloatMetric("funding", 0.8, 1000),
            FloatMetric("compliance", 0.1, 943),
            FloatMetric("license", 0.5, 234),
        ]
        self.schema3: list[FloatMetric | DictMetric] = [
            DictMetric(
                "size", {"raspberry_pi": 0.5, "desktop_pc": 0.7, "aws_server": 1.0}, 54
            ),
            DictMetric("compatibility", {"windows": 0.5, "mac": 0.2, "linux": 0.8}, 29),
            DictMetric(
                "documentation",
                {"english": 0.9, "spanish": 0.5, "french": 0.2, "mandarin": 0.0},
                1094,
            ),
            DictMetric("license", {"distribution": 1.0, "modification": 0.3}, 297),
            FloatMetric("setup", 0.2, 30),
            FloatMetric("speed", 0.7, 49),
            FloatMetric("accuracy", 0.1, 10),
            FloatMetric("setup", 0.2, 30),
            DictMetric("database", {"size": 0.2, "quality": 0.9}, 964),
            FloatMetric("team_size", 0.9, 9),
        ]

        # edge cases

        self.schema0: list[FloatMetric | DictMetric] = []
        self.schema_weird_names: list[FloatMetric | DictMetric] = [
            FloatMetric("valid sql header, actually", 0.3, 11),
            DictMetric(
                "this one too",
                {
                    "and this": 0.0,
                    "and that": 1.0,
                    "and this again": 0.5,
                    "fourth one": 0.1,
                },
                3939,
            ),
        ]

    # database initialization
    def testCreateNewDatabase(self):

        accessor = SQLiteAccessor(None, self.schema1)
        accessor.cursor.execute("PRAGMA table_info(models)")
        columns = {row[1]: row[2] for row in accessor.cursor.fetchall()}

        self.assertDictEqual(
            columns,
            {
                "url": "TEXT",
                "name": "TEXT",
                "net_score": "REAL",
                "net_score_latency": "INTEGER",
                "size": "REAL",
                "size_latency": "INTEGER",
                "setup": "REAL",
                "setup_latency": "INTEGER",
                "compatibility_windows": "REAL",
                "compatibility_mac": "REAL",
                "compatibility_linux": "REAL",
                "compatibility_latency": "INTEGER",
            },
        )

    def test_add_and_get_model(self):
        accessor = SQLiteAccessor(None, self.schema1)
        model = ModelStats(
            url="test_url",
            name="Test Model",
            net_score=0.99,
            net_score_latency=5,
            metrics=[
                FloatMetric("size", 0.3, 10),
                FloatMetric("setup", 0.2, 30),
                DictMetric(
                    "compatibility", {"windows": 0.5, "mac": 0.2, "linux": 0.8}, 29
                ),
            ],
        )
        accessor.add_to_db(model)
        fetched = accessor.get_model_statistics("test_url")
        self.assertEqual(fetched.url, model.url)
        self.assertEqual(fetched.name, model.name)
        self.assertEqual(fetched.net_score, model.net_score)
        self.assertEqual(fetched.net_score_latency, model.net_score_latency)
        # Check metrics
        for m1, m2 in zip(model.metrics, fetched.metrics):
            self.assertEqual(m1.name, m2.name)
            self.assertEqual(m1.latency, m2.latency)
            self.assertEqual(m1.data, m2.data)

    def test_check_entry_in_db(self):
        accessor = SQLiteAccessor(None, self.schema1)
        model = ModelStats(
            url="test_url2",
            name="Test Model 2",
            net_score=0.88,
            net_score_latency=7,
            metrics=[
                FloatMetric("size", 0.4, 12),
                FloatMetric("setup", 0.3, 32),
                DictMetric(
                    "compatibility", {"windows": 0.6, "mac": 0.3, "linux": 0.9}, 31
                ),
            ],
        )
        accessor.add_to_db(model)
        self.assertTrue(accessor.check_entry_in_db("test_url2"))
        self.assertFalse(accessor.check_entry_in_db("nonexistent_url"))

    def test_db_exists_schema_match(self):
        accessor = SQLiteAccessor(None, self.schema1)
        self.assertTrue(accessor.db_exists())

    def test_empty_schema(self):
        accessor = SQLiteAccessor(None, self.schema0)
        model = ModelStats(
            url="empty_url",
            name="Empty Model",
            net_score=0.0,
            net_score_latency=0,
            metrics=[],
        )
        accessor.add_to_db(model)
        fetched = accessor.get_model_statistics("empty_url")
        self.assertEqual(fetched.url, model.url)
        self.assertEqual(fetched.metrics, [])

    def test_weird_names_schema(self):
        accessor = SQLiteAccessor(None, self.schema_weird_names)
        model = ModelStats(
            url="weird_url",
            name="Weird Model",
            net_score=0.5,
            net_score_latency=1,
            metrics=self.schema_weird_names,
        )
        accessor.add_to_db(model)
        fetched = accessor.get_model_statistics("weird_url")
        self.assertEqual(fetched.url, model.url)
        self.assertEqual(fetched.name, model.name)
        self.assertEqual(fetched.net_score, model.net_score)
        self.assertEqual(fetched.net_score_latency, model.net_score_latency)
        for m1, m2 in zip(model.metrics, fetched.metrics):
            self.assertEqual(m1.name, m2.name)
            self.assertEqual(m1.latency, m2.latency)
            self.assertEqual(m1.data, m2.data)
    
    def test_get_nonexistent_model(self):
        accessor = SQLiteAccessor(None, self.schema1)
        model = ModelStats(
            url="test_url2",
            name="Test Model 2",
            net_score=0.88,
            net_score_latency=7,
            metrics=[
                FloatMetric("size", 0.4, 12),
                FloatMetric("setup", 0.3, 32),
                DictMetric(
                    "compatibility", {"windows": 0.6, "mac": 0.3, "linux": 0.9}, 31
                ),
            ],
        )
        accessor.add_to_db(model)
        # test for panics
        accessor.get_model_statistics("test_url2")
        with self.assertRaises(ValueError):
            accessor.get_model_statistics("nonexistent_url")
    
    def test_wrong_schema(self):
        
        accessor = SQLiteAccessor(self.test_db, self.schema1)
        del accessor
        
        accessor_2 = SQLiteAccessor(self.test_db, self.schema3, create_if_missing=False)
        self.assertFalse(accessor_2.db_exists())
        del accessor_2
        os.remove(self.test_db)
    
    def test_add_with_wrong_schema(self):
        accessor = SQLiteAccessor(None, self.schema1)
        model1 = ModelStats("example.com/correct", "Correct", 0.2, 1225, self.schema1)
        model2 = ModelStats("example.com/incorrect", "Incorrect", 0.2, 1225, self.schema2)
        accessor.add_to_db(model1)
        with self.assertRaises(ValueError):
            accessor.add_to_db(model2)
    
    def test_uninitialized_db(self):
        accessor = SQLiteAccessor(None, self.schema1, create_if_missing=False)
        self.assertFalse(accessor.db_exists())
