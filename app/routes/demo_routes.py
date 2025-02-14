from flask import Blueprint, render_template

demo_routes = Blueprint("demo_routes", __name__)


@demo_routes.route("/erekrut")
def erekrut_demo():
    return render_template("erekrut_demo.html")


@demo_routes.route("/brown-living")
def brown_living_demo():
    return render_template("brown_living_demo.html")
