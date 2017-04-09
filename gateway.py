#!/usr/bin/env python

import sys
import serial.tools.list_ports
from clients.Temperature import Temperature
from clients.Valves import Valves
from clients.Pilight import Pilight
from config import config

baud_rate = 115200

clients = [
    Temperature,
    Valves,
    Pilight
]


class Gateway:

    def __init__(self):

        arduino = config.get("arduino", "serial")
        device = None
        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            if arduino == p.serial_number:
                device = p.device

        if device is None:
            print('Arduino with serial number {} not found'.format(arduino))
            sys.exit(1)

        self.ser = serial.Serial(device, baud_rate)
        self.ser.flushInput()
        self.ser.flushOutput()
        self.clients = []
        for client in clients:
            self.clients.append(client(self))

    def run(self):
        try:
            while True:
                message = self.ser.readline()
                print(message)
                payload = message.split()
                for client in self.clients:
                    client.execute(payload)

        except KeyboardInterrupt:
            for client in self.clients:
                client.destroy()

    def write(self, message):
        self.ser.write(message.encode('utf-8'))
        self.ser.write('\n'.encode('utf-8'))
        self.ser.flush()


def main():
    Gateway().run()

if __name__ == "__main__":
    main()
