from fastapi import FastAPI

app = FastAPI(title="My FastAPI Application")

@app.get("/health")
def health():
    return {"status": "ok"}


 
 






if __name__ == "__main__":
    uvicorn.run('main:app',host="0.0.0.0",port=8000, reload=True)
