#!/usr/bin/env python

import sys
import serial
from clients.temperature import Temperature
from clients.valves import Valves

baud_rate = 115200

clients = [
    Temperature,
    Valves
]


class Gateway:

    def __init__(self, device):
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


def main(argv):
    Gateway(argv[0]).run()

if __name__ == "__main__":
    main(sys.argv[1:])
