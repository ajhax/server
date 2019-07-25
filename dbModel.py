import sqlite3


class DB:
    def __init__(self):
        self.conn = sqlite3.connect('sqlite.db', check_same_thread=False)
        self.c = self.conn.cursor()
        self.init_check()

    def init_check(self):
        self.c.execute('SELECT name from sqlite_master where type="table"')
        tables = self.c.fetchall()
        if ('machines', ) not in tables:
            print("machines table doesn't exist, Creating!")
            self.c.execute('''CREATE TABLE "machines" (
	                        "machineId"	TEXT NOT NULL, "lastConnected"	 TEXT,
	                        "os"	TEXT,   "computerName"	TEXT,
                            "username"	TEXT,   "network"	TEXT,
                            "cpu"	TEXT,   "ram"	TEXT,
	                        PRIMARY KEY("machineId"));''')
        if ('queue', ) not in tables:
            print("queue table doesn't exist, Creating!")
            self.c.execute('''CREATE TABLE "queue" (
	                        "taskId"	TEXT UNIQUE, "task"	TEXT, 
                            "machineId"	TEXT, "args"	TEXT, "isComplete"	TEXT)''')

    def close(self):
        self.conn.commit()
        self.conn.close()
