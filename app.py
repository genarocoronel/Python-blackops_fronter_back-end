# Importing libraries for use
# Importing flask
from flask import Flask
# Importing requests
import requests
# Importing JSON
import json

# Setting up the flask
app = Flask("EvE ERB API")


@app.route('/')
def init_route():
    print("{'error': 'Page not found'}");

if __name__ == '__main__':
    app.run()

