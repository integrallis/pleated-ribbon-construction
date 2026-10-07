generated-by: experiments/e1b_ribbon_construction/analyze_banding_steps.py over results/e1b/phase1/ (field banding_instr_per_key)

# Banding work by insertion order (derived — do not hand-edit)

| insertion order | instr/key at 100,000,000 (reps) | instr/key at 400,000,000 (reps) |
|---|---|---|
| arrival order | 97.43 (3) | 97.67 (3) |
| full sort (ips2ra) | 96.15 (3) | 97.67 (3) |
| partitioned, 2^16-slot windows | 97.85 (3) | 97.70 (3) |

Largest relative difference between orders: 1.8% at 100,000,000, 0.0% at 400,000,000. Insertion order changes where banding touches memory, not how much work it does.
