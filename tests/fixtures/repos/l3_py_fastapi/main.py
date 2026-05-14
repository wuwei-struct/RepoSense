from fastapi import FastAPI, APIRouter
import threading
import asyncio
app = FastAPI()
router = APIRouter()
@app.get("/ping")
def ping():
    return {"ok": True}
@router.post('/items')
def items():
    return {"ok": True}
def locks():
    L1 = threading.Lock()
    L2 = asyncio.Lock()
