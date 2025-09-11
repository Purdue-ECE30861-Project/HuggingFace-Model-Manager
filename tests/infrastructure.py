import unittest

from database import *


class TestDatabaseAccess(unittest.TestCase):
    def setUp(self):
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
