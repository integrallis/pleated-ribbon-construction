# filter_bench raw results (RocksDB v10.2.0, i9-14900HX)

Verified: binary rebuilt from patched source (object compiled clean, binary newer than source,
`PLEAT_PROFILE banding` string confirmed embedded) before these runs.

## Scale sweep — build ns/key + FP rate (stock vs pleated)

```
keys/filter    mode     build_ns/key FP
100000         stock    52.2625      0.948596
100000         pleated  54.356       0.948596
1000000        stock    62.816       0.951186
1000000        pleated  54.4487      0.951186
100000000      stock    94.467       0.953013
100000000      pleated  53.1509      0.953013
```

## 100M confirmation — timing repeats

```
stock:   95.8296 ns/key
stock:   94.8645 ns/key
pleated: 54.0724 ns/key
pleated: 53.5696 ns/key
```

## 20M keys/filter — 4-way matrix (two reps), FP identical (0.947791) across all

```
config           rep1_ns    rep2_ns
stock            91.7245    98.9337
no-prefetch      125.678    119.684
pleated          56.6171    57.9463
pleated+noPF     60.1637    62.4718
```

## Banding-phase hardware counters (perf_event_open, scoped to banding call)

20M keys/filter (no-prefetch baseline vs pleated):
```
pleat OFF: cache_misses/key=10.62, 10.72   instr/key=250.5
pleat ON : cache_misses/key= 0.457, 0.407  instr/key=248
```

100M keys/filter (stock vs pleated):
```
stock  : cache_misses/key=11.47, 11.42   instr/key=243.1
pleated: cache_misses/key= 0.463, 0.466  instr/key=243.3
```
