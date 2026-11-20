import json
import asyncio

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from openai import AsyncOpenAI
from agents import Agent, Runner, set_default_openai_client, set_tracing_disabled, AgentOutputSchema
from dotenv import load_dotenv
from src.classes.response import BehavioralModel

from src.model_checker.tool import ModelCheckerTool

import httpx

load_dotenv()

from src.constants.llm_settings import MODEL, OPENAI_BASE_URL, MODEL_BUILDER_BASE_PROMPT, \
    CHECKOUT_INTERPRETER_BASE_PROMPT

# TODO убрать http_client (это для отладки)
http_client = httpx.AsyncClient(verify=False)

client = AsyncOpenAI(base_url=OPENAI_BASE_URL, http_client=http_client)
set_default_openai_client(client)
set_tracing_disabled(True)

model_builder_agent = Agent(
    name="ModelBuilder",
    instructions=MODEL_BUILDER_BASE_PROMPT,
    model=MODEL,
    output_type=AgentOutputSchema(BehavioralModel, strict_json_schema=False),
)
checkout_interpreter_agent = Agent(
    name="CheckResultInterpreter",
    instructions=CHECKOUT_INTERPRETER_BASE_PROMPT,
    model=MODEL
)

app = FastAPI(title="AI Agent Analyst")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

model_checker = ModelCheckerTool(
    tla_tools_jar="tla2tools.jar",
    timeout_sec=30,
    max_states=100000
)

class AskRequest(BaseModel):
    text: str


def model_checker_call(model) -> dict:
    if model.get("properties"):
        property_to_check = model["properties"][0]
        check = model_checker.check(model, property_to_check)
    else:
        check = {"status": "MODEL_INVALID", "message": "No properties to check"}
    return check


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/ask")
async def ask(req: AskRequest):
    try:
        result = await Runner.run(model_builder_agent, req.text)
        model_obj = result.final_output_as(BehavioralModel)

        model_dict = model_obj.model_dump(by_alias=True, exclude_none=True)
        model_json = model_obj.model_dump_json(by_alias=True, exclude_none=True, indent=2)

        model_checker_response = await asyncio.to_thread(model_checker_call, model_dict)

        interpreter_prompt = (
            f"Исходный запрос: {req.text}\n"
            f"Модель: {model_json}\n"
            f"Результат проверки: {json.dumps(model_checker_response, ensure_ascii=False)}"
        )
        checkout_interpreter_result = await Runner.run(checkout_interpreter_agent, interpreter_prompt)
        return {
            "model": model_obj.model_dump(by_alias=True, exclude_none=True),
            "interpretation": checkout_interpreter_result.final_output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при обработке запроса агентом: {str(e)}")