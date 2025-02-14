from app.sql.db_config import Session
from app.sql.models import APIKey
from app.loggers.custom import logger
from werkzeug.security import generate_password_hash, check_password_hash
import secrets


def generate_api_key():
    return secrets.token_urlsafe(32)


def create_api_key(user_id):
    session = Session()
    try:
        existing_key = session.query(APIKey).filter_by(user_id=user_id).first()
        if existing_key:
            logger.error(f"API key for user_id {user_id} already exists")
            return None
        else:
            api_key = generate_api_key()
            hashed_key = generate_password_hash(api_key)
            new_api_key = APIKey(user_id=user_id, hashed_key=hashed_key)
            session.add(new_api_key)
            session.commit()
            logger.info(f"New API key created for user_id {user_id}")
            return api_key
    except Exception as e:
        logger.error(f"Error creating API key: {e}")
        session.rollback()
        return None
    finally:
        session.close()


def update_api_key(user_id):
    session = Session()
    try:
        api_key_entry = session.query(APIKey).filter_by(user_id=user_id).first()
        if api_key_entry:
            new_api_key = generate_api_key()
            api_key_entry.hashed_key = generate_password_hash(new_api_key)
            session.commit()
            logger.info(f"API key updated for user_id {user_id}")
            return new_api_key
        else:
            logger.error(f"API key for user_id {user_id} not found")
            return None
    except Exception as e:
        logger.error(f"Error updating API key: {e}")
        session.rollback()
        return None
    finally:
        session.close()


def validate_api_key(api_key):
    session = Session()
    try:
        api_key_entries = session.query(APIKey).all()
        for entry in api_key_entries:
            if check_password_hash(entry.hashed_key, api_key):
                logger.info(f"API key validation successful for user_id {entry.user_id}")
                return True
        logger.error("API key validation failed")
        return False
    except Exception as e:
        logger.error(f"Error validating API key: {e}")
        return False
    finally:
        session.close()


def get_user_id_from_api_key(api_key):
    session = Session()
    try:
        api_key_entries = session.query(APIKey).all()
        for entry in api_key_entries:
            if check_password_hash(entry.hashed_key, api_key):
                return entry.user_id
        return None
    except Exception as e:
        logger.error(f"Error getting user_id from API key: {e}")
        return None
    finally:
        session.close()
