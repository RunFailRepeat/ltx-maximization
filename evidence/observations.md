# Sanitized source observations

These are owner-provided observations and a reviewed static assessment, not new runs performed for this repository. Private graphs, assets, raw logs, machine identifiers and source file hashes are intentionally omitted.

| Case | Installed | Executed | Safety pass | Visual pass | Identity-fidelity pass |
| --- | --- | --- | --- | --- | --- |
| Basic red-ball video | Runtime available per source report; exact dependency lock not supplied here | Reported succeeded | Full lifecycle evidence not supplied here | Basic success reported; independent full review not performed here | Not tested |
| Reference-conditioned run | Runtime available per source report | Attempted | Failed added-swap guard | No completed output established | Not tested |
| Reference-bypass run | Runtime available per source report | Attempted; stopped before sampling | Failed added-swap guard | Not assessed | Not tested |
| Shared-conditioning graph revision | Static preparation only | Not executed | Runtime safety untested | Not assessed | Not tested |

A one-frame reconstruction does not establish diffusion generation, motion, reference-conditioned quality or identity fidelity.

## Static revision hypothesis

The reviewed source assessment changes one negative-conditioning edge to use the positive-conditioning source. The previous negative encoder remains present but unreachable from output roots; bypass and CFG=1 are unchanged. Under default CFG=1 optimization without custom hooks or a disabled optimization, the source assessment predicts unchanged positive diffusion prediction. This is a conditional hypothesis: numerical equivalence and memory benefit remain untested.

Observed swap was already near the guard before the reported negative-encoding start. Removing that encoding is therefore not a proven memory fix; loading and positive encoding still consume memory. Client receipt timestamps do not give exact native stage boundaries.

The public checker uses an invented abstract graph with named nodes and explicit links. It does not execute, rewrite or claim compatibility with a real ComfyUI workflow.

## Experiment-specific safeguard record

Starting and recovered available RAM: at least 80 GiB.
Available-RAM floor: 24 GiB.
Added logical swap ceiling: 2 GiB.
Timeout: 1200 seconds.
Target full-lifecycle sample interval: 0.5 seconds; fail on gaps above 1 second.
Continue coverage through termination and final recovery; fail closed on monitor errors or incomplete recovery. No automatic retry.

These are the measured experiment's safeguards, not universal hardware recommendations. dry_checks.py only replays supplied synthetic telemetry. It is not an independent live monitor or a substitute for process termination/recovery controls.

Missing for reproducible real execution: approved sanitized workflow, immutable upstream revision, model/checkpoint/license manifest, dependency lock, launch specification, measurement definitions and complete sanitized lifecycle evidence.
