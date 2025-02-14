from flask import Blueprint, send_from_directory, current_app

integration_routes = Blueprint("integration_routes", __name__)


@integration_routes.route("/js/<path:filename>")
def serve_js(filename):
    return send_from_directory(current_app.root_path + "/static/demos", filename)


@integration_routes.route("/css/<path:filename>")
def serve_css(filename):
    return send_from_directory(current_app.root_path + "/static/demos", filename)
