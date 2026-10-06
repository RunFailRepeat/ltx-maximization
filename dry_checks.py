"""Offline synthetic graph and telemetry checks. Never launches or monitors a model."""
import copy
import math

GUARDS = {"start_gib": 80, "floor_gib": 24, "added_swap_gib": 2,
          "timeout_s": 1200, "target_interval_s": 0.5, "max_gap_s": 1, "recovery_gib": 80}

def reachable(graph, roots):
    """Abstract graph: inputs are literals or explicit {'link': 'node-id'} objects."""
    if not isinstance(graph, dict) or not roots:
        raise ValueError("graph and roots required")
    visiting, done = set(), set()
    def visit(node):
        if node not in graph: raise ValueError("broken link")
        if node in visiting: raise ValueError("cycle")
        if node in done: return
        inputs = graph[node].get("inputs")
        if not isinstance(inputs, dict): raise ValueError("inputs required")
        visiting.add(node)
        for value in inputs.values():
            if isinstance(value, dict) and "link" in value:
                if set(value) != {"link"} or not isinstance(value["link"], str):
                    raise ValueError("invalid link")
                visit(value["link"])
        visiting.remove(node); done.add(node)
    # Validate even unreachable graph nodes, then calculate root reachability.
    for node in graph: visit(node)
    done.clear()
    for node in roots: visit(node)
    return done

def check_rewire(before, after, sampler, old_negative, positive, roots):
    reachable(before, roots)
    actual = reachable(after, roots)
    expected = copy.deepcopy(before)
    try:
        if expected[sampler]["inputs"]["negative"] != {"link": old_negative}:
            raise ValueError("unexpected original link")
        expected[sampler]["inputs"]["negative"] = {"link": positive}
    except KeyError as exc:
        raise ValueError("missing sampler input") from exc
    if expected != after: raise ValueError("changes outside intended link")
    if old_negative in actual: raise ValueError("negative encoder remains reachable")
    return {"structural_pass": True, "numerical_equivalence": "untested", "memory_improvement": "untested"}

def check_trace(samples):
    """Replay sanitized samples; this is not a live safety controller."""
    if not isinstance(samples, list) or len(samples) < 3:
        raise ValueError("start, lifecycle and recovery samples required")
    for s in samples:
        if not isinstance(s, dict) or s.get("monitor_error") is not False:
            raise ValueError("monitor error or missing status")
        for k in ("t", "available_gib", "added_swap_gib"):
            v = s.get(k)
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0:
                raise ValueError("invalid telemetry")
    if samples[0].get("phase") != "start" or samples[0]["t"] != 0 or samples[0]["available_gib"] < GUARDS["start_gib"]:
        raise ValueError("start guard")
    if samples[-1].get("phase") != "recovered" or samples[-1]["available_gib"] < GUARDS["recovery_gib"]:
        raise ValueError("recovery guard")
    phases = [s.get("phase") for s in samples]
    if "terminated" not in phases or phases.index("terminated") != len(phases)-2:
        raise ValueError("termination and final recovery required")
    if any(p != "running" for p in phases[1:-2]):
        raise ValueError("invalid lifecycle")
    for a, b in zip(samples, samples[1:]):
        if not 0 < b["t"]-a["t"] <= GUARDS["max_gap_s"]: raise ValueError("coverage gap")
    for s in samples:
        if s["available_gib"] < GUARDS["floor_gib"]: raise ValueError("available floor")
        if s["added_swap_gib"] > GUARDS["added_swap_gib"]: raise ValueError("swap guard")
        if s["t"] > GUARDS["timeout_s"]: raise ValueError("timeout")
    return {"trace_pass": True, "live_monitor_implemented": False, "visual_pass": "not_assessed",
            "identity_fidelity_pass": "not_assessed", "retry_authorized": False}
