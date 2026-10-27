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

## The hosting comparison

At 35 users on 1 vCPU / 2 GiB with one to three replicas (no scale to zero), against the same operations on 0.25 vCPU / 0.5 GiB with scale to zero above.

| Operation | Target | Count | p50 ms | p95 ms | p99 ms | Errors | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| open | 1 s | 768 | 1018 | 1282 | 2090 | 0.65% | FAIL (p95 1282 ms) |
| narrow | 1 s | 20 | 2286 | 2685 | 2742 | 15.00% | FAIL (p95 2685 ms) |
| check | 1 s | 1488 | 1330 | 1650 | 5351 | 7.12% | FAIL (p95 1650 ms) |
| first plan set | 10 s | 11 | 4354 | 5353 | 5353 | 36.36% | FAIL (p95 5353 ms) |
| reply | 10 s | 51 | 6857 | 11367 | 19676 | 3.92% | FAIL (p95 11367 ms) |
| history | - | 1564 | 989 | 1256 | 1534 | 5.88% | - |
| me | - | 70 | 940 | 2594 | 2628 | 0.00% | - |
| pair | - | 250 | 1019 | 1250 | 3672 | 0.80% | - |
| plan set | - | 2374 | 1025 | 1364 | 5010 | 7.46% | - |
| questionnaire | - | 70 | 1185 | 1925 | 3806 | 8.57% | - |
| start chat | - | 62 | 1612 | 1969 | 2090 | 19.35% | - |

## Azure over the window

| Metric | Max | Mean |
| --- | --- | --- |
| Replicas | 2 | 1 |
| Requests | 758 | 213 |
| RestartCount | 0 | 0 |
| UsageNanoCores | 261250000 | 70638268 |
| WorkingSetBytes | 371337216 | 308950894 |

