import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
MODEL = os.getenv("MODEL")

PROJECT_DIRECTORY = Path(__file__).resolve().parents[2]
PROMPTS_DIRECTORY = os.path.join(PROJECT_DIRECTORY, "prompts")

BASE_PROMPT = ""
with open(f"{PROMPTS_DIRECTORY}/base_prompt.txt", "r", encoding="utf-8") as f:
    BASE_PROMPT = f.read()


MAX_HISTORY = 10