from typing import Protocol

class DatabaseAccessor(Protocol):
    def init_database(self):
        ...
    
    def db_exists(self) -> bool:
        ...
    
    # checks whether or not a given model is in the database
    def check_entry_in_db(self) -> bool:
        ...
    
    def add_to_db(self):
        ...
    


class SQLiteAccessor:
    def __init__(self):
        if not self.db_exists():
            self.init_database()
    
    def db_exists(self):
        pass
    
    def init_database(self):
        pass

    def check_entry_in_db(self) -> bool:
        ...

    def add_to_db(self):
        pass

