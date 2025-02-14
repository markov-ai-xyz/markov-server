from app.utils.neo4j import init_driver
from threading import Lock


class Neo4jConnectionPool:
    def __init__(self):
        self.connections = {}
        self.lock = Lock()

    def get_connection(self, uri, username, password):
        key = (uri, username, password)
        with self.lock:
            if key not in self.connections:
                driver = init_driver(uri, username, password)
                self.connections[key] = driver
            return self.connections[key]

    def close_all_connections(self):
        with self.lock:
            for driver in self.connections.values():
                driver.close()
            self.connections.clear()
