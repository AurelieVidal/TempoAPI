import connexion
from extensions import db
import os
from connexion import FlaskApp
from flask_mail import Mail
from routes import routes

# Initialize Connexion app with Flask
options = connexion.options.SwaggerUIOptions(
    swagger_ui_path="/documentation"
)

if not os.environ.get('DATABASE'):
    raise Exception("Environment variable DATABASE missing")
if not os.environ.get('MAIL_USERNAME'):
    raise Exception("Environment variable MAIL_USERNAME missing")
if not os.environ.get('MAIL_PASSWORD'):
    raise Exception("Environment variable MAIL_PASSWORD missing")

app = FlaskApp(__name__,  specification_dir='./', swagger_ui_options=options)

# Configuration of the database
app.app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE')

# Initialize extensions
db.init_app(app.app)

# Add the Swagger to the API
app.add_api('swagger.yaml')

# Blueprint for visible routes
app.app.register_blueprint(routes)

# Email configuration
if not os.environ.get('MAIL_USERNAME'):
    raise Exception("No env variable MAIL_USERNAME")
if not os.environ.get('MAIL_PASSWORD'):
    raise Exception("No env variable MAIL_PASSWORD")
app.app.config['MAIL_PORT'] = 465
app.app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.app.config['MAIL_USERNAME'] = os.environ.get("MAIL_USERNAME")
app.app.config['MAIL_PASSWORD'] = os.environ.get("MAIL_PASSWORD")
app.app.config['MAIL_USE_TLS'] = False
app.app.config['MAIL_USE_SSL'] = True
mail = Mail(app.app)

# Initialize sessions
if not os.environ.get('SESSION_SECRET_KEY'):
    raise Exception("No env variable SESSION_SECRET_KEY")
app.app.secret_key = os.environ.get("SESSION_SECRET_KEY")

# Add routes
# TODO : change : explanation of the project ?


@app.route('/')
def hello_world():
    return 'Hello World!'


# Launch the application on port 5000
if __name__ == '__main__':
    app.run(port=5000)
