from flask import Flask, jsonify
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from config import Config
from flask_mail import Mail

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app=app)
migrate = Migrate(app=app, db=db)
mail = Mail(app)


import user_route
import country_route
