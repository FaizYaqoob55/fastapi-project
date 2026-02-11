from fastapi import FastAPI
from app.database import engine,Base
from app import models
import uvicorn

app = FastAPI(title="My FastAPI Application")

@app.on_event('startup')
def startup():
    Base.metadata.create_all(bind=engine)



@app.get("/health")
def health():
    return {"status": "database connected"}



if __name__ == "__main__":
    uvicorn.run('main:app',host="0.0.0.0",port=8000, reload=True)
