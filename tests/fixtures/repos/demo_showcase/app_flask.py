from flask import Flask
app = Flask(__name__)
@app.route("/api/flask_hello")
def flask_hello():
    return "hi"
