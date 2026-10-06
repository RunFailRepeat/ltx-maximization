"""Compare sanitized run metadata only. No model/runtime imports or side effects."""
import json
import math
import sys
from pathlib import Path

REQUIRED_CONTEXT = {"model_revision", "workload_id", "hardware_id", "runtime_revision"}

def compare(data):
    if not isinstance(data, dict):
        raise ValueError("input must be an object")
    runs = []
    for name in ("baseline", "candidate"):
        run = data.get(name)
        if not isinstance(run, dict) or not isinstance(run.get("id"), str) or not run["id"].strip():
            raise ValueError(name + " needs a nonempty id")
        context = run.get("context")
        if not isinstance(context, dict) or not REQUIRED_CONTEXT <= context.keys():
            raise ValueError(name + " missing context")
        if any(not isinstance(v, str) or not v.strip() for v in context.values()):
            raise ValueError(name + " context values must be nonempty strings")
        factors = run.get("factors")
        if not isinstance(factors, dict) or not factors:
            raise ValueError(name + " needs factors")
        if any(not isinstance(v, (str, int, float, bool)) or
               isinstance(v, float) and not math.isfinite(v) for v in factors.values()):
            raise ValueError(name + " factors must be finite scalar values")
        for field in ("wall_seconds", "peak_memory_gb"):
            value = run.get(field)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                raise ValueError(name + " invalid " + field)
        runs.append(run)
    a, b = runs
    if a["id"] == b["id"]:
        raise ValueError("run ids must differ")
    if a["context"] != b["context"]:
        raise ValueError("context mismatch")
    if a["factors"].keys() != b["factors"].keys():
        raise ValueError("factor keys must match")
    changed = [k for k in a["factors"] if a["factors"][k] != b["factors"][k]]
    if len(changed) != 1:
        raise ValueError("exactly one factor must change")
    return {"changed_factor": changed[0],
            "speed_ratio": a["wall_seconds"] / b["wall_seconds"],
            "memory_ratio": a["peak_memory_gb"] / b["peak_memory_gb"],
            "quality": "unassessed", "generalization": "not_established"}

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python compare_runs.py RUNS.json")
    try:
        result = compare(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
    except (ValueError, OSError) as exc:
        raise SystemExit(str(exc))
    print(json.dumps(result, indent=2, allow_nan=False))
