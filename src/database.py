from typing import Protocol
import sqlite3
from pathlib import Path

PROD_DATABASE_PATH: Path = Path("models.db")


class ModelStats:
    def __init__(
        self,
        url: str,
        name: str,
        net_score: float,
        net_score_latency: int,
        ramp_up_time: float,
        ramp_up_time_latency: int,
        bus_factor: float,
        bust_factor_latency: int,
        performance_claims: float,
        performance_claims_latency: int,
        license: float,
        license_latency: int,
        size_score: dict[str, float],
        size_score_latency: int,
        dataset_and_code_score: float,
        dataset_and_code_score_latency: int,
        dataset_quality: float,
        dataset_quality_latency: int,
        code_quality: float,
        code_quality_latency: int,
    ):
        self.url = url
        self.name = name
        self.net_score = net_score
        self.net_score_latency = net_score_latency
        self.ramp_up_time = ramp_up_time
        self.ramp_up_time_latency = ramp_up_time_latency
        self.bus_factor = bus_factor
        self.bus_factor_latency = bust_factor_latency
        self.performance_claims = performance_claims
        self.performance_claims_latency = performance_claims_latency
        self.license = license
        self.license_latency = license_latency
        self.size_score = size_score
        self.size_score_latency = size_score_latency
        self.dataset_and_code_score = dataset_and_code_score
        self.dataset_and_code_score_latency = dataset_and_code_score_latency
        self.dataset_quality = dataset_quality
        self.dataset_quality_latency = dataset_quality_latency
        self.code_quality = code_quality
        self.code_quality_latency = code_quality_latency


class DatabaseAccessor(Protocol):
    def init_database(self): ...

    def db_exists(self) -> bool: ...

    # checks whether or not a given model is in the database
    def check_entry_in_db(self) -> bool: ...

    def add_to_db(self, model: ModelStats): ...

    def get_model_statistics(self, model_url: str) -> ModelStats: ...


class SQLiteAccessor:
    def __init__(self):
        if not self.db_exists():
            self.init_database()
        else:
            self.connection: sqlite3.Connection = sqlite3.connect(PROD_DATABASE_PATH)
            self.cursor: sqlite3.Cursor = self.connection.cursor()
    
    def __del__(self):
        self.connection.close()
    
    def db_exists(self) -> bool:
        return PROD_DATABASE_PATH.exists()

    def init_database(self):
        self.connection: sqlite3.Connection = sqlite3.connect(PROD_DATABASE_PATH)
        self.cursor: sqlite3.Cursor = self.connection.cursor()

        # create the table with schema matching ModelStats, url as PRIMARY KEY
        self.cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS models (
                    url TEXT PRIMARY KEY,
                    name TEXT,
                    net_score REAL,
                    net_score_latency INTEGER,
                    ramp_up_time REAL,
                    ramp_up_time_latency INTEGER,
                    bus_factor REAL,
                    bus_factor_latency INTEGER,
                    performance_claims REAL,
                    performance_claims_latency INTEGER,
                    license REAL,
                    license_latency INTEGER,
                    size_score_raspberry_pi REAL,
                    size_score_jetson_nano REAL,
                    size_score_desktop_pc REAL,
                    size_score_aws_server REAL,
                    size_score_latency INTEGER,
                    dataset_and_code_score REAL,
                    dataset_and_code_score_latency INTEGER,
                    dataset_quality REAL,
                    dataset_quality_latency INTEGER,
                    code_quality REAL,
                    code_quality_latency INTEGER
                )
            """
        )
        self.connection.commit()

    def check_entry_in_db(self, url: str) -> bool:
        self.cursor.execute("SELECT url from models WHERE url = ?", (url,))
        return self.cursor.fetchone() is not None

    def add_to_db(self, model_stats: ModelStats):
        self.cursor.execute(
            """
                INSERT OR REPLACE INTO models (
                    url, name, net_score, net_score_latency, ramp_up_time, ramp_up_time_latency,
                    bus_factor, bus_factor_latency, performance_claims, performance_claims_latency,
                    license, license_latency,
                    size_score_raspberry_pi, size_score_jetson_nano, size_score_desktop_pc, size_score_aws_server,
                    size_score_latency,
                    dataset_and_code_score, dataset_and_code_score_latency,
                    dataset_quality, dataset_quality_latency,
                    code_quality, code_quality_latency
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                model_stats.url,
                model_stats.name,
                model_stats.net_score,
                model_stats.net_score_latency,
                model_stats.ramp_up_time,
                model_stats.ramp_up_time_latency,
                model_stats.bus_factor,
                model_stats.bus_factor_latency,
                model_stats.performance_claims,
                model_stats.performance_claims_latency,
                model_stats.license,
                model_stats.license_latency,
                model_stats.size_score.get("raspberry_pi", None),
                model_stats.size_score.get("jetson_nano", None),
                model_stats.size_score.get("desktop_pc", None),
                model_stats.size_score.get("aws_server", None),
                model_stats.size_score_latency,
                model_stats.dataset_and_code_score,
                model_stats.dataset_and_code_score_latency,
                model_stats.dataset_quality,
                model_stats.dataset_quality_latency,
                model_stats.code_quality,
                model_stats.code_quality_latency
            )
        )
        self.connection.commit()

    def get_model_statistics(self, model_url: str) -> ModelStats:
        self.cursor.execute("SELECT * FROM models WHERE url = ?", (model_url,))
        row = self.cursor.fetchone()
        if row:
            return ModelStats(
                url=row[0],
                name=row[1],
                net_score=row[2],
                net_score_latency=row[3],
                ramp_up_time=row[4],
                ramp_up_time_latency=row[5],
                bus_factor=row[6],
                bust_factor_latency=row[7],
                performance_claims=row[8],
                performance_claims_latency=row[9],
                license=row[10],
                license_latency=row[11],
                size_score={
                    "raspberry_pi": row[12],
                    "jetson_nano": row[13],
                    "desktop_pc": row[14],
                    "aws_server": row[15]
                },
                size_score_latency=row[16],
                dataset_and_code_score=row[17],
                dataset_and_code_score_latency=row[18],
                dataset_quality=row[19],
                dataset_quality_latency=row[20],
                code_quality=row[21],
                code_quality_latency=row[22]
            )
        else:
            raise ValueError(f"No entry found in database for URL: {model_url}")
