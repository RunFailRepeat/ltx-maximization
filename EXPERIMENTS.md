# Controlled experiment protocol

## Verified upstream context, checked 2026-10-06

The official [LTX-Video repository](https://github.com/Lightricks/LTX-Video) directs new development to LTX-2 and lists dev, distilled and quantized variants with different memory/quality trade-offs.

The official [LTX-2 repository](https://github.com/Lightricks/LTX-2) describes multiple pipelines and quantization/offload options. Its current README distinguishes LTX-2.5 components from legacy LTX-2.3 and states that their files are not interchangeable. Attention backends are hardware-dependent. These are upstream descriptions, not measured results from this project. Pin an immutable upstream revision and verify its matching model/config contract before implementation.

## What to measure

1. Choose one essential visible action and define pass/fail criteria before testing.
2. Fix prompt/reference versions, seed, dimensions, frame count/fps, model revision and hardware/runtime fingerprint.
3. Establish a baseline with actual wall time, peak memory, output existence and reviewed usable duration.
4. Change one factor at a time: for example precision, pipeline, offload or supported step schedule. Treat these as hypotheses, not universally beneficial toggles.
5. Repeat with a predeclared seed set. Report individual results and variability; one pair is not evidence of general superiority.
6. Review normal-speed motion and directly listened audio when applicable. Record anatomy, support/contact, identity consistency, story coverage and usable ranges separately from process success.
7. Preserve failure summaries and exact config hashes. Stop on approval/resource limits; do not retry automatically.

## Comparator contract

Input: a JSON object containing exactly baseline and candidate records. Each record must contain exactly id, context, factors, completed, safety_passed, wall_seconds and peak_memory_gb. Both completed and safety_passed must be the Boolean true. A stopped, failed, missing-status or unverified run is not a performance comparison; it must not receive speed/memory ratios. Unsupported record fields are rejected rather than silently ignoring conflicting status or measurement descriptions.

Context must match exactly and contain nonempty strings for model_revision, workload_id, hardware_id, runtime_revision, wall_time_scope, memory_metric, memory_scope and memory_unit. Additional nonempty string context entries are allowed and must also match. Use wall_time_scope to specify the measured window (for example prompt execution through completed output), memory_metric to distinguish resident/allocated/reserved memory, and memory_scope to distinguish a process, device or whole system. memory_unit must be GB (10^9 bytes) or GiB (2^30 bytes); the legacy peak_memory_gb field carries values in that explicit unit. Do not mix units, scopes, definitions or timing windows.

Exactly one factor must differ. Numeric measurements and computed ratios must be finite and positive. Boolean factor values are distinct from integers (true is not interchangeable with 1). The updated examples/synthetic.json is fabricated complete/safe metadata and still produces ratios of 2.0. Existing metadata must be explicitly migrated; do not infer successful completion, safety or measurement definitions to make an old record pass.

Outputs: baseline time divided by candidate time (above 1 means candidate is faster), baseline memory divided by candidate memory (above 1 means candidate uses less peak memory), and the changed factor. Quality is always marked unassessed. It cannot prove causation, assess footage, estimate full-project cost or choose a winner.

These validations check supplied metadata, not truth: a caller must substantiate completed work, passed safeguards and the declared measurement window using retained receipts. A true flag does not itself independently prove any of them. Equal context strings cannot detect an omitted or falsely recorded experimental difference.

## Offline graph and telemetry contract

The rewire checker accepts only the exact negative-input replacement to the declared positive source in its abstract graph. It compares nested values with their types: a second change from 1 to true, true to 1, or 1 to 1.0 is rejected even though ordinary Python equality can treat them alike. The edited conditioning node, positive source and old negative source must be reachable before the edit, and the edited node and positive source must remain reachable afterward. Exactly the old negative source may leave the reachable set. Callers must supply every actual output root; the checker does not infer ComfyUI output nodes. A structural pass establishes neither runtime compatibility nor CFG behavior, numerical equivalence or memory improvement.

Telemetry remains an offline replay of synthetic samples, never a live controller. Each sample needs t (seconds), phase, available_gib, added_swap_gib, swap_used_bytes and monitor_error=false. The first sample must be start at t=0 with added_swap_gib=0; its nonnegative integer swap_used_bytes is the absolute baseline. Every added_swap_gib is a signed delta from that baseline, and negative deltas are valid. It must match the absolute counters within one byte for display rounding. Counter-derived integer deltas, not rounded display values, enforce the swap boundary. Absolute counters reject negative values, booleans and fractional/nonfinite numbers.

At least one running sample, termination and final recovery are required in that order. Existing limits remain at least 80 GiB available at start/recovery, at least 24 GiB available throughout, no gap above 1 second, and no timestamp above 1200 seconds. The 0.5-second interval is a target, not proof that a live monitor met it. Every phase is checked, including shutdown and recovery.

LTX-HELPER-VALIDATION-002 proposes that reaching 2 GiB added logical swap fails acceptance (delta >= 2 GiB), with one-byte-below/equal/above tests. This clarifies an offline contract; it does not change a live controller, grant execution authority or authorize relaxing another safeguard. A valid sample list cannot prove that its phase labels correspond to actual process exit, absence of competing workloads, full lifecycle coverage or successful generation. Supply those independent receipts separately. No automatic retry.

## Known limits

- Runtime/model identity and compatible settings must be pinned; recipes cannot be transferred blindly between generations or pipelines.
- Lower memory use does not establish unchanged quality; offload can change runtime costs.
- Peak-memory figures require the same measurement definition and include/exclude policy.
- Equal seeds do not guarantee equal outputs across software or hardware.
- No tested VRAM minimum, speedup, motion quality or production-ready result is claimed here.
- No model downloads, installs, training or generations were performed for this repository.
