import asyncio
import logging
import platform
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from routers import leds, weather
from utils.leds import get_global_color

if platform.system() == "Linux":
    from homed import Daemon

templates = Jinja2Templates(directory="templates")

app = FastAPI()
app.logger = logging.getLogger("uvicorn")

app.include_router(leds.router)
app.include_router(weather.router)


@app.on_event("startup")
async def startup_event():
    if platform.system() == "Linux":
        homed = Daemon()
        loop = asyncio.get_event_loop()
        loop.create_task(homed.start_sensor())
        loop.create_task(homed.start_openweather_collection())
    else:
        print(f"Unexpected platform {platform.system()}. Did not launch homed daemon.")


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
