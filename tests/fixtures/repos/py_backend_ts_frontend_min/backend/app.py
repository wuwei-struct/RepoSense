from fastapi import FastAPI

app = FastAPI()


@app.get("/users/{id}")
def get_user(id: str):
    return {"id": id}


@app.post("/orders")
def create_order():
    return {"ok": True}
