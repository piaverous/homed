import sqlite3

class SQLiteClient:
    def __enter__(self):
        pass
    
    def __exit__(self, exc_type, exc, tb):
        self.db.close()

    async def __aexit__(self, exc_type, exc, tb):
        self.__exit__(exc_type, exc, tb)

    async def __aenter__(self):
        self.__enter__()
    
    def __init__(self):
        self.db = sqlite3.connect('/data/storage/home.db')
