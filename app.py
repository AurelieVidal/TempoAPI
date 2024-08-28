from flask import Flask
from connexion import App
import connexion
from extensions import db
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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
engine = create_engine(os.environ.get('DATABASE'), echo=True)
Session = sessionmaker(bind=engine, expire_on_commit=False)

# Add the Swagger to the API
connex_app.add_api('swagger.yaml')

# TODO : put an explanation of the project ?
@app.route('/')
def hello_world():
    return 'Hello World!'

# Launch the application on port 5000
if __name__ == '__main__':
    connex_app.run(port=5000)
