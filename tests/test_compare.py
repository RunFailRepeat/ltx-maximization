import copy
import unittest
from compare_runs import compare

def fixture():
    a = {"id": "synthetic-a",
         "context": {"model_revision": "synthetic-model-v1", "workload_id": "synthetic-scene",
                     "hardware_id": "synthetic-device", "runtime_revision": "synthetic-runtime-v1",
                     "wall_time_scope": "prompt execution through completed output",
                     "memory_metric": "peak resident memory", "memory_scope": "isolated process",
                     "memory_unit": "GiB"},
         "completed": True, "safety_passed": True,
         "factors": {"mode": "a"}, "wall_seconds": 20, "peak_memory_gb": 8}
    b = copy.deepcopy(a)
    b.update(id="synthetic-b", factors={"mode": "b"}, wall_seconds=10, peak_memory_gb=4)
    return {"baseline": a, "candidate": b}

class CompareChecks(unittest.TestCase):
    def test_ratios_do_not_claim_quality(self):
        r = compare(fixture())
        self.assertEqual((r["speed_ratio"], r["memory_ratio"], r["quality"]), (2, 2, "unassessed"))
    def test_context_mismatch(self):
        d = fixture(); d["candidate"]["context"]["hardware_id"] = "different"
        with self.assertRaisesRegex(ValueError, "context mismatch"): compare(d)
    def test_zero_or_nonfinite(self):
        for v in (0, -1, float("nan"), float("inf"), True, 10**400):
            d = fixture(); d["candidate"]["wall_seconds"] = v
            with self.assertRaises(ValueError): compare(d)
    def test_two_changes(self):
        d = fixture(); d["baseline"]["factors"]["steps"] = 8; d["candidate"]["factors"]["steps"] = 4
        with self.assertRaisesRegex(ValueError, "exactly one"): compare(d)
    def test_no_change(self):
        d = fixture(); d["candidate"]["factors"] = {"mode": "a"}
        with self.assertRaisesRegex(ValueError, "exactly one"): compare(d)
    def test_missing_context(self):
        d = fixture(); del d["baseline"]["context"]["model_revision"]
        with self.assertRaisesRegex(ValueError, "missing context"): compare(d)
    def test_completion_and_safety_must_be_true(self):
        for field in ("completed", "safety_passed"):
            for value in (False, None, 0, 1, "true"):
                with self.subTest(field=field, value=value):
                    d = fixture(); d["candidate"][field] = value
                    with self.assertRaisesRegex(ValueError, "completed with safety passed"): compare(d)
    def test_missing_completion_or_safety_rejected(self):
        for field in ("completed", "safety_passed"):
            d = fixture(); del d["candidate"][field]
            with self.assertRaisesRegex(ValueError, "run fields"): compare(d)
    def test_measurement_definitions_required(self):
        for field in ("wall_time_scope", "memory_metric", "memory_scope", "memory_unit"):
            d = fixture(); del d["candidate"]["context"][field]
            with self.assertRaisesRegex(ValueError, "missing context"): compare(d)
    def test_mismatched_measurement_definitions_rejected(self):
        for field, value in (("wall_time_scope", "through early termination"),
                             ("memory_metric", "allocated memory"),
                             ("memory_scope", "whole system"), ("memory_unit", "GB")):
            d = fixture(); d["candidate"]["context"][field] = value
            with self.assertRaisesRegex(ValueError, "context mismatch"): compare(d)
    def test_unsupported_memory_unit_rejected(self):
        d = fixture(); d["candidate"]["context"]["memory_unit"] = "bytes"
        with self.assertRaisesRegex(ValueError, "memory_unit"): compare(d)
    def test_unknown_record_and_root_fields_rejected(self):
        d = fixture(); d["candidate"]["peak_memory_definition"] = "contradictory unvalidated units"
        with self.assertRaisesRegex(ValueError, "run fields"): compare(d)
        d = fixture(); d["candidate_status"] = "aborted"
        with self.assertRaisesRegex(ValueError, "exactly baseline and candidate"): compare(d)
    def test_overflow_or_underflow_ratios_rejected(self):
        for field in ("wall_seconds", "peak_memory_gb"):
            for a, b in ((1e308, 1e-308), (1e-308, 1e308)):
                d = fixture(); d["baseline"][field] = a; d["candidate"][field] = b
                with self.assertRaisesRegex(ValueError, "ratios"): compare(d)
    def test_boolean_factor_is_not_equal_to_integer(self):
        d = fixture(); d["baseline"]["factors"]["flag"] = True; d["candidate"]["factors"]["flag"] = 1
        with self.assertRaisesRegex(ValueError, "exactly one"): compare(d)
    def test_empty_context_or_factor_keys_rejected(self):
        for field in ("context", "factors"):
            d = fixture(); d["baseline"][field][""] = "invalid"
            with self.assertRaises(ValueError): compare(d)
