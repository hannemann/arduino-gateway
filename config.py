import configparser
import os

config = configparser.ConfigParser()

for loc in os.curdir, os.path.expanduser("~/.config"), "/etc/arduino-gateway", os.environ.get("ARDUINO_GATEWAY_CONF"):
    try:
        if loc is not None:
            with open(os.path.join(loc, "config.ini")) as source:
                config.read_file(source)
    except IOError:
        pass
