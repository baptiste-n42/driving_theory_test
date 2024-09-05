import configparser
import logging

from datetime import datetime, timedelta
from flask import Flask, make_response, jsonify, render_template, redirect
from flask_jwt_extended import JWTManager

config = configparser.ConfigParser()


def create_app(*args, **kwargs):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    from . import home, exam
    try:
        config.read_file(open('./configuration.ini', "r"))
    except FileNotFoundError:
        logging.error("Configuration not found.")

    app.register_blueprint(home.bp)
    app.register_blueprint(exam.bp)
    app.config["JWT_SECRET_KEY"] = config.get("DEFAULT", "JWT_SECRET_KEY") or "secret"
    app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
    app.config["JWT_COOKIE_CSRF_PROTECT"] = False
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=7)
    jwt = JWTManager(app)

    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}

    @app.errorhandler(404)
    def not_found(e):
        return render_template("home/not_found.html"), 404

    @jwt.unauthorized_loader
    def unauthorized_loader(e):
        return redirect("/")

    @app.route("/healthcheck")
    def healthcheck():
        return make_response(jsonify({"status": "OK"}), 200)

    @app.errorhandler(Exception)
    def all_exception_handler(error):
        return make_response(jsonify({"error": f"Error : {error.args}"}), 400)

    return app
