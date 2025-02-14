from neo4j import GraphDatabase


def init_driver(uri, user, password):
    return GraphDatabase.driver(uri, auth=(user, password))


def close_driver(driver):
    driver.close()


def execute_read(driver, func, *args):
    with driver.session() as session:
        return session.execute_read(func, *args)


def execute_write(driver, func, *args):
    with driver.session() as session:
        return session.execute_write(func, *args)
