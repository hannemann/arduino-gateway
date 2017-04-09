import sqlite3
import sys
from config import configparser, config


class Db:

    conn = None
    file = None
    cursor = None
    config_section = "db"

    def __init__(self):
        self.get_file().connect().get_cursor()
    
    def connect(self):
        self.conn = sqlite3.connect(self.file)
        self.conn.row_factory = sqlite3.Row
        return self

    def get_file(self):
        try:
            self.file = config.get(self.config_section, "file")
        except configparser.NoSectionError:
            print('Section "' + self.config_section + '" not found in configuration')
            sys.exit(1)
        except configparser.NoOptionError:
            print('Option "file" not found in configuration')
            sys.exit(1)
        
        return self
    
    def get_cursor(self):
        self.cursor = self.conn.cursor()
        return self
    
    def close(self):
        self.conn.close()
        self.file = None
