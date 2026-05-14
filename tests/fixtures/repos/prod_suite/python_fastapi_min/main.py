from fastapi import FastAPI
app = FastAPI()

@app.get("/hello")
def hello():
    return {"ok": True}

@app.post("/pay")
def pay():
    return {"ok": True}

# idempotent

