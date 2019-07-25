import uuid
from threading import Lock

lock = Lock()


class Queue:
    def __init__(self, db):
        self.db = db

    def insert(self, task, machine_id, args=[]):
        task_id = str(uuid.uuid4()).replace('-', '')
        lock.acquire(True)
        self.db.c.execute('SELECT * from queue WHERE taskId=?', (task_id, ))
        while len(self.db.c.fetchall()) != 0:
            task_id = str(uuid.uuid4()).replace('-', '')
            self.db.c.execute(
                'SELECT * from queue WHERE taskId=?', (task_id, ))
        self.db.c.execute("INSERT INTO queue VALUES (?,?,?,?,?)",
                          (task_id, task, machine_id, str(args), "false"))
        self.db.conn.commit()
        lock.release()
        return task_id


if __name__ == "__main__":
    from dbModel import DB
    queue = Queue(DB())
    queue.insert("msg", "123123")
