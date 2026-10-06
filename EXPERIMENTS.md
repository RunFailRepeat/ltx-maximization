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

Input: a JSON object with baseline and candidate records. Each has an ID, context object, factors object, wall_seconds and peak_memory_gb. Context must match exactly and must contain model_revision, workload_id, hardware_id and runtime_revision. Exactly one factor must differ. Numeric measurements must be finite and positive.

Outputs: baseline time divided by candidate time (above 1 means candidate is faster), baseline memory divided by candidate memory (above 1 means candidate uses less peak memory), and the changed factor. Quality is always marked unassessed. It cannot prove causation, assess footage, estimate full-project cost or choose a winner.

## Known limits

- Runtime/model identity and compatible settings must be pinned; recipes cannot be transferred blindly between generations or pipelines.
- Lower memory use does not establish unchanged quality; offload can change runtime costs.
- Peak-memory figures require the same measurement definition and include/exclude policy.
- Equal seeds do not guarantee equal outputs across software or hardware.
- No tested VRAM minimum, speedup, motion quality or production-ready result is claimed here.
- No model downloads, installs, training or generations were performed for this repository.
