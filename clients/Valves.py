from clients.Db import Db, sqlite3
from config import configparser, config
import sys
import subprocess


class Valves(Db):

    config_section = "openhr20"
    query_all =\
        'select * from log where id in ' \
        '(select id from log order by id desc, addr limit 200) ' \
        'group by addr order by addr;'
    payload = None
    receiver_id = None
    controller = None

    def __init__(self, gateway):
        self.gateway = gateway
        Db.__init__(self)
        self.get_controller()

    def execute(self, payload):
        self.payload = payload
        if "GET" == self.parse():
            self.gateway.write(self.fetch())
        if "SET" == self.parse():
            group = self.get_valve_control_group_name_by_addr(str(self.payload[2]))
            temp = str(self.payload[3]).strip(chr(0))
            if isinstance(group, basestring) and isinstance(temp, basestring):
                subprocess.call([self.controller, group, temp])

    def parse(self):
        if len(self.payload) > 3 and self.payload[1].find('G/V') == 0:
            self.receiver_id = self.payload[0]
            return "GET"
        if len(self.payload) > 3 and self.payload[1].find('S/V') == 0:
            self.receiver_id = self.payload[0]
            return "SET"
        return False

    def fetch(self):
        try:
            self.cursor.execute(self.query_all)

        except sqlite3.OperationalError:
            print("SQLite operational error. Database file invalid or not found")
            self.destroy()
            return "E"

        values = [
            self.receiver_id,
            "V"
        ]
        names = []
        name = ''
        for row in self.cursor:
            if row is not None:
                name = str(self.get_valve_group_name_by_addr(str(row["addr"])))
                if name not in names:
                    names.append(name)
                    res = [
                        str(row["addr"]),
                        name,
                        str(row["wanted"] / float(100)),
                        str(row["real"] / float(100))
                    ]
                    values.append('/'.join(res))

        return "|".join(values)

    def get_controller(self):
        try:
            self.controller = config.get(self.config_section, "controller")
        except configparser.NoSectionError:
            print('Section "' + self.config_section + '" not found in configuration')
            sys.exit(1)
        except configparser.NoOptionError:
            print('Option "file" not found in configuration')
            sys.exit(1)

    @staticmethod
    def get_valve_name_by_addr(addr):
        for item in config.items('valves'):
            if str(item[1]) == str(addr):
                return item[0]

        return False

    @staticmethod
    def get_valve_group_name_by_addr(addr):
        for item in config.items('valve_groups'):
            if str(addr) in str(item[1]).split(','):
                return item[0]

        return False

    @staticmethod
    def get_valve_control_group_name_by_addr(addr):
        for item in config.items('valve_control_groups'):
            if str(addr) in str(item[1]).split(','):
                return item[0]

        return False

    def destroy(self):
        self.payload = None
        self.receiver_id = None
