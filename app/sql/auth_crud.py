from app.sql.db_config import Session
from app.sql.models import Authentication
from app.loggers.custom import logger


def create_auth(username, password):
    session = Session()
    try:
        auth = session.query(Authentication).filter_by(username=username).first()
        if auth:
            logger.error(f"Authentication for username {username} already exists")
        else:
            new_auth = Authentication(username=username, password=password)
            session.add(new_auth)
            session.commit()
            logger.info("New authentication created")
    except Exception as e:
        logger.error(f"Error creating authentication: {e}")
        session.rollback()
    finally:
        session.close()


def update_auth(username, new_password):
    session = Session()
    try:
        auth = session.query(Authentication).filter_by(username=username).first()
        if auth:
            auth.password = new_password
            session.commit()
            logger.info(f"Authentication for username {username} updated")
        else:
            logger.error(f"Authentication for username {username} not found")
    except Exception as e:
        logger.error(f"Error updating authentication: {e}")
        session.rollback()
    finally:
        session.close()


def validate_auth(username, password):
    session = Session()
    try:
        auth = session.query(Authentication).filter_by(username=username).first()
        if auth and auth.password == password:
            logger.info(f"Authentication successful for username {username}")
            return True
        else:
            logger.error(f"Authentication failed for username {username}")
            return False
    except Exception as e:
        logger.error(f"Error validating authentication: {e}")
        return False
    finally:
        session.close()
