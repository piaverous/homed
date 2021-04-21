import Adafruit_DHT
import asyncio
import logging
import os
import requests
import signal
import sys
import time 

from prometheus_client import start_http_server, Gauge
from dotenv import load_dotenv
from sqlite import SQLiteClient, Table, Row
from typing import List

load_dotenv()

temp_gauge = Gauge('temperature_living_room', 'Temperature in living room in °C')
hum_gauge = Gauge('humidity_living_room', 'Humidity in living room in %')

REFERENCE_TIMESTAMP = 1577836800
MEASUREMENT_FREQUENCY_SECONDS = 30

OPEN_WEATHER_BASE = "http://api.openweathermap.org/data/2.5/weather"
OPEN_WEATHER_URL = f"{OPEN_WEATHER_BASE}?lat={os.getenv('HOME_COORDS_LAT')}&lon={os.getenv('HOME_COORDS_LON')}&appid={os.getenv('OPENWEATHERMAP_API_KEY')}&units=metric"

home_measures = Table(
    "home_measures",
    [
        Row("id", "INTEGER PRIMARY KEY"),
        Row("deg", "INTEGER NOT NULL"), # Temperature
        Row("hum", "INTEGER NOT NULL"), # Humidity
        Row("ts", "INTEGER NOT NULL"),  # Timestamp
    ]
)

openweather_measurements = Table(
    "openweather",
    [
        Row("id", "INTEGER PRIMARY KEY"),
        Row("deg", "REAL NOT NULL"), # Temperature
        Row("hum", "INTEGER NOT NULL"), # Humidity
        Row("pre", "INTEGER NOT NULL"), # Pressure
        Row("wsp", "REAL NOT NULL"), # Wind Speed
        Row("wag", "INTEGER NOT NULL"), # Wind Angle
        Row("rai", "INTEGER NOT NULL"), # Rain (boolean 1-true or 0-false)
        Row("sno", "INTEGER NOT NULL"), # Snow (boolean 1-true or 0-false)
        Row("ts", "INTEGER NOT NULL"),  # Timestamp
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
            home_measures, 
            openweather_measurements,
        ]
        self.sensor, self.pin = Adafruit_DHT.DHT11, 4

        start_http_server(8070)
        self.initialize_sqlite_db()
        print("Done initializing !")

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


    async def start_sensor(self):
        self.running = True
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

        home_sql_query = f"INSERT INTO home_measures(deg,hum,ts) VALUES (?,?,?)"

        self.conn = SQLiteClient()
        while self.running:
            try:
                init_ts = self.get_timestamp()

                humidity, temperature = Adafruit_DHT.read_retry(
                    self.sensor, 
                    self.pin
                )

                temp_gauge.set(temperature)
                hum_gauge.set(humidity)

                ts = self.get_timestamp()
                if not humidity or not temperature:
                    print(f"Failure in measurement at ts={ts}")
                    continue

                print(f"Temp={temperature}°C | Hum={humidity}% | Dur={ts-init_ts}")

                cur = self.conn.db.cursor()
                cur.execute(home_sql_query, (temperature, humidity, ts))
                self.conn.db.commit()

                final_ts = self.get_timestamp()
                await asyncio.sleep(MEASUREMENT_FREQUENCY_SECONDS - final_ts + init_ts) # Make sure every N seconds exactly a new measurement is made
            except Exception as err:
                print(f"WARN: encountered error but continuing: {err}")
                continue
        self.conn.db.close()

    async def start_openweather_collection(self):
        self.running = True
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

        openweather_sql_query = f"INSERT INTO openweather(deg,hum,pre,wsp,wag,rai,sno,ts) VALUES (?,?,?,?,?,?,?,?)"

        self.conn = SQLiteClient()
        while self.running:
            try:
                init_ts = self.get_timestamp()
                res = requests.get(OPEN_WEATHER_URL).json()
                main_data = res["main"]

                deg, hum, pre = main_data["temp"], main_data["humidity"], main_data["pressure"]
                ts = self.get_timestamp()

                wind_info = res["wind"]
                wsp, wag = wind_info["speed"], wind_info["deg"]

                rai = 1 if "rain" in res.keys() else 0
                sno = 1 if "snow" in res.keys() else 0

                print(f"Openweather data : {deg} - {hum} - {pre} - {wsp} - {wag} - {rai} - {sno} - {ts}")

                cur = self.conn.db.cursor()
                cur.execute(openweather_sql_query, (deg,hum,pre,wsp,wag,rai,sno,ts))
                self.conn.db.commit()

                final_ts = self.get_timestamp()
                await asyncio.sleep(MEASUREMENT_FREQUENCY_SECONDS - final_ts + init_ts) # Make sure every N seconds exactly a new measurement is made
            except Exception as err:
                print(f"WARN: encountered error but continuing: {err}")
                continue
        self.conn.db.close()

if __name__ == "__main__":
    daemon = Daemon()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait([
        daemon.start_sensor(), 
        daemon.start_openweather_collection()
    ]))
    loop.close()
