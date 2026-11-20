import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agents import Runner

from src.main import model_builder_agent, checkout_interpreter_agent
from src.classes.response import BehavioralModel

app = FastAPI(title="AI Agent Analyst")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

class AskRequest(BaseModel):
    text: str

def model_checker_stub() -> dict:
    """TODO: заменить на реальный вызов ModelChecker (TLC)."""
    return json.loads('''{
      "status": "PROPERTY_VIOLATED",
      "property_id": "P2",
      "engine": "TLC",
      "counterexample": {
        "steps": [
          {"number": 0, "state": {"status": "Created", "approved": false, "cancelled": false}},
          {"number": 1, "transition": "Approve", "state": {"status": "Approved", "approved": true, "cancelled": false}},
          {"number": 2, "transition": "Cancel", "state": {"status": "Cancelled", "approved": true, "cancelled": true}},
          {"number": 3, "transition": "Execute", "state": {"status": "Executed", "approved": true, "cancelled": true}}
        ]
      }
    }''')

@app.get("/api/health")
async def health():
    return {"status": "ok"}

@app.post("/api/ask")
async def ask(req: AskRequest):

    result = await Runner.run(
        model_builder_agent, [{"role": "user", "content": req.text}]
    )
    model = result.final_output_as(BehavioralModel).model_dump(
        by_alias=True, exclude_none=True
    )


    check = model_checker_stub()


    interp = await Runner.run(
        checkout_interpreter_agent,
        f"Исходный запрос: {req.text}\n"
        f"Модель: {json.dumps(model, ensure_ascii=False)}\n"
        f"Результат проверки: {check}",
    )
    return {"model": model, "interpretation": interp.final_output}
