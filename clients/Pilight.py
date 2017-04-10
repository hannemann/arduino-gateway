#!/usr/bin/env python
# coding=utf-8

import socket
import struct
import threading
import re
import json
import time
import datetime
from config import config


class Pilight(threading.Thread):
    
    service = "urn:schemas-upnp-org:service:pilight:1"
    hasServer = False
    terminate = False
    getConfigFlag = True
    ip = None
    port = None
    sock = None
    payload = None
    alive = False
    batt = None
    temp = None
    node = None

    def __init__(self, gateway, retries=5):
        threading.Thread.__init__(self, name='pilight')
        self.retries = retries
        self.gateway = gateway
        self.discover()
    
    def discover(self):
        group = ("239.255.255.250", 1900)
        message = "\r\n".join([
            'M-SEARCH * HTTP/1.1',
            'HOST: {0}:{1}'.format(*group),
            'MAN: "ssdp:discover"',
            'ST: {st}', 'MX: 3', '', ''])
        
        self.ip = None
        self.port = None
        self.sock = None
        
        sock = self.get_udp_socket()

        for _ in range(self.retries):
            sock.sendto(message.format(st=self.service), group)
            while True:
                try:
                    response = sock.recv(1024)
                    location = re.search('Location:([0-9.]+):(.*)', str(response), re.IGNORECASE)
                    if location:
                        self.ip = location.group(1)
                        self.port = location.group(2)
                    break
                except socket.timeout:
                    break
                except socket.error as exc:
                    if _ == self.retries - 1:
                        raise PilightException(0, exc.strerror)
                    break
            time.sleep(.5)
        if self.ip is not None and self.port is not None:
            return True
        else:
            raise PilightException(0, 'No pilight instance discovered')

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket.setdefaulttimeout(0)
        self.sock.connect_ex((self.ip, int(self.port)))
        self.hasServer = True

    def identify(self):
        message = {
            "action": "identify",
            "options": {
                "receiver": 1,
                "config": 1
            }
        }
        response = self.send_message(message).get_response()
        if response is not False and 'status' in response and response["status"] == "success":
            return True
        else:
            return False

    def execute(self, payload):

        self.payload = payload

        if self.parse():
            self.connect()
            time.sleep(.1)
            if self.hasServer and self.identify():
                temp = "{}".format(self.temp)
                temp = temp.strip(chr(0))
                volts = "{:.2f}".format(float(self.batt))
                volts = volts.strip(chr(0))
		timestamp = '{:%d.%m %H:%M}'.format(datetime.datetime.now())
                message = {
                    "action": "control",
                    "code": {
                        "device": self.get_device_name_by_node(self.node),
                        "values": {
                            "label": '{} {}° {}V'.format(timestamp, temp, volts),
                            "color": "black"
                        }
                    }
                }
                print('Sending message to Pilight: {}'.format(message))
                self.send_message(message)
                self.sock.shutdown(socket.SHUT_RDWR)
                self.sock.close()
                self.sock = None

        self.hasServer = False

    def parse(self):
        if len(self.payload) > 3 and self.payload[1].find('T/') == 0:
            self.node = self.payload[0]
            self.batt = self.payload[1].split('/')[1].strip()
            self.temp = self.payload[1].split('/')[2].strip()
            return True
        return False

    def send_message(self, message):
        """
        Args:
            message (Union[str, list, dict])
        """
        if isinstance(message, list):
            message = '\n'.join(json.dumps(x) for x in message)
        else:
            message = json.dumps(message)
        try:
            self.sock.send(message + '\n')
        except socket.error as msg:
            print(msg)
            pass
        return self
    
    def get_response(self):
        text = ''
        line = ''
        while True:
            try:
                line = self.sock.recv(1024)
                text += line
            except socket.error:
                pass
            if "\n\n" in line[-2:]:
                text = text[:-2]
                break
            if self.terminate is True:
                break
        try:
            response = json.loads(text)
        except ValueError:
            return False
        
        return response
        
    @staticmethod
    def get_udp_socket():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, struct.pack('LL', 0, 10000))
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        return sock

    @staticmethod
    def get_device_name_by_node(node):
        for item in config.items('pilight_temp_nodes_map'):
            if str(item[0]) == str(node):
                return item[1]

        return False
    
    def destroy(self):
        self.terminate = True


class PilightException(Exception):

    def __init__(self, exc_id, message):
        self.id = exc_id
        self.message = message
