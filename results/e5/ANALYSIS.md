generated-by: experiments/e5_byte_identity/run.py --stage analyze over results/e5/ (machine: AMD EPYC-Milan Processor, x86_64; RocksDB 31b239747)

# E5 analysis (derived — do not hand-edit)

| keys/filter | pair | filters | byte-compare differing | SHA-256 lists equal |
|---|---|---|---|---|
| 100,000 | stock_a vs stock_b | 396 / 396 | 0 | yes |
| 100,000 | stock_a vs pleated | 396 / 396 | 0 | yes |
| 1,000,000 | stock_a vs stock_b | 40 / 40 | 0 | yes |
| 1,000,000 | stock_a vs pleated | 40 / 40 | 0 | yes |
| 10,000,000 | stock_a vs stock_b | 4 / 4 | 0 | yes |
| 10,000,000 | stock_a vs pleated | 4 / 4 | 0 | yes |
| 100,000,000 | stock_a vs stock_b | 3 / 3 | 0 | yes |
| 100,000,000 | stock_a vs pleated | 3 / 3 | 0 | yes |

- Control (stock_a == stock_b at every size): PASS
- **H-E5** (pleated byte-identical to stock at every size): HOLDS — 443 filters compared, all identical
