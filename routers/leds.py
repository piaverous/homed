from fastapi import APIRouter, Response
from typing import Dict

from utils.leds import set_color_hex, get_global_color
from utils.cache import color_cache

router = APIRouter(
    prefix="/color",
    tags=["leds","color"],
)


@router.get("/init")
def init():
    color, is_on = get_global_color()
    return {
        "color": color,
        "on": is_on,
    }

@router.post("/")
async def set_color_post(body: Dict):
    color = body["color"]
    color_cache["color"] = color
    set_color_hex(color)


@router.get("/set")
async def set_color_get(color: str = "#000000"):
    color_cache["color"] = color
    set_color_hex(color)


@router.get("/get")
async def get_color():
    color, is_on = get_global_color()
    return Response(content=color, media_type="text/plain")