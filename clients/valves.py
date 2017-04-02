from clients.db import Db, sqlite3
from config import config


class Valves(Db):

    config_section = "openhr20"
    query_all =\
        'select * from log where id in ' \
        '(select id from log order by id desc, addr limit 200) ' \
        'group by addr order by addr;'
    payload = None
    receiver_id = None

    def __init__(self, gateway):
        self.gateway = gateway
        Db.__init__(self)

    def execute(self, payload):
        self.payload = payload
        if self.parse():
            self.gateway.write(self.fetch())

    def parse(self):
        if len(self.payload) > 3 and self.payload[1].find('G/V') == 0:
            self.receiver_id = self.payload[0]
            return True
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
        for row in self.cursor:
            if row is not None:
                res = [
                    str(row["addr"]),
                    str(self.get_valve_name_by_addr(str(row["addr"]))),
                    str(row["wanted"] / float(100)),
                    str(row["real"] / float(100))
                ]
                values.append('/'.join(res))

        return "|".join(values)

    @staticmethod
    def get_valve_name_by_addr(addr):
        for item in config.items('valves'):
            if str(item[1]) == str(addr):
                return item[0]

        return False

    def destroy(self):
        self.payload = None
        self.receiver_id = None
