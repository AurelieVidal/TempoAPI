from flask import Flask
from connexion import App
import connexion
import os

# Initialisation de l'application Connexion avec Flask

options = connexion.options.SwaggerUIOptions(
    swagger_ui_path="/documentation"
)

connex_app = App(__name__, specification_dir='./', swagger_ui_options=options)
app = connex_app.app
if not os.environ.get('DATABASE'):
    raise Exception("No env variable DATABASE")
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE')


# Ajout de l'API via Swagger
connex_app.add_api('swagger.yaml')

# Route de test
@app.route('/')
def hello_world():
    return 'Hello World!'

# Définir la fonction pour l'endpoint /greeting
def post_greeting(body):
    name = body.get('name')
    greeting = body.get('greeting')
    return f"{greeting} {name}", 200

# Lancement de l'application
if __name__ == '__main__':
    connex_app.run(port=5000)
