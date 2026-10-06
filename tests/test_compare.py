import copy
import unittest
from compare_runs import compare

def fixture():
    a = {"id": "synthetic-a",
         "context": {"model_revision": "synthetic-model-v1", "workload_id": "synthetic-scene",
                     "hardware_id": "synthetic-device", "runtime_revision": "synthetic-runtime-v1"},
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
        for v in (0, -1, float("nan"), float("inf"), True):
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
