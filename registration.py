"""Chapel Hill Public Library Patron Self-Registration"""
__author__ = "Jeremy Nelson"

import csv
from flask import Flask, request, jsonify 

app = Flask(__name__)


@app.route("/", methods=["POST"])
def index():
    """Default view for handling post submissions from a posted form"""
    if not request.method.startswith("POST"):
        return "Method not support"
    

if __name__ == '__main__':
    print("Starting Chapel Hills Patron Registration")
    app.run(debug=True)
