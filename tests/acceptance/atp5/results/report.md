# ATP-5: performance under load

report.py wrote this from the CSVs beside it. p95 is nearest-rank: a latency a request actually had. A verdict is given for the operations NF-4 names; the rest are read but set no target. Where a reply's time goes between its model calls is left to the Chapter 5 figures (README.md).

## Operations overall

| Operation | Target | Count | p50 ms | p95 ms | p99 ms | Errors | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| open | 1 s | 2825 | 1052 | 1921 | 11012 | 1.42% | FAIL (p95 1921 ms) |
| narrow | 1 s | 45 | 3630 | 16212 | 24904 | 13.33% | FAIL (p95 16212 ms) |
| check | 1 s | 2353 | 1348 | 2348 | 12919 | 16.70% | FAIL (p95 2348 ms) |
| first plan set | 10 s | 70 | 9119 | 30008 | 30011 | 44.29% | FAIL (p95 30008 ms) |
| reply | 10 s | 239 | 7179 | 18332 | 30282 | 8.37% | FAIL (p95 18332 ms) |
| history | - | 2427 | 1015 | 1549 | 9069 | 13.31% | - |
| me | - | 70 | 1723 | 12403 | 16958 | 2.86% | - |
| pair | - | 949 | 1074 | 1826 | 10718 | 1.37% | - |
| plan set | - | 3668 | 1045 | 2306 | 12916 | 14.37% | - |
| questionnaire | - | 70 | 2897 | 14965 | 21964 | 35.71% | - |
| start chat | - | 102 | 2650 | 17049 | 23856 | 23.53% | - |

## NF-4: performance under load

Across every stage, 12818 operations, 10.95% failed (over NF-4's 1% limit).


### Stage hold_35a (35 users)

| Operation | Target | Count | p50 ms | p95 ms | p99 ms | Errors | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| open | 1 s | 1111 | 1046 | 1326 | 2404 | 0.81% | FAIL (p95 1326 ms) |
| narrow | 1 s | 2 | 1921 | 2099 | 2099 | 0.00% | FAIL (p95 2099 ms) |
| check | 1 s | 727 | 1363 | 1652 | 3197 | 1.93% | FAIL (p95 1652 ms) |
| reply | 10 s | 103 | 7516 | 12133 | 12384 | 5.83% | FAIL (p95 12133 ms) |
| history | - | 704 | 1024 | 1280 | 1572 | 0.71% | - |
| pair | - | 389 | 1062 | 1352 | 3119 | 1.03% | - |
| plan set | - | 1147 | 1058 | 1308 | 1680 | 0.96% | - |
| questionnaire | - | 2 | 1110 | 1296 | 1296 | 0.00% | - |
| start chat | - | 8 | 1451 | 1611 | 1611 | 12.50% | - |

### Stage hold_35b (35 users)

| Operation | Target | Count | p50 ms | p95 ms | p99 ms | Errors | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| open | 1 s | 760 | 1035 | 1275 | 1580 | 0.92% | FAIL (p95 1275 ms) |
| check | 1 s | 770 | 1292 | 1546 | 1721 | 25.71% | FAIL (p95 1546 ms) |
| reply | 10 s | 63 | 7242 | 10503 | 14811 | 3.17% | FAIL (p95 10503 ms) |
| history | - | 836 | 979 | 1237 | 1308 | 21.29% | - |
| pair | - | 263 | 1070 | 1302 | 2115 | 0.76% | - |
| plan set | - | 1130 | 989 | 1276 | 1653 | 23.72% | - |

## Where the time goes

- Cold start (first request after > 6 minutes idle): before: 6608.7 ms, after: 8663.3 ms.
- Warm /health median 544 ms against /v1/me median 758 ms: about 214 ms is the round trip to the EU database.
- open p95 in the steady 35-hold: 1275 ms on 0.25 vCPU, 1218 ms on 1 vCPU with three replicas.
- check p95 in the steady 35-hold: 1546 ms on 0.25 vCPU, 1591 ms on 1 vCPU with three replicas.
- Four times the CPU barely moves open or check p95, so the plan reads are not bound by CPU. Against a 546 ms network floor and about 192 ms per EU read, they are bound by round trips.

## The hosting comparison, per operation

The stage run (0.25 vCPU / 0.5 GiB, scale to zero, one replica) against the comparison (1 vCPU / 2 GiB, one to three replicas), p50 and p95 in milliseconds and fail the share of non-2xx. The comparison's shape is shortened and starts all 35 users at once rather than ramping over two minutes, so its first hold is not a like-for-like steady state and carries the freshly scaled replicas' start-up errors.

| Operation | Stage p50 | Stage p95 | Stage fail | Comp p50 | Comp p95 | Comp fail |
| --- | --- | --- | --- | --- | --- | --- |
| open | 1052 | 1921 | 1.4% | 1018 | 1282 | 0.7% |
| narrow | 3630 | 16212 | 13.3% | 2286 | 2685 | 15.0% |
| check | 1348 | 2348 | 16.7% | 1330 | 1650 | 7.1% |
| first plan set | 9119 | 30008 | 44.3% | 4354 | 5353 | 36.4% |
| reply | 7179 | 18332 | 8.4% | 6857 | 11367 | 3.9% |
| history | 1015 | 1549 | 13.3% | 989 | 1256 | 5.9% |
| me | 1723 | 12403 | 2.9% | 940 | 2594 | 0.0% |
| pair | 1074 | 1826 | 1.4% | 1019 | 1250 | 0.8% |
| plan set | 1045 | 2306 | 14.4% | 1025 | 1364 | 7.5% |
| questionnaire | 2897 | 14965 | 35.7% | 1185 | 1925 | 8.6% |
| start chat | 2650 | 17049 | 23.5% | 1612 | 1969 | 19.4% |

## Azure over the window

| Metric | Max | Mean |
| --- | --- | --- |
| Replicas | 2 | 1 |
| Requests | 758 | 213 |
| RestartCount | 0 | 0 |
| UsageNanoCores | 261250000 | 70638268 |
| WorkingSetBytes | 371337216 | 308950894 |

