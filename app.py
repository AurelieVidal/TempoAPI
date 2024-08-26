from flask import Flask
from connexion import App
import connexion
from extensions import db
import os

# Initialize Connexion app with Flask
options = connexion.options.SwaggerUIOptions(
    swagger_ui_path="/documentation"
)

connex_app = App(__name__, specification_dir='./', swagger_ui_options=options)
app = connex_app.app

# Configuration of the database
if not os.environ.get('DATABASE'):
    raise Exception("No env variable DATABASE")
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE')

# Initialize extentions
db.init_app(app)

# Add the Swagger to the API
connex_app.add_api('swagger.yaml')

# Tests purposes
# TODO : put an explanation of the project ?
@app.route('/')
def hello_world():
    return 'Hello World!'

# Testing to create a route
# TODO : remove
def post_greeting(body):
    name = body.get('name')
    greeting = body.get('greeting')
    return f"{greeting} {name}", 200

# Launch the application on port 5000
if __name__ == '__main__':
    connex_app.run(port=5000)
