"""Offline synthetic graph and telemetry checks. Never launches or monitors a model."""
import copy
import math

GUARDS = {"start_gib": 80, "floor_gib": 24, "added_swap_gib": 2,
          "timeout_s": 1200, "target_interval_s": 0.5, "max_gap_s": 1, "recovery_gib": 80}
GIB = 1024 ** 3

def finite_number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False

def same_structure(a, b):
    """Compare JSON-like graph values without Python's bool/int equivalence."""
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        if any(not isinstance(k, str) for k in a) or any(not isinstance(k, str) for k in b):
            return False
        return a.keys() == b.keys() and all(same_structure(a[k], b[k]) for k in a)
    if isinstance(a, (list, tuple)):
        return len(a) == len(b) and all(same_structure(x, y) for x, y in zip(a, b))
    return a == b

def reachable(graph, roots):
    """Abstract graph: inputs are literals or explicit {'link': 'node-id'} objects."""
    if not isinstance(graph, dict) or not isinstance(roots, (list, tuple)) or not roots:
        raise ValueError("graph and roots required")
    if any(not isinstance(node, str) or not node for node in graph) or any(
            not isinstance(node, str) or not node for node in roots):
        raise ValueError("node ids must be nonempty strings")
    visiting, done = set(), set()
    def visit(node):
        if node not in graph: raise ValueError("broken link")
        if node in visiting: raise ValueError("cycle")
        if node in done: return
        if not isinstance(graph[node], dict): raise ValueError("node object required")
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
    if any(not isinstance(node, str) or not node for node in (sampler, old_negative, positive)):
        raise ValueError("rewire node ids must be nonempty strings")
    original = reachable(before, roots)
    actual = reachable(after, roots)
    if len({sampler, old_negative, positive}) != 3:
        raise ValueError("rewire nodes must differ")
    if not {sampler, old_negative, positive} <= original or not {sampler, positive} <= actual:
        raise ValueError("edited conditioning path must be reachable")
    expected = copy.deepcopy(before)
    try:
        if expected[sampler]["inputs"]["negative"] != {"link": old_negative}:
            raise ValueError("unexpected original link")
        if expected[sampler]["inputs"].get("positive") != {"link": positive}:
            raise ValueError("unexpected positive link")
        expected[sampler]["inputs"]["negative"] = {"link": positive}
    except KeyError as exc:
        raise ValueError("missing sampler input") from exc
    if not same_structure(expected, after): raise ValueError("changes outside intended link")
    if old_negative in actual: raise ValueError("negative encoder remains reachable")
    if original - actual != {old_negative} or actual - original:
        raise ValueError("unexpected reachable-set change")
    return {"structural_pass": True, "numerical_equivalence": "untested", "memory_improvement": "untested"}

def check_trace(samples):
    """Replay sanitized samples; this is not a live safety controller."""
    if not isinstance(samples, list) or len(samples) < 4:
        raise ValueError("start, running, termination and recovery samples required")
    for s in samples:
        if not isinstance(s, dict) or s.get("monitor_error") is not False:
            raise ValueError("monitor error or missing status")
        for k in ("t", "available_gib", "added_swap_gib"):
            v = s.get(k)
            if not finite_number(v):
                raise ValueError("invalid telemetry")
            if k != "added_swap_gib" and v < 0:
                raise ValueError("invalid telemetry")
        absolute_swap = s.get("swap_used_bytes")
        if isinstance(absolute_swap, bool) or not isinstance(absolute_swap, int) or absolute_swap < 0:
            raise ValueError("invalid absolute swap counter")
    baseline_swap = samples[0]["swap_used_bytes"]
    if samples[0]["added_swap_gib"] != 0:
        raise ValueError("start swap delta must be zero")
    for s in samples:
        try:
            expected_delta = (s["swap_used_bytes"] - baseline_swap) / GIB
        except OverflowError as exc:
            raise ValueError("swap delta is not finite") from exc
        if not math.isclose(s["added_swap_gib"], expected_delta, rel_tol=0, abs_tol=1 / GIB):
            raise ValueError("swap delta does not match absolute counters")
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
        # Proposed ticket contract: reaching the 2 GiB stop fails acceptance.
        # Use integer absolute counters so rounded display deltas cannot hide it.
        if s["swap_used_bytes"] - baseline_swap >= GUARDS["added_swap_gib"] * GIB:
            raise ValueError("swap guard")
        if s["t"] > GUARDS["timeout_s"]: raise ValueError("timeout")
    return {"trace_pass": True, "live_monitor_implemented": False, "visual_pass": "not_assessed",
            "identity_fidelity_pass": "not_assessed", "retry_authorized": False}
