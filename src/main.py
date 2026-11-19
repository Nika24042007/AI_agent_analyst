import json

from openai import AsyncOpenAI
from agents import Agent, Runner, set_default_openai_client, set_tracing_disabled, AgentOutputSchema
from dotenv import load_dotenv
from src.classes.response import BehavioralModel

import httpx

load_dotenv()

from src.constants.llm_settings import MODEL, OPENAI_BASE_URL, MODEL_BUILDER_BASE_PROMPT, CHECKOUT_INTERPRETER_BASE_PROMPT, MAX_HISTORY

#TODO убрать http_client (это для отладки)
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

def run_agent():
    print("Для выхода введите 'exit' или 'quit'.")

    history = []

    try:
        while True:
            prompt = input("User: ")
            if prompt.lower() in ("exit", "quit"):
                break

            history.append({"role": "user", "content": prompt})

            print("Агент думает...")

            result = Runner.run_sync(model_builder_agent, history)
            history = result.to_input_list()
            if len(history) > MAX_HISTORY:
                history = history[-MAX_HISTORY:]

            model_obj = result.final_output_as(BehavioralModel)
            model_json = model_obj.model_dump_json(by_alias=True, exclude_none=True, indent=2)
            print(f"Agent (Model): {model_json}\n")
            #TODO: здесь вызов ModelChecker, пока заглушка
            model_checker_response = json.loads('''{ 
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
            checkout_interpreter_result = Runner.run_sync(checkout_interpreter_agent, f"Исходный запрос: {prompt}\n Модель: {model_json}\n Результат проверки: {model_checker_response}")
            print(f"Agent (CheckResult): {checkout_interpreter_result.final_output}\n")
            print("---")


    except (EOFError, KeyboardInterrupt):
        ...


if __name__ == "__main__":
    try:
        run_agent()
    except KeyboardInterrupt:
        ...