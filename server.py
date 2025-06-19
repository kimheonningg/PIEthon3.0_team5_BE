from fastapi import FastAPI, status
from core.models.registerform import RegisterForm
from core.auth import register_user

app = FastAPI(title="PIEthon3.0", version="1.0.0")

@app.get("/server_on")
async def server_on():
    return {"server_on": True}

@app.post("/register")
async def register(user_info: RegisterForm):
    new_id = await register_user(user_info)
    return {"_id": new_id, "message": "registered"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="localhost", port=8000, reload=True)
