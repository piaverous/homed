from fastapi import APIRouter
from sqlite import SQLiteClient

router = APIRouter(
    prefix="/weather",
    tags=["weather","dht11"],
)


@router.get("/")
async def get_weather():
    conn = SQLiteClient().db
    cur = conn.cursor()

    query_temps = f"SELECT deg,id,ts FROM home_measures ORDER BY ts DESC LIMIT 1"
    cur.execute(query_temps)
    temp = cur.fetchone()
    
    query_hums = f"SELECT hum,id,ts FROM home_measures WHERE hum <= 100 ORDER BY ts DESC LIMIT 1"
    cur.execute(query_hums)
    hum = cur.fetchone()

    return {"temperature": temp[0], "humidity": hum[0] }
