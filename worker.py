import os
import redis

from rq import Worker, Queue, Connection

listen = ['default']
redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')

conn = redis.from_url(redis_url)

if __name__ == 'main':
    with Connection(conn):
        w = Worker(list(map(Queue, listen)))
        w.work()
