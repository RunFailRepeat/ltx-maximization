"""Compare sanitized run metadata only. No model/runtime imports or side effects."""
import json
import math
import sys
from pathlib import Path

REQUIRED_CONTEXT = {"model_revision", "workload_id", "hardware_id", "runtime_revision",
                    "wall_time_scope", "memory_metric", "memory_scope", "memory_unit"}
RUN_FIELDS = {"id", "context", "factors", "wall_seconds", "peak_memory_gb",
              "completed", "safety_passed"}

def finite_number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False

def compare(data):
    if not isinstance(data, dict) or set(data) != {"baseline", "candidate"}:
        raise ValueError("input must contain exactly baseline and candidate")
    runs = []
    for name in ("baseline", "candidate"):
        run = data.get(name)
        if not isinstance(run, dict) or not isinstance(run.get("id"), str) or not run["id"].strip():
            raise ValueError(name + " needs a nonempty id")
        if set(run) != RUN_FIELDS:
            raise ValueError(name + " missing or unsupported run fields")
        if run["completed"] is not True or run["safety_passed"] is not True:
            raise ValueError(name + " must be completed with safety passed")
        context = run.get("context")
        if not isinstance(context, dict) or not REQUIRED_CONTEXT <= context.keys():
            raise ValueError(name + " missing context")
        if any(not isinstance(k, str) or not k.strip() or
               not isinstance(v, str) or not v.strip() for k, v in context.items()):
            raise ValueError(name + " context keys and values must be nonempty strings")
        if context["memory_unit"] not in {"GB", "GiB"}:
            raise ValueError(name + " memory_unit must be GB or GiB")
        factors = run.get("factors")
        if not isinstance(factors, dict) or not factors:
            raise ValueError(name + " needs factors")
        if any(not isinstance(k, str) or not k.strip() for k in factors):
            raise ValueError(name + " factor keys must be nonempty strings")
        if any(not isinstance(v, (str, int, float, bool)) or
               isinstance(v, float) and not math.isfinite(v) for v in factors.values()):
            raise ValueError(name + " factors must be finite scalar values")
        for field in ("wall_seconds", "peak_memory_gb"):
            value = run.get(field)
            if not finite_number(value) or value <= 0:
                raise ValueError(name + " invalid " + field)
        runs.append(run)
    a, b = runs
    if a["id"] == b["id"]:
        raise ValueError("run ids must differ")
    if a["context"] != b["context"]:
        raise ValueError("context mismatch")
    if a["factors"].keys() != b["factors"].keys():
        raise ValueError("factor keys must match")
    changed = [k for k in a["factors"]
               if a["factors"][k] != b["factors"][k] or
               isinstance(a["factors"][k], bool) != isinstance(b["factors"][k], bool)]
    if len(changed) != 1:
        raise ValueError("exactly one factor must change")
    speed_ratio = a["wall_seconds"] / b["wall_seconds"]
    memory_ratio = a["peak_memory_gb"] / b["peak_memory_gb"]
    if any(not math.isfinite(v) or v <= 0 for v in (speed_ratio, memory_ratio)):
        raise ValueError("ratios must be finite and positive")
    return {"changed_factor": changed[0],
            "speed_ratio": speed_ratio,
            "memory_ratio": memory_ratio,
            "quality": "unassessed", "generalization": "not_established"}

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python compare_runs.py RUNS.json")
    try:
        result = compare(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
    except (ValueError, OSError) as exc:
        raise SystemExit(str(exc))
    print(json.dumps(result, indent=2, allow_nan=False))
