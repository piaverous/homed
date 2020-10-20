import asyncio
import logging
import platform
from typing import Dict
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from pprint import pprint
from utils import set_color_hex, get_global_color
from sqlite import SQLiteClient

if platform.system() == "Linux":
    from homed import Daemon

templates = Jinja2Templates(directory="templates")

app = FastAPI()
app.logger = logging.getLogger("uvicorn")

app.mount("/dist", StaticFiles(directory="templates/dist"), name="dist")


@app.on_event("startup")
async def startup_event():
    if platform.system() == "Linux":
        homed = Daemon()
        loop = asyncio.get_event_loop()
        loop.create_task(homed.start())
    else:
        print(f"Unexpected platform {platform.system()}. Did not launch homed daemon.")

@app.get("/on")
def on():
    set_color_hex('#ffffff')
    return {"status": "ON"}


@app.get("/off")
def off():    
    set_color_hex('#000000')
    return {"status": "OFF"}


@app.get("/", response_class=HTMLResponse)
async def render(request: Request):
    color, is_on = get_global_color()
    is_checked = "checked" if is_on else ""
    return templates.TemplateResponse(
        "item.html", 
        {
            "request": request, 
            "color": color, 
            "is_on": is_on, 
            "is_checked": is_checked
        }
    )

@app.get("/graphs", response_class=HTMLResponse)
async def grnder_graphs(request: Request):
    return templates.TemplateResponse(
        "graphs.html", 
        {
            "request": request, 
            "data": get_all_temps()
        }
    )


@app.get("/init")
def init():
    color, is_on = get_global_color()
    return {
        "color": color,
        "on": is_on,
    }

@app.get("/data")
def get_all_temps():
    conn = SQLiteClient().db
    cur = conn.cursor()

    from_date = 0
    query_temps = f"SELECT * FROM temperature WHERE ts > {from_date} ORDER BY ts"
    cur.execute(query_temps)
    temps = cur.fetchall()
    
    query_hums = f"SELECT * FROM humidity WHERE ts > {from_date} AND hum <= 100 ORDER BY ts"
    cur.execute(query_hums)
    hums = cur.fetchall()

    return {"temperature": temps, "humidity": hums}


@app.post("/color/")
async def create_item(body: Dict):
    set_color_hex(body["color"])
