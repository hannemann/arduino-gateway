import datetime


class Temperature:

    def __init__(self, gateway):
        self.filename = "/media/heizung/temp-sensor-test.txt"
        self.date_format = "%Y-%m-%d %H:%M:%S"
        self.target = None
        self.batt = None
        self.temp = None
        self.payload = None
        self.gateway = gateway

    def execute(self, payload):
        self.payload = payload
        if self.parse(payload):
            self.write_to_file()

    def parse(self, payload):
        if len(payload) > 3 and payload[1].find('T/') == 0:
            self.batt = payload[1].split('/')[1].strip()
            self.temp = payload[1].split('/')[2].strip()
            return True
        return False

    def write_to_file(self):
        ts = datetime.datetime.now().strftime(self.date_format)
        message = ' '.join([ts, self.batt, self.temp])
        self.target = open(self.filename, 'a+')
        self.target.write(message)
        self.target.write("\n")
        self.destroy()
        print(message)
        # self.gateway.write("DZ:21:21.03|WZ L:21:20.98")

    def destroy(self):
        if self.target is not None:
            self.target.close()
            self.target = None
        self.batt = None
        self.temp = None
