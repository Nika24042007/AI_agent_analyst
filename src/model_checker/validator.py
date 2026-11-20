from typing import Any


def validate_model(model: dict, property_: dict) -> list[str]:
    errors: list[str] = []
    
    variables = model.get("variables", [])
    if not isinstance(variables, list):
        errors.append("'variables' must be a list")
        return errors
    
    var_names = []
    for v in variables:
        if "name" not in v:
            errors.append("Variable missing 'name'")
            continue
        var_names.append(v["name"])
        
        if v.get("type") == "enum" and not v.get("values"):
            errors.append(f"Enum variable '{v['name']}' missing 'values'")
        if v.get("type") == "integer":
            if v.get("min") is None or v.get("max") is None:
                errors.append(f"Integer variable '{v['name']}' missing min/max")
    
    if len(var_names) != len(set(var_names)):
        dupes = [n for n in var_names if var_names.count(n) > 1]
        errors.append(f"Duplicate variable names: {set(dupes)}")
    
    initial = model.get("initial", {})
    for v in variables:
        name = v.get("name")
        if name not in initial:
            errors.append(f"Missing initial value for '{name}'")
            continue
        
        val = initial[name]
        if v.get("type") == "enum" and val not in v.get("values", []):
            errors.append(f"Initial value '{val}' for '{name}' not in domain")
        if v.get("type") == "integer":
            if not (v["min"] <= val <= v["max"]):
                errors.append(f"Initial value '{val}' for '{name}' out of range")
    
    transitions = model.get("transitions", [])
    trans_names = [t.get("name") for t in transitions if "name" in t]
    if len(trans_names) != len(set(trans_names)):
        dupes = [n for n in trans_names if trans_names.count(n) > 1]
        errors.append(f"Duplicate transition names: {set(dupes)}")
    if "id" not in property_:
        errors.append("Property missing 'id'")
    if "type" not in property_:
        errors.append("Property missing 'type'")
    if property_.get("type") not in ("invariant", "forbidden_state", "reachable", "deadlock_free"):
        errors.append(f"Unknown property type: {property_.get('type')}")
    
    return errors