import os

import connexion
import yaml
from connexion import FlaskApp
from flask_mail import Mail

from extensions import db

# Initialize Connexion app with Flask
options = connexion.options.SwaggerUIOptions(
    swagger_ui_path="/documentation"
)

if not os.environ.get("DATABASE"):
    raise KeyError("Environment variable DATABASE missing")
if not os.environ.get("MAIL_USERNAME"):
    raise KeyError("Environment variable MAIL_USERNAME missing")
if not os.environ.get("MAIL_PASSWORD"):
    raise KeyError("Environment variable MAIL_PASSWORD missing")

app = FlaskApp(__name__, specification_dir="./", swagger_ui_options=options)

# Configuration of the database
app.app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE")

# Initialize extensions
db.init_app(app.app)

# Add the Swagger to the API
app.add_api("swagger.yaml", options={"swagger_ui": True})


def load_secure_paths(swagger_file):
    with open(swagger_file, "r", encoding="utf-8") as file:
        swagger_data = yaml.safe_load(file)

    paths = swagger_data.get("paths")
    secure_paths = set()

    for route_name, value in paths.items():
        for method, content in value.items():
            if content.get("security"):
                secure_paths.add(f"{method.upper()} {route_name}")
    return secure_paths


SECURE_PATHS = load_secure_paths("swagger.yaml")

# Email configuration
if not os.environ.get("MAIL_USERNAME"):
    raise KeyError("No env variable MAIL_USERNAME")
if not os.environ.get("MAIL_PASSWORD"):
    raise KeyError("No env variable MAIL_PASSWORD")
app.app.config["MAIL_PORT"] = 465
app.app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
app.app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
app.app.config["MAIL_USE_TLS"] = False
app.app.config["MAIL_USE_SSL"] = True
mail = Mail(app.app)

# Blueprint for visible routes
from routes import routes

app.app.register_blueprint(routes)

# Initialize sessions
if not os.environ.get("SESSION_SECRET_KEY"):
    raise KeyError("No env variable SESSION_SECRET_KEY")
app.app.secret_key = os.environ.get("SESSION_SECRET_KEY")

# Add routes
# TODO : change to an explanation of the project


@app.route("/")
def hello_world():
    return "Hello World!"


app.app.app_context().push()


# Launch the application on port 5000
if __name__ == "__main__":
    app.run(port=5000)
