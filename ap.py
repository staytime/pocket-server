



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


sensor_temp = machine.ADC(4)

def reading_chip_temperature():
    reading = sensor_temp.read_u16() * ADC_CVT_FACT
    return 27 - (reading - 0.706) / 0.001721

class JSONResponse(server.Response):
    def __init__(self, content = None, status = 200, headers={}):
        self.status = 404
        if status is not None:
            self.status = status

        self.headers = headers

        if isinstance(content, dict):
            content = json.dumps(content)
        elif isinstance(content, str):
            pass
        else:
            content = "{}"

        headers["Content-Type"] = "application/json"
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

@server.route("/about", methods=("GET", ))
def about_page(request):
    #https://github.com/staytime/pocket-server
    temperature = reading_chip_temperature()
    return f"hello! {temperature}"


@server.route("/toggle", methods=("GET", ))
@server.route("/toggle/<status>", methods=("GET", ))
def on_board_led_on(request, status = None):
    if status is None:
        led.toggle()
        time.sleep_ms(30)
        return jsonify(201, message = "OK")

    status = str(status).lower()
    if status in LED_CMD_FLAG:
        time.sleep_ms(30)
        if status == "on":
            led.on()
        else:
            led.off()

        return jsonify(201, message = "OK")
    else:
        return jsonify(201, message = "Parameter incorrect")

@server.route("/toggle-status", methods=("GET", ))
def on_board_led_off(request):
    time.sleep_ms(100)
    led.off()
    return "OK", 201

# add support for static file
@server.route("/static/<folder>/<static_file>", ("GET", ))
def serve_static_file(request, folder, static_file):
    __ = f"/static/{folder}/{static_file}"
    logging.info(f"> serve static file {__}")
    if server.file_exists(__):
        return server.serve_file(__)
    else:
        return serve_404_page(request)

server.run()
