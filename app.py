from flask import Flask
from connexion import FlaskApp

#app = Flask(__name__)
app = FlaskApp(__name__)

def post_greeting(name: str, greeting: str):  # Paramaeters are automatically unpacked
    return f"{greeting} {name}", 200          # Responses are automatically serialized

app.add_api("swagger.yaml")


# @app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


if __name__ == '__main__':
    app.run()
