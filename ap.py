



import network
from machine import Pin, PWM
import time
from phew import (server, \
                  connect_to_wifi, \
                  access_point, \
                  dns, \
                  logging)

from phew.template import render_template
import json



IP_ADDRESS = '192.168.4.1'
LED_QUICK_DUR = 200
AP_SSID = 'picow'
AP_PASSWORD = 'pw123456'
ADC_CVT_FACT = 3.3 / (2 ** 16 - 1)
LED_CMD_FLAG = {"on", "off"}


led = Pin("LED", Pin.OUT)
led_status = 0

sensor_temp = machine.ADC(4)

def chip_temperature():
    reading = sensor_temp.read_u16() * ADC_CVT_FACT
    return 27 - (reading - 0.706) / 0.001721

# add support for JSON
class JSONResponse(server.Response):
    def __init__(self, content = None, status = 200, headers={}):
        self.status = 404
        if status is not None:
            self.status = status

        self.headers = headers

        if isinstance(content, dict):
            content = json.dumps(content)

        # treating string as raw json
        elif isinstance(content, str):
            pass

        else:
            content = "{}"

        headers["Content-Type"] = "application/json"
        headers["Content-Length"] = len(content)

        self.body = content

def jsonify(status, **kwargs) -> JSONResponse:
    return JSONResponse(content = dict(**kwargs), status = status)

# setup wifi AP
wlan = access_point(AP_SSID, password = None)

# setup network
# detail: https://docs.micropython.org/en/latest/esp8266/tutorial/network_basics.html
wlan.ifconfig((IP_ADDRESS, '255.255.255.0', IP_ADDRESS, IP_ADDRESS))
for i in range(5):
    led.on()
    time.sleep_ms(LED_QUICK_DUR)
    led.off()
    time.sleep_ms(LED_QUICK_DUR)

while not wlan.active():
    led.on()
    time.sleep_ms(LED_QUICK_DUR)
    led.off()
    time.sleep_ms(LED_QUICK_DUR)

led.off()
led_status = 0
dns.run_catchall(IP_ADDRESS)
print('AP init sucessed')
print(wlan.ifconfig())





@server.catchall()
def serve_404_page(request):
    r = server.serve_file("/templates/404_page.html")
    r.status = 404
    return r



# for ios device
# detail:  https://stackoverflow.com/questions/50220605/ios-how-can-i-detect-that-the-current-wifi-needs-to-go-through-a-confirmation
@server.route("/hotspot-detect.html", methods = ("GET", ))
def ios_hostsport(request):
    return """
    <!DOCTYPE HTML>
    <HTML>
    <HEAD>
    <TITLE>Success</TITLE>
    </HEAD>
    <BODY>
    Success
    </BODY>
    </HTML>
    """

@server.route("/", methods=("GET", ))
def landing_page(request):
    return render_template("/templates/home.html")



@server.route("/toggle", methods=("GET", ))
def on_board_led_toggle(request):
    global led_status
    if led_status == 0:
        led_status = 1
        led.on()

    else:
        led_status = 0
        led.off()

    return jsonify(201, message = "OK", led_status = led_status)



@server.route("/toggle/<status>", methods=("GET", ))
def on_board_led_set(request, status):
    global led_status
    status = str(status).lower()
    if status in LED_CMD_FLAG:
        if status == "on":
            led.on()
            led_status = 1

        else:
            led.off()
            led_status = 0

        return jsonify(201, message = "OK", led_status = led_status)

    else:
        return jsonify(400, message = "Parameter incorrect")



@server.route("/board-status", methods=("GET", ))
def get_board_status(request):
    global led_status
    return jsonify(200, \
                   message = "OK", \
                   led_status = led_status, \
                   chip_temperature = chip_temperature())



# add support for static file
@server.route("/static/<folder>/<static_file>", ("GET", ))
def serve_static_file(request, folder, static_file):
    __ = f"/static/{folder}/{static_file}"
    # logging.info(f"> serve static file {__}")
    if server.file_exists(__):
        r = server.serve_file(__)
        r.add_header("Cache-Control", "public, max-age=604800")
        return r
    else:
        return serve_404_page(request)

server.run()
