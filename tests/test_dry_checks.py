import copy
import unittest
from dry_checks import reachable, check_rewire, check_trace, GIB

def graph():
    return {"positive": {"inputs": {"text": "synthetic"}},
            "negative": {"inputs": {"text": "synthetic"}},
            "sample": {"inputs": {"positive": {"link": "positive"}, "negative": {"link": "negative"}, "cfg": 1, "bypass": True}},
            "output": {"inputs": {"image": {"link": "sample"}}}}
def trace():
    return [{"t": i*0.5, "phase": phase, "available_gib": ram, "added_swap_gib": 0,
             "swap_used_bytes": 5*GIB, "monitor_error": False}
            for i, (phase, ram) in enumerate([("start",80),("running",30),("terminated",40),("recovered",80)])]

def set_swap_delta(samples, index, delta_bytes):
    samples[index]["swap_used_bytes"] = samples[0]["swap_used_bytes"] + delta_bytes
    samples[index]["added_swap_gib"] = delta_bytes / GIB

class DryChecks(unittest.TestCase):
    def test_intended_rewire(self):
        a=graph(); b=copy.deepcopy(a); b["sample"]["inputs"]["negative"]={"link":"positive"}
        self.assertEqual(check_rewire(a,b,"sample","negative","positive",["output"])["memory_improvement"],"untested")
        self.assertIn("negative",b)
    def test_extra_change_rejected(self):
        a=graph(); b=copy.deepcopy(a); b["sample"]["inputs"].update(negative={"link":"positive"},cfg=2)
        with self.assertRaisesRegex(ValueError,"outside"): check_rewire(a,b,"sample","negative","positive",["output"])
    def test_type_only_extra_change_rejected(self):
        for key, value in (("cfg", True), ("bypass", 1), ("cfg", 1.0)):
            a = graph(); b = copy.deepcopy(a)
            b["sample"]["inputs"]["negative"] = {"link": "positive"}
            b["sample"]["inputs"][key] = value
            with self.subTest(key=key, value=value):
                with self.assertRaisesRegex(ValueError, "outside"):
                    check_rewire(a, b, "sample", "negative", "positive", ["output"])
    def test_nested_type_only_extra_change_rejected(self):
        a = graph(); a["positive"]["inputs"]["literal"] = {"layers": [1, True]}
        b = copy.deepcopy(a); b["sample"]["inputs"]["negative"] = {"link": "positive"}
        b["positive"]["inputs"]["literal"]["layers"][0] = True
        with self.assertRaisesRegex(ValueError, "outside"):
            check_rewire(a, b, "sample", "negative", "positive", ["output"])
    def test_broken_link_and_cycle(self):
        for target in ("absent","output"):
            a=graph(); a["positive"]["inputs"]["loop"]={"link":target}
            with self.assertRaises(ValueError): reachable(a,["output"])
    def test_valid_trace_is_not_visual_pass(self):
        self.assertEqual(check_trace(trace())["visual_pass"],"not_assessed")
    def test_guard_crossings(self):
        for index,key,value in [(0,"available_gib",79),(1,"available_gib",23),(1,"added_swap_gib",2.01),
                                (3,"available_gib",79),(1,"monitor_error",True),(1,"t",2)]:
            a=trace(); a[index][key]=value
            with self.assertRaises(ValueError): check_trace(a)
    def test_missing_recovery_or_termination(self):
        for a in (trace()[:-1], trace()[:2]+trace()[3:]):
            with self.assertRaises(ValueError): check_trace(a)
    def test_irrelevant_output_root_rejected(self):
        a = graph(); a["unused"] = {"inputs": {"literal": "unrelated"}}
        a["output"]["inputs"]["image"] = {"link": "unused"}
        b = copy.deepcopy(a); b["sample"]["inputs"]["negative"] = {"link": "positive"}
        with self.assertRaisesRegex(ValueError, "must be reachable"):
            check_rewire(a, b, "sample", "negative", "positive", ["output"])
    def test_positive_source_mismatch_rejected(self):
        a = graph(); a["other"] = {"inputs": {"literal": "different"}}
        a["sample"]["inputs"]["positive"] = {"link": "other"}
        a["sample"]["inputs"]["extra"] = {"link": "positive"}
        b = copy.deepcopy(a); b["sample"]["inputs"]["negative"] = {"link": "positive"}
        with self.assertRaisesRegex(ValueError, "positive link"):
            check_rewire(a, b, "sample", "negative", "positive", ["output"])
    def test_extra_pruned_dependency_rejected(self):
        a = graph(); a["extra"] = {"inputs": {"literal": "negative-only dependency"}}
        a["negative"]["inputs"]["extra"] = {"link": "extra"}
        b = copy.deepcopy(a); b["sample"]["inputs"]["negative"] = {"link": "positive"}
        with self.assertRaisesRegex(ValueError, "reachable-set"):
            check_rewire(a, b, "sample", "negative", "positive", ["output"])
    def test_other_root_keeps_negative_reachable(self):
        a = graph(); b = copy.deepcopy(a); b["sample"]["inputs"]["negative"] = {"link": "positive"}
        with self.assertRaisesRegex(ValueError, "remains reachable"):
            check_rewire(a, b, "sample", "negative", "positive", ["output", "negative"])
    def test_malformed_graph_rejected(self):
        for a, roots in (({"bad": []}, ["bad"]), ({1: {"inputs": {}}}, [1]), (graph(), "output")):
            with self.assertRaises(ValueError): reachable(a, roots)
    def test_signed_swap_delta_is_preserved(self):
        a = trace(); set_swap_delta(a, 1, -123456)
        self.assertTrue(check_trace(a)["trace_pass"])
        self.assertEqual(a[1]["added_swap_gib"], -123456 / GIB)
    def test_absolute_swap_counter_validation(self):
        for value in (-1, 1.5, True, float("nan"), float("inf"), None):
            a = trace(); a[1]["swap_used_bytes"] = value
            with self.assertRaisesRegex(ValueError, "absolute swap counter"): check_trace(a)
        a = trace(); del a[1]["swap_used_bytes"]
        with self.assertRaisesRegex(ValueError, "absolute swap counter"): check_trace(a)
    def test_swap_delta_must_match_counters(self):
        a = trace(); a[1]["added_swap_gib"] = -0.1
        with self.assertRaisesRegex(ValueError, "does not match"): check_trace(a)
        a = trace(); a[0]["added_swap_gib"] = 0.1
        with self.assertRaisesRegex(ValueError, "start swap delta"): check_trace(a)
        a = trace(); a[0]["added_swap_gib"] = 1/GIB
        with self.assertRaisesRegex(ValueError, "start swap delta"): check_trace(a)
    def test_swap_boundary_below_equal_and_above(self):
        a = trace(); set_swap_delta(a, 1, 2*GIB-1)
        self.assertTrue(check_trace(a)["trace_pass"])
        for delta in (2*GIB, 2*GIB+1):
            a = trace(); set_swap_delta(a, 1, delta)
            with self.assertRaisesRegex(ValueError, "swap guard"): check_trace(a)
    def test_rounded_display_delta_cannot_hide_threshold(self):
        a = trace(); set_swap_delta(a, 1, 2*GIB)
        a[1]["added_swap_gib"] -= 1/GIB
        with self.assertRaisesRegex(ValueError, "swap guard"): check_trace(a)
    def test_all_lifecycle_phases_enforce_swap_guard(self):
        for index in (1, 2, 3):
            a = trace(); set_swap_delta(a, index, 2*GIB)
            with self.assertRaisesRegex(ValueError, "swap guard"): check_trace(a)
    def test_nonfinite_negative_or_boolean_telemetry_rejected(self):
        for field in ("t", "available_gib", "added_swap_gib"):
            for value in (float("nan"), float("inf"), True, 10**400):
                a = trace(); a[1][field] = value
                with self.assertRaisesRegex(ValueError, "invalid telemetry"): check_trace(a)
        for field in ("t", "available_gib"):
            a = trace(); a[1][field] = -1
            with self.assertRaisesRegex(ValueError, "invalid telemetry"): check_trace(a)
    def test_missing_monitor_status_rejected(self):
        a = trace(); del a[1]["monitor_error"]
        with self.assertRaisesRegex(ValueError, "monitor error"): check_trace(a)
    def test_running_sample_required(self):
        a = trace(); del a[1]
        with self.assertRaisesRegex(ValueError, "running"): check_trace(a)
    def test_exact_ram_and_gap_boundaries(self):
        a = trace(); a[1]["available_gib"] = 24
        for i, s in enumerate(a): s["t"] = i
        self.assertTrue(check_trace(a)["trace_pass"])
    def test_timeout_rejected(self):
        a = [dict(trace()[1], t=i) for i in range(1202)]
        a[0].update(phase="start", available_gib=80)
        a[-2].update(phase="terminated")
        a[-1].update(phase="recovered", available_gib=80)
        with self.assertRaisesRegex(ValueError, "timeout"): check_trace(a)
    def test_unrepresentable_swap_delta_rejected(self):
        a = trace(); a[1]["swap_used_bytes"] = 10**400
        with self.assertRaisesRegex(ValueError, "swap delta is not finite"): check_trace(a)
