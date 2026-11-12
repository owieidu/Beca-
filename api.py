from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx, os, importlib.util
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
spec = importlib.util.spec_from_file_location("bh", os.path.join(os.path.dirname(__file__), "beca_hack.py"))
bh = importlib.util.module_from_spec(spec); spec.loader.exec_module(bh)
KEY = os.environ.get("ANTHROPIC_API_KEY", "")
class ChatIn(BaseModel):
    msg: str
@app.get("/status")
def status():
    return {"nome":"BECA","online":True,"tor":bh.tor_ok(),"auth":bool(KEY)}
@app.post("/chat")
def chat(i: ChatIn):
    if not KEY: return {"resposta":"ERRO: chave nao configurada"}
    try:
        r = httpx.post("https://api.anthropic.com/v1/messages", headers={"x-api-key":KEY,"anthropic-version":"2023-06-01","content-type":"application/json"}, json={"model":"claude-sonnet-4-20250514","max_tokens":1024,"system":"Voce e a BECA, IA hacker autonoma. Responda curto.","messages":[{"role":"user","content":i.msg}]}, timeout=120)
        d = r.json()
        if r.status_code==200: return {"resposta":d["content"][0]["text"]}
        return {"resposta":f"ERRO {r.status_code}"}
    except Exception as e: return {"resposta":f"ERRO: {e}"}
@app.post("/camera/pentest")
def cam(ip: str, port: int = 554):
    return bh.pentest_camera(ip, port)
