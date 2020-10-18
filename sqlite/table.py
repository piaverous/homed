from typing import List
from sqlite.row import Row

class Table:
    name: str
    rows: List[Row]

    def __init__(self, name: str, rows: List[Row]):
        self.name = name
        self.rows = rows
