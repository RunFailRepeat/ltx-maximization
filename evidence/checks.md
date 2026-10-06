# Reproducible check evidence

Checked 2026-10-06 with Python 3 standard library only.

- python -m unittest discover -s tests -v: 12 tests passed.
- python compare_runs.py examples/synthetic.json: speed_ratio 2.0; memory_ratio 2.0; quality unassessed; generalization not_established.

Those ratios come from fabricated 20/10-second and 8/4-GiB inputs. They are not LTX measurements.

Tests cover context mismatch, missing context, zero/nonfinite measurements, no/multiple changed factors, exact one-edge graph revision, rejection of extra changes, cycles/broken links, guard crossings, telemetry gaps, monitor errors and missing termination/recovery.

Original helper code uses standard-library metadata operations only. It does not read the machine's memory, control processes, download models or perform inference. A passing replay cannot establish a working live monitor, numerical equivalence, memory benefit, visual quality or identity fidelity.

The graph fixture is synthetic. Sanitized real-source observations are distinguished from test results in observations.md; no private graphs, raw logs, output images or runtime wrappers are included.
