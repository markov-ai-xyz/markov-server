from app.sql.db_config import Session
from app.sql.models import User
from app.loggers.custom import logger


def create_user(phone, name):
    session = Session()
    try:
        user = session.query(User).filter_by(phone=phone).first()
        if user:
            logger.error(f"User with phone number {phone} already exists")
        else:
            new_user = User(phone=phone, name=name)
            session.add(new_user)
            session.commit()
            logger.info("New user created")
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        session.rollback()
    finally:
        session.close()


def read_user(phone):
    session = Session()
    try:
        user = session.query(User).filter_by(phone=phone).first()
        if user:
            logger.info(f"Retrieved user with phone number {phone}")
            return user
        else:
            logger.error(f"User with phone number {phone} not found")
            return None
    except Exception as e:
        logger.error(f"Error reading user: {e}")
    finally:
        session.close()


def update_user(phone, name=None, location=None, email=None, skills=None, tenure=None):
    session = Session()
    try:
        user = session.query(User).filter_by(phone=phone).first()
        if user:
            if name:
                user.name = name
            if location:
                user.location = location
            if email:
                user.email = email
            if skills:
                user.skills = skills
            if tenure:
                user.tenure = tenure
            session.commit()
            logger.info(f"User with phone number {phone} updated")
        else:
            logger.error(f"User with phone number {phone} not found")
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        session.rollback()
    finally:
        session.close()


def delete_user(phone):
    session = Session()
    try:
        user = session.query(User).filter_by(phone=phone).first()
        if user:
            session.delete(user)
            session.commit()
            logger.info(f"User with phone number {phone} deleted")
        else:
            logger.error(f"User with phone number {phone} not found")
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        session.rollback()
    finally:
        session.close()
