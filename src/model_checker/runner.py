import os
import subprocess
import tempfile
import time
import json


def run_tlc(
    tla_code: str,
    cfg_code: str,
    tla_tools_jar: str = "tla2tools.jar",
    timeout_sec: int = 30,
    max_states: int = 100000,
) -> tuple[str, bool, int, dict | None]:
    if not os.path.exists(tla_tools_jar):
        raise FileNotFoundError(
            f"TLC not found: {tla_tools_jar}. "
        )
    
    start = time.time()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tla_path = os.path.join(tmpdir, "BehaviorModel.tla")
        cfg_path = os.path.join(tmpdir, "BehaviorModel.cfg")
        trace_json_path = os.path.join(tmpdir, "trace.json")
        
        with open(tla_path, "w", encoding="utf-8") as f:
            f.write(tla_code)
        with open(cfg_path, "w", encoding="utf-8") as f:
            f.write(cfg_code)
        
        cmd = [
            "java",
            "-cp", tla_tools_jar,
            "tlc2.TLC",
            "-config", cfg_path,
            "-workers", "1",
            "-depth", str(max_states),
            "-dumpTrace", "json", trace_json_path,
            tla_path,
        ]
        
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                cwd=tmpdir,
            )
            elapsed = int((time.time() - start) * 1000)
            
            trace_data = None
            if os.path.exists(trace_json_path):
                with open(trace_json_path, "r", encoding="utf-8") as f:
                    trace_data = json.load(f)
            
            return proc.stdout + "\n" + proc.stderr, False, elapsed, trace_data
        except subprocess.TimeoutExpired:
            elapsed = int((time.time() - start) * 1000)
            return "", True, elapsed, None
        except FileNotFoundError:
            raise RuntimeError(
                "Java not found. Установи Java 11+ и добавь в PATH."
            )