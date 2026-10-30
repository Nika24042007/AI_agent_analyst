from openai import AsyncOpenAI
from agents import Agent, Runner, set_default_openai_client, set_tracing_disabled, AgentOutputSchema
from dotenv import load_dotenv
from src.classes.response import BehavioralModel

import httpx

load_dotenv()

from src.constants.llm_settings import MODEL, OPENAI_BASE_URL, BASE_PROMPT, MAX_HISTORY

#TODO убрать http_client (это для отладки)
http_client = httpx.AsyncClient(verify=False)

client = AsyncOpenAI(base_url=OPENAI_BASE_URL, http_client=http_client)
set_default_openai_client(client)
set_tracing_disabled(True)

agent = Agent(
    name="Pro Assistant",
    instructions=BASE_PROMPT,
    model=MODEL,
    output_type=AgentOutputSchema(BehavioralModel, strict_json_schema=False),
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

            result = Runner.run_sync(agent, history)
            history = result.to_input_list()
            if len(history) > MAX_HISTORY:
                history = history[-MAX_HISTORY:]

            model_obj = result.final_output_as(BehavioralModel)
            print(f"Agent: {model_obj.model_dump_json(by_alias=True, exclude_none=True, indent=2)}\n")
            print("---")


    except (EOFError, KeyboardInterrupt):
        ...


if __name__ == "__main__":
    try:
        run_agent()
    except KeyboardInterrupt:
        ...