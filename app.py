# Importing libraries for use
# Importing flask
from flask import Flask
# Importing requests
import requests
# Importing JSON
import json

# Setting up the flask
app = Flask("LendingServe - Back End System")


@app.route('/')
def init_route():
    print("{'error': 'Page not found'}");

if __name__ == '__main__':
    app.run(host= '0.0.0.0')

