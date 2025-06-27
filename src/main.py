from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def landing_page():
    return {"message": "Welcome"}


@app.get("/novels")
def get_novels():
    return {"message": "Novels"}