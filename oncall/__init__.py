from flask import Flask
from oncall.calendar import calendar


app = Flask(__name__)
app.register_blueprint(calendar)
