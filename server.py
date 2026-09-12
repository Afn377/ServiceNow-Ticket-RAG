import os

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from deepseek_client import call_deepseek
from recommend import recommend
from retrieve import load_corpus, load_index, retrieve

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

corpus = load_corpus()
index = load_index()


class RecommendRequest(BaseModel):
    ticket_description: str


def verify_api_key(x_api_key: str = Header(default=None)) -> None:
    expected = os.environ.get("BACKEND_API_KEY")
    if expected and x_api_key != expected:
        raise HTTPException(status_code=401, detail="invalid or missing API key")


@app.post("/recommend", dependencies=[Depends(verify_api_key)])
def recommend_endpoint(request: RecommendRequest) -> dict:
    articles = retrieve(request.ticket_description, corpus, index)
    return recommend(request.ticket_description, articles, call_llm=call_deepseek)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8420)
