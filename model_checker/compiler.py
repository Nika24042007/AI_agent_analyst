
def compile_to_tla(model: dict, property_: dict) -> tuple[str, str]:
    tla_code = _build_tla(model, property_)
    cfg_code = _build_cfg(property_)
    return tla_code, cfg_code


def _build_tla(model: dict, property_: dict) -> str:
    lines = []
    lines.append("---- MODULE BehaviorModel ----")
    lines.append("EXTENDS Naturals, Sequences, TLC")
    lines.append("")
    
    var_names = [v["name"] for v in model["variables"]]
    lines.append(f"VARIABLES {', '.join(var_names)}")
    lines.append(f"vars == <<{', '.join(var_names)}>>")
    lines.append("")
    
    lines.append("Init ==")
    for v in model["variables"]:
        val = model["initial"][v["name"]]
        lines.append(f"  /\\ {v['name']} = {_tla_value(val, v['type'])}")
    lines.append("")
    
    for t in model["transitions"]:
        lines.append(f"{t['name']} ==")
        lines.append(f"  /\\ {_compile_expr(t['guard'])}")
        affected = {e["set"][0] for e in t["effects"]}
        for eff in t["effects"]:
            var_name, new_val = eff["set"]
            var_def = next(v for v in model["variables"] if v["name"] == var_name)
            lines.append(f"  /\\ {var_name}' = {_tla_value(new_val, var_def['type'])}")
        for v in model["variables"]:
            if v["name"] not in affected:
                lines.append(f"  /\\ {v['name']}' = {v['name']}")
        lines.append("")
    
    lines.append("Next ==")
    if model["transitions"]:
        disj = "\n  \\/ ".join(t["name"] for t in model["transitions"])
        lines.append(f"  \\/ {disj}")
    else:
        lines.append("  /\\ FALSE")
    lines.append("")
    
    lines.append("Spec == Init /\\ [][Next]_vars")
    lines.append("")
    
    lines.append(_compile_property(property_))
    lines.append("")
    lines.append("====")
    return "\n".join(lines)


def _build_cfg(property_: dict) -> str:
    lines = ["INIT Init", "NEXT Next"]
    
    if property_["type"] == "deadlock_free":
        lines.append("CHECK_DEADLOCK TRUE")
    else:
        lines.append(f"INVARIANT {property_['id']}")
        lines.append("CHECK_DEADLOCK FALSE")
    
    return "\n".join(lines)


def _compile_property(property_: dict) -> str:
    pid = property_["id"]
    ptype = property_["type"]
    expr = _compile_expr(property_.get("expression", {}))
    
    if ptype == "invariant":
        return f"{pid} == {expr}"
    if ptype == "forbidden_state":
        return f"{pid} == ~({expr})"
    if ptype == "reachable":
        return f"{pid} == ~({expr})"
    if ptype == "deadlock_free":
        return f"{pid} == ENABLED Next"
    
    raise ValueError(f"Unknown property type: {ptype}")


def _compile_expr(expr: dict) -> str:
    if not expr:
        return "TRUE"
    
    if "eq" in expr:
        var_expr, value = expr["eq"]
        return f"{var_expr['var']} = {_tla_literal(value)}"
    
    if "in" in expr:
        var_expr, values = expr["in"]
        items = ", ".join(_tla_literal(v) for v in values)
        return f"{var_expr['var']} \\in {{{items}}}"
    
    if "and" in expr:
        parts = [_compile_expr(e) for e in expr["and"]]
        return "(" + " /\\ ".join(parts) + ")"
    
    if "or" in expr:
        parts = [_compile_expr(e) for e in expr["or"]]
        return "(" + " \\/ ".join(parts) + ")"
    
    if "not" in expr:
        return f"~({_compile_expr(expr['not'])})"
    
    raise ValueError(f"Unknown expression: {expr}")


def _tla_literal(value) -> str:
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return f'"{value}"'
    return str(value)


def _tla_value(value, type_: str) -> str:
    if type_ == "boolean":
        return "TRUE" if value else "FALSE"
    return _tla_literal(value)