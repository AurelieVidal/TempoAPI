from flask import Flask
import connexion
from extensions import db
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from connexion import FlaskApp

# Initialize Connexion app with Flask
options = connexion.options.SwaggerUIOptions(
    swagger_ui_path="/documentation"
)

if not os.environ.get('DATABASE'):
    raise Exception("No env variable DATABASE")

#connex_app = connexion.App(__name__, specification_dir='./', swagger_ui_options=options)
app = FlaskApp(__name__,  specification_dir='./', swagger_ui_options=options)

# Configuration of the database
if not os.environ.get('DATABASE'):
    raise Exception("No env variable DATABASE")
app.app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE')

# Initialize extensions
db.init_app(app.app)
engine = create_engine(os.environ.get('DATABASE'), echo=True)
Session = sessionmaker(bind=engine, expire_on_commit=False)

# Add the Swagger to the API
app.add_api('swagger.yaml')

# Add routes
@app.route('/')
def hello_world():
    return 'Hello World!'

# Launch the application on port 5000
if __name__ == '__main__':
    app.run(port=5000)