# @Unused
# TODO: Configure redis in Docker & fix IP mapping
from flask import request, jsonify
from redis import Redis

RATE_LIMIT_WINDOW = 60
MAX_REQUESTS = 10

# Define redis_client here
redis_client = Redis(host="localhost", port=6379, db=0)


def limit_remote_addr_handler():
    ip = request.remote_addr
    try:
        requests = redis_client.incr(ip)

        if requests == 1:
            redis_client.expire(ip, RATE_LIMIT_WINDOW)

        if requests > MAX_REQUESTS:
            return jsonify({"error": "Too many requests - try again later."}), 429

    except Exception as e:
        print(e)
        return jsonify({"error": "Internal server error"}), 500
