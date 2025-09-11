from typing import Protocol, Generic, TypeVar, override
import sqlite3
from pathlib import Path

PROD_DATABASE_PATH: Path = Path("models.db")

T = TypeVar('T')

class MetricStats(Generic[T]):
    def __init__(self, name: str, data: T, latency: int):
        self.name = name
        self.data = data
        self.latency = latency
    def to_sql_schema(self) -> str:
        raise NotImplementedError("Metric does not have defined SQL type")

class FloatMetric(MetricStats[float]):
    @override
    def to_sql_schema(self) -> str:
        return f"{self.name} REAL, {self.name}_latency INTEGER"

class DictMetric(MetricStats[dict[str, float]]):
    @override
    def to_sql_schema(self) -> str:
        schema: str = ""
        for key, _ in self.data.items():
            schema += (f"{self.name}_{key} REAL, ")
        schema += f"{self.name}_latency INTEGER"
        return schema



class ModelStats:
    # TODO: support modular metrics, each having its own score and latency
    def __init__(
        self,
        url: str,
        name: str,
        net_score: float,
        net_score_latency: int,
        metrics: list[MetricStats[float|dict[str, float]]]
    ):
        self.url = url
        self.name = name
        self.net_score = net_score
        self.net_score_latency = net_score_latency
        self.metrics = metrics


class DatabaseAccessor(Protocol):
    def init_database(self): ...

    def db_exists(self) -> bool: ...

    # checks whether or not a given model is in the database
    def check_entry_in_db(self) -> bool: ...

    def add_to_db(self, model: ModelStats): ...

    def get_model_statistics(self, model_url: str) -> ModelStats: ...


class SQLiteAccessor:
    def __init__(self, metric_schema: list[MetricStats[float|dict[str, float]]]):
        self.metric_schema = metric_schema
        if not self.db_exists():
            self.init_database()
        else:
            self.connection: sqlite3.Connection = sqlite3.connect(PROD_DATABASE_PATH)
            self.cursor: sqlite3.Cursor = self.connection.cursor()
    
    def __del__(self):
        self.connection.close()
    
    def db_exists(self) -> bool:
        # TODO: check that the database schema matches the currently selected metrics
        return PROD_DATABASE_PATH.exists()

    def init_database(self):
        self.connection: sqlite3.Connection = sqlite3.connect(PROD_DATABASE_PATH)
        self.cursor: sqlite3.Cursor = self.connection.cursor()

        # create the table with schema matching ModelStats, url as PRIMARY KEY
        self.cursor.execute(
            f"""
                CREATE TABLE IF NOT EXISTS models (
                    url TEXT PRIMARY KEY,
                    name TEXT,
                    net_score REAL,
                    net_score_latency INTEGER{[", " + m.to_sql_schema() for m in self.metric_schema]}
                )
            """
        )
        self.connection.commit()

    def check_entry_in_db(self, url: str) -> bool:
        self.cursor.execute("SELECT url from models WHERE url = ?", (url,))
        return self.cursor.fetchone() is not None

    def add_to_db(self, model_stats: ModelStats):
        # TODO: database schema should match modular metrics and not be hardcoded
        
        raise NotImplemented

    def get_model_statistics(self, model_url: str) -> ModelStats:
        # TODO: database schema should match modular metrics and not be hardcoded
        self.cursor.execute("SELECT * FROM models WHERE url = ?", (model_url,))
        row = self.cursor.fetchone()
        if row:
            raise NotImplemented
        else:
            raise ValueError(f"No entry found in database for URL: {model_url}")
