import os
import json
from model_checker import ModelCheckerTool

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


JAR_PATH = os.path.join(BASE_DIR, "tla2tools.jar")
JSON_PATH = os.path.join(BASE_DIR, "test_input.json")

with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

tool = ModelCheckerTool(
    tla_tools_jar=JAR_PATH,
    timeout_sec=30,
    max_states=100000,
)

result = tool.check(data["model"], data["property"])

print(json.dumps(result, indent=2, ensure_ascii=False))