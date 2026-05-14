from flask import Flask
app = Flask(__name__)

@app.route("/hello")
def hello():
    return "ok"

@app.route("/pay", methods=["POST"])
def pay():
    return "ok"
