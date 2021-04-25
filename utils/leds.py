import pigpio

MAX_BRIGHTNESS = 255
RED_PIN, GREEN_PIN, BLUE_PIN = 17, 24, 22

pi = pigpio.pi()

def updateColor(color, step):
	color += step
	
	if color > 255:
		return 255
	if color < 0:
		return 0
	return color

def set_lights(pin, brightness):
	realBrightness = int(int(brightness) * (float(MAX_BRIGHTNESS) / 255.0))
	pi.set_PWM_dutycycle(pin, realBrightness)

def set_color_hex(color: str):
	R,G,B = tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
	set_lights(RED_PIN, R)
	set_lights(GREEN_PIN, G)
	set_lights(BLUE_PIN, B)

def get_led_color(pin):
	try:
		return int(pi.get_PWM_dutycycle(pin) * 255.0 / MAX_BRIGHTNESS)
	except Exception:
		val = int(int(0) * (float(MAX_BRIGHTNESS) / 255.0))
		pi.set_PWM_dutycycle(pin, val)
		return 0


def get_global_color():
	red = get_led_color(RED_PIN)
	green = get_led_color(GREEN_PIN)
	blue = get_led_color(BLUE_PIN)
	
	if red == 0 and green == 0 and blue == 0:
		return "#000000", False
	
	return '#%02x%02x%02x' % (red, green, blue), True