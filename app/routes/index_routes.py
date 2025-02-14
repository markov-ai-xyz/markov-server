from flask import Blueprint, render_template

index_routes = Blueprint("index_routes", __name__)


@index_routes.route("/")
@index_routes.route("/portal")
@index_routes.route("/dashboard")
@index_routes.route("/supply-knowledge")
def index():
    return render_template("index.html")


@index_routes.route("/health")
def health_check():
    return "OK", 200
