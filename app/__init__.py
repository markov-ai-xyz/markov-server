from flask import Flask
from flask_cors import CORS
from flask_sock import Sock

from app.routes.agent_routes import agent_routes
from app.routes.auth_routes import auth_routes
from app.routes.custom_agent_routes import custom_agent_routes
from app.routes.demo_routes import demo_routes
from app.routes.development_routes import development_routes
from app.routes.index_routes import index_routes
from app.routes.integration_routes import integration_routes
from app.routes.location_routes import location_routes
from app.routes.socket_routes import init_socket_routes
from app.routes.wa_webhook_routes import wa_webhook_routes
from app.routes.ingestion_routes import ingestion_routes
from app.routes.transformation_routes import transformation_routes
from app.loggers.custom import logger

SECRET_KEY = "markov_decision_process"


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["SECRET_KEY"] = SECRET_KEY

    CORS(app)
    sock = Sock(app)
    init_socket_routes(sock)

    app.register_blueprint(agent_routes, url_prefix="/")
    app.register_blueprint(auth_routes, url_prefix="/")
    app.register_blueprint(custom_agent_routes, url_prefix="/")
    app.register_blueprint(demo_routes, url_prefix="/")
    app.register_blueprint(development_routes, url_prefix="/")
    app.register_blueprint(index_routes, url_prefix="/")
    app.register_blueprint(ingestion_routes, url_prefix="/")
    app.register_blueprint(integration_routes, url_prefix="/")
    app.register_blueprint(location_routes, url_prefix="/")
    app.register_blueprint(transformation_routes, url_prefix="/")
    app.register_blueprint(wa_webhook_routes, url_prefix="/")

    logger.info("Registered all blueprints")
    return app
