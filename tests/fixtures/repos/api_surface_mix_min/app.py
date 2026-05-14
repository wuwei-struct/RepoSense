from fastapi import FastAPI
from flask import Flask

app = FastAPI()
web = Flask(__name__)

@app.post("/pay/{id}")
def pay(id: int):
    return {"ok": True}

@web.route("/hello")
def hello():
    return "ok"
