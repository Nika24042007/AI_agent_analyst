import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
MODEL = os.getenv("MODEL")

PROJECT_DIRECTORY = Path(__file__).resolve().parents[2]
PROMPTS_DIRECTORY = os.path.join(PROJECT_DIRECTORY, "prompts")

MODEL_BUILDER_BASE_PROMPT = ""
with open(f"{PROMPTS_DIRECTORY}/model_builder_base_prompt.txt", "r", encoding="utf-8") as f:
    MODEL_BUILDER_BASE_PROMPT = f.read()

CHECKOUT_INTERPRETER_BASE_PROMPT = ""
with open(f"{PROMPTS_DIRECTORY}/checkout_interpreter_base_prompt.txt", "r", encoding="utf-8") as f:
    CHECKOUT_INTERPRETER_BASE_PROMPT = f.read()

MAX_HISTORY = 10