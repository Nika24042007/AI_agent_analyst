from typing import Any
from .validator import validate_model
from .compiler import compile_to_tla
from .runner import run_tlc
from .parser import parse_tlc_output


class ModelCheckerTool:
    def __init__(
        self,
        tla_tools_jar: str = "tla2tools.jar",
        timeout_sec: int = 30,
        max_states: int = 100000,
    ):
        self.tla_tools_jar = tla_tools_jar
        self.timeout_sec = timeout_sec
        self.max_states = max_states
    
    def check(self, model: dict[str, Any], property_: dict[str, Any]) -> dict[str, Any]:
        property_id = property_.get("id", "unknown")
        
        validation_errors = validate_model(model, property_)
        if validation_errors:
            return {
                "status": "MODEL_INVALID",
                "property_id": property_id,
                "engine": "TLC",
                "errors": validation_errors,
            }
        
        try:
            tla_code, cfg_code = compile_to_tla(model, property_)
        except Exception as e:
            return {
                "status": "ENGINE_ERROR",
                "property_id": property_id,
                "engine": "TLC",
                "message": f"Compilation failed: {e}",
            }
        
        try:
            # Теперь получаем 4 значения, включая trace_data
            tlc_output, timed_out, elapsed_ms, trace_data = run_tlc(
                tla_code, cfg_code,
                tla_tools_jar=self.tla_tools_jar,
                timeout_sec=self.timeout_sec,
                max_states=self.max_states,
            )
        except Exception as e:
            return {
                "status": "ENGINE_ERROR",
                "property_id": property_id,
                "engine": "TLC",
                "message": f"TLC launch failed: {e}",
            }
        
        if timed_out:
            return {
                "status": "TIMEOUT",
                "property_id": property_id,
                "engine": "TLC",
                "message": f"TLC exceeded {self.timeout_sec}s timeout",
            }

        return parse_tlc_output(
            tlc_output,
            property_id,
            trace_data,
            property_type=property_.get("type", "invariant"),
        )