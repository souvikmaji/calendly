from flask import Flask
from db import init_db
from routes import bp as api_routes

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///calendly.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

init_db(app)
app.register_blueprint(api_routes, url_prefix='/api')

if __name__ == '__main__':
    app.run(debug=True)