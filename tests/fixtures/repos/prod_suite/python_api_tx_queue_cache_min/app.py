from fastapi import FastAPI
from django.db import transaction
from django.core.cache import cache
from tasks import some_task

app = FastAPI()

@app.post("/pay")
def pay():
    with transaction.atomic():
        cache.set("k", "v")
        cache.get("k")
        some_task.delay(1, 2)
    return {"ok": True}

