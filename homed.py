import Adafruit_DHT
import asyncio
import logging
import signal
import sys
import time 

from sqlite import SQLiteClient, Table, Row
from typing import List

REFERENCE_TIMESTAMP = 1577836800

temperature_table = Table(
    "temperature",
    [
        Row("id", "INTEGER PRIMARY KEY"),
        Row("deg", "INTEGER NOT NULL"),
        Row("ts", "INTEGER NOT NULL"),
    ]
)

humidity_table = Table(
    "humidity",
    [
        Row("id", "INTEGER PRIMARY KEY"),
        Row("hum", "INTEGER NOT NULL"),
        Row("ts", "INTEGER NOT NULL"),
    ]
)


class Daemon:
    running: bool
    tables: List[Table]

    def __init__(self):
        print("Initializing daemon...")
        self.log = logging.getLogger("homed")
        self.running = False
        self.tables = [
            temperature_table, 
            humidity_table
        ]
        self.sensor, self.pin = Adafruit_DHT.DHT11, 4

        self.initialize_sqlite_db()

    def get_timestamp(self):
        return int(time.time()) - REFERENCE_TIMESTAMP

    def exit_gracefully(self, signum, frame):
        """Stop the Watcher Process properly
        """
        print("Exiting gracefully...")
        self.running = False

        time.sleep(1)
        if self.conn and self.conn.db:
            self.conn.db.close()
        sys.exit(signum)

    def initialize_sqlite_db(self):
        conn = SQLiteClient()
        for table in self.tables:
            c = conn.db.cursor()

            create_table_query = f"CREATE TABLE IF NOT EXISTS {table.name} ("
            for index, row in enumerate(table.rows):
                create_table_query += f" {row.name} {row.row_type}"
                if index < len(table.rows) - 1:
                    create_table_query += ","
            create_table_query += ")"

            c.execute(create_table_query)
        conn.db.close()


    async def start(self):
        self.running = True
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

        temp_sql_query = f"INSERT INTO temperature(deg,ts) VALUES (?,?)"
        humi_sql_query = f"INSERT INTO humidity(hum,ts) VALUES (?,?)"

        self.conn = SQLiteClient()
        while self.running:
            init_ts = self.get_timestamp()

            humidity, temperature = Adafruit_DHT.read_retry(
                self.sensor, 
                self.pin
            )
            ts = self.get_timestamp()
            if not humidity or not temperature:
                print(f"Failure in measurement at ts={ts}")
                continue

            print(f"Temp={temperature}°C | Hum={humidity}% | Dur={ts-init_ts}")

            cur = self.conn.db.cursor()
            cur.execute(temp_sql_query, (temperature, ts))
            cur.execute(humi_sql_query, (humidity, ts))
            self.conn.db.commit()

            final_ts = self.get_timestamp()
            await asyncio.sleep(30 - final_ts + init_ts) # Make sure every 5 seconds exactly a new measurement is made
        self.conn.db.close()

if __name__ == "__main__":
    daemon = Daemon()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(daemon.start())
    loop.close()
