import copy
import unittest
from dry_checks import reachable, check_rewire, check_trace

def graph():
    return {"positive": {"inputs": {"text": "synthetic"}},
            "negative": {"inputs": {"text": "synthetic"}},
            "sample": {"inputs": {"positive": {"link": "positive"}, "negative": {"link": "negative"}, "cfg": 1, "bypass": True}},
            "output": {"inputs": {"image": {"link": "sample"}}}}
def trace():
    return [{"t": i*0.5, "phase": phase, "available_gib": ram, "added_swap_gib": 0, "monitor_error": False}
            for i, (phase, ram) in enumerate([("start",80),("running",30),("terminated",40),("recovered",80)])]

class DryChecks(unittest.TestCase):
    def test_intended_rewire(self):
        a=graph(); b=copy.deepcopy(a); b["sample"]["inputs"]["negative"]={"link":"positive"}
        self.assertEqual(check_rewire(a,b,"sample","negative","positive",["output"])["memory_improvement"],"untested")
        self.assertIn("negative",b)
    def test_extra_change_rejected(self):
        a=graph(); b=copy.deepcopy(a); b["sample"]["inputs"].update(negative={"link":"positive"},cfg=2)
        with self.assertRaisesRegex(ValueError,"outside"): check_rewire(a,b,"sample","negative","positive",["output"])
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
