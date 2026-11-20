import re
from typing import Any


def parse_tlc_output(
    output: str,
    property_id: str,
    trace_data: dict | None = None,
    property_type: str = "invariant",
) -> dict[str, Any]:

    stats = _extract_stats(output)

    if re.search(r"Parsing or semantic analysis failed", output) or \
       re.search(r"Could not find or load main class", output) or \
       re.search(r"java\.lang\.\w*(Error|Exception)", output):
        return {
            "status": "ENGINE_ERROR",
            "property_id": property_id,
            "engine": "TLC",
            "message": output.strip()[:800],
        }

    if "OutOfMemoryError" in output or "State space exhausted" in output:
        return {"status": "STATE_LIMIT_REACHED", "property_id": property_id,
                "engine": "TLC", "statistics": stats}

    invariant_violated = bool(re.search(rf"Invariant {re.escape(property_id)} is violated", output))
    deadlock_reached = bool(re.search(r"Deadlock reached", output))
    completed = bool(re.search(r"Model checking complete", output))
    limit_hit = bool(re.search(r"STATE_LIMIT_EXCEEDED", output))

    if limit_hit:
        return {"status": "STATE_LIMIT_REACHED", "property_id": property_id,
                "engine": "TLC", "statistics": stats}

    if property_type == "reachable":
        if invariant_violated:
            return {
                "status": "PROPERTY_HOLDS",
                "property_id": property_id,
                "engine": "TLC",
                "statistics": stats,
                "witness": {"steps": _steps(trace_data, output)},
            }
        if completed:
            return {
                "status": "PROPERTY_VIOLATED",
                "property_id": property_id,
                "engine": "TLC",
                "message": "Target state is not reachable in the explored model",
                "statistics": stats,
            }

    if property_type == "deadlock_free":
        if deadlock_reached:
            return {
                "status": "PROPERTY_VIOLATED",
                "property_id": property_id,
                "engine": "TLC",
                "message": "Reachable state with no enabled transitions",
                "counterexample": {"steps": _steps(trace_data, output)},
            }
        if completed:
            return {"status": "PROPERTY_HOLDS", "property_id": property_id,
                    "engine": "TLC", "statistics": stats}

    if invariant_violated:
        return {
            "status": "PROPERTY_VIOLATED",
            "property_id": property_id,
            "engine": "TLC",
            "counterexample": {"steps": _steps(trace_data, output)},
        }

    if completed:
        return {"status": "PROPERTY_HOLDS", "property_id": property_id,
                "engine": "TLC", "statistics": stats}

    return {
        "status": "ENGINE_ERROR",
        "property_id": property_id,
        "engine": "TLC",
        "message": f"Unrecognized TLC output: {output.strip()[:800]}",
    }


def _steps(trace_data: dict | None, output: str) -> list[dict]:
    if trace_data:
        s = _parse_trace_from_json(trace_data)
        if s:
            return s
    return _parse_trace_text(output)


def _parse_trace_from_json(trace_data: dict) -> list[dict]:
    ce = trace_data.get("counterexample")
    if not ce:
        return []

    actions_map = {}
    for entry in ce.get("action", []):
        if isinstance(entry, list) and len(entry) == 3:
            to_state, action = entry[2], entry[1]
            if isinstance(to_state, list) and isinstance(action, dict):
                actions_map[to_state[0]] = action.get("name", "").split()[0]

    steps = []
    for entry in ce.get("state", []):
        if isinstance(entry, list) and len(entry) >= 2:
            num, state = entry[0], entry[1]
            step = {"number": num - 1, "state": state}
            if num in actions_map:
                step["transition"] = actions_map[num]
            steps.append(step)
    return steps


def _parse_trace_text(output: str) -> list[dict]:
    steps = []
    blocks = re.split(r"\nState (\d+):", output)
    i = 1
    while i < len(blocks) - 1:
        num, body = int(blocks[i]), blocks[i + 1]
        header = re.search(r"<([^>]+)>", body)
        transition = None
        if header and header.group(1).strip() not in ("Initial predicate", "Init"):
            transition = header.group(1).strip().split()[0]

        state = {}
        for line in body.splitlines():
            line = line.strip()
            if not line or line.startswith("<") or line.startswith("Back to state"):
                continue
            m = re.match(r"^(?:/\\\s*)?([a-zA-Z_]\w*)\s*=\s*(.+)$", line)
            if m:
                state[m.group(1)] = _parse_value(m.group(2).strip())

        step = {"number": num - 1, "state": state}
        if transition:
            step["transition"] = transition
        steps.append(step)
        i += 2
    return steps


def _parse_value(raw: str) -> Any:
    if raw == "TRUE":
        return True
    if raw == "FALSE":
        return False
    if raw.startswith('"') and raw.endswith('"'):
        return raw[1:-1]
    try:
        return int(raw)
    except ValueError:
        return raw


def _extract_stats(output: str) -> dict:
    return {
        "states_generated": _extract_int(output, r"([\d,]+) states generated") or 0,
        "distinct_states": _extract_int(output, r"([\d,]+) distinct states") or 0,
        "depth": _extract_int(output, r"depth of the complete state graph search is (\d+)") or 0,
    }


def _extract_int(text: str, pattern: str) -> int | None:
    m = re.search(pattern, text)
    return int(m.group(1).replace(",", "")) if m else None