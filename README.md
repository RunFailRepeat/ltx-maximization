# LTX maximization

A measurement-first experiment protocol and small offline comparator for LTX investigations. “Maximization” means finding a useful speed/memory/quality trade-off for a specified task; it is not a claim of optimal settings or production quality.

- [Experiment protocol and known limitations](EXPERIMENTS.md)
- [Comparator](compare_runs.py)
- [Synthetic example](examples/synthetic.json)
- [Check evidence](evidence/checks.md)
- [Sanitized observations and safeguard limits](evidence/observations.md)
- [Offline graph/telemetry checks](dry_checks.py)

## Try the comparator

Python 3 standard library only. Review the code first.

```sh
python -m unittest discover -s tests -v
python compare_runs.py examples/synthetic.json
```

This reads metadata and prints ratios. It does not import a model framework, access the network, download weights, inspect the machine, launch subprocesses or run inference. The example is fabricated test data, not a hardware benchmark.

## Implementation status

Implemented: metadata comparison, compatibility guards, offline graph/telemetry validators and synthetic unit tests.
Not implemented/verified: LTX runtime installation, inference adapter, model acquisition, hardware tuning, actual generations, audiovisual evaluation or any optimal configuration.

Needed before a reproducible real implementation: exact LTX family/model ID and revision; chosen upstream commit; sanitized actual config/workflow; dependency lock; reviewed invocation; model/license manifest; sanitized hardware/runtime versions; and measured runs with quality-review coverage. Source reports and a static graph assessment are summarized in the observations document; they are not a runnable implementation or independently reproduced benchmark.

Roadmap: review sanitized source exports, pin the runtime/model, validate an independent full-lifecycle guard, then seek separate authorization for a bounded experiment. Numerical equivalence, memory improvement and identity fidelity remain untested. No automatic retry.

Do not contribute credentials, personal paths, access details, private media/scripts/references or raw logs. Use opaque experiment IDs and reviewed summaries. No paid calls or model runs are authorized by this repository.
