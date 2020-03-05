import time

from machine import Pin, Signal, deepsleep
from micropython import const
from network import WLAN, STA_IF, STAT_CONNECTING

import uping

SERVICE_LED_PIN = const(2)
MODE_SW_PIN = const(16)
SERVICE_ADDRESS = "google.com"

SSID = const(0)
AUTH_MODE = const(4)
OPEN_AUTH_MODE = const(0)


def blink_user_led(interval, times: int = 1) -> None:
    user_led = Signal(Pin(SERVICE_LED_PIN, Pin.OUT), invert=True)
    for _ in range(times):
        user_led.on()
        time.sleep(interval)
        user_led.off()
        time.sleep(interval)


def init_wlan_station() -> WLAN:
    station = WLAN(STA_IF)
    station.active(True)
    return station


def connect_to_ap(client: WLAN, ssid) -> bool:
    client.connect(ssid)
    while client.status() is STAT_CONNECTING:
        pass
    return client.isconnected()


def ping(host) -> bool:
    try:
        result = uping.ping(host, count=4, timeout=5000, interval=10, quiet=True, size=64)
        return result[1] > 0
    except OSError:
        return False


def check_open_network(ssid, wlan: WLAN) -> bool:
    result = connect_to_ap(wlan, ssid) and ping(SERVICE_ADDRESS)
    if wlan.isconnected():
        wlan.disconnect()
    return result


def find_open_networks(wlan: WLAN):
    available_networks = wlan.scan()
    open_networks = []
    for network in available_networks:
        if network[AUTH_MODE] is not OPEN_AUTH_MODE:
            continue
        print("Checking {:s}...".format(network[SSID].decode("utf-8")))
        blink_user_led(0.3)
        if check_open_network(network[SSID], wlan):
            open_networks.append(network)
    return open_networks


def main():
    mode_sw = Pin(MODE_SW_PIN, Pin.IN)
    service_mode = mode_sw.value() == 0
    if service_mode:
        return
    station = init_wlan_station()
    open_networks = find_open_networks(station)
    station.active(False)
    if open_networks:
        print("Open wifi networks:")
        for network in open_networks:
            print(network)
        blink_user_led(1, len(open_networks))
    else:
        print("No open wifi networks found.")
    deepsleep()


if __name__ == '__main__':
    main()
