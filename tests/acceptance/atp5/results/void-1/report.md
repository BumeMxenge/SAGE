# ATP-5: performance under load

report.py wrote this from the CSVs beside it. p95 is nearest-rank: a latency a request actually had. A verdict is given for the operations NF-4 names; the rest are read but set no target. Where a reply's time goes between its model calls is left to the Chapter 5 figures (README.md).

## Operations overall

| Operation | Target | Count | p50 ms | p95 ms | p99 ms | Errors | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| open | 1 s | 2108 | 1014 | 1308 | 2121 | 2.80% | FAIL (p95 1308 ms) |
| narrow | 1 s | 29 | 2425 | 3342 | 3745 | 10.34% | FAIL (p95 3342 ms) |
| check | 1 s | 2681 | 1129 | 1535 | 2343 | 51.51% | FAIL (p95 1535 ms) |
| first plan set | 10 s | 70 | 557 | 5987 | 8511 | 60.00% | FAIL (p95 5987 ms) |
| reply | 10 s | 175 | 6558 | 11023 | 14106 | 9.71% | FAIL (p95 11023 ms) |
| history | - | 2739 | 919 | 1197 | 1522 | 48.81% | - |
| me | - | 70 | 634 | 1581 | 3050 | 50.00% | - |
| pair | - | 692 | 1042 | 1342 | 2389 | 3.90% | - |
| plan set | - | 4128 | 932 | 1226 | 1735 | 50.36% | - |
| questionnaire | - | 70 | 586 | 2448 | 2651 | 58.57% | - |
| start chat | - | 58 | 1973 | 3529 | 3625 | 13.79% | - |

## NF-4: performance under load

Across every stage, 12820 operations, 39.23% failed (over NF-4's 1% limit).


### Stage hold_35a (35 users)

| Operation | Target | Count | p50 ms | p95 ms | p99 ms | Errors | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| open | 1 s | 930 | 1011 | 1223 | 1423 | 4.73% | FAIL (p95 1223 ms) |
| narrow | 1 s | 1 | 1941 | 1941 | 1941 | 0.00% | FAIL (p95 1941 ms) |
| check | 1 s | 777 | 1279 | 1573 | 2300 | 27.54% | FAIL (p95 1573 ms) |
| reply | 10 s | 75 | 6782 | 12692 | 16156 | 20.00% | FAIL (p95 12692 ms) |
| history | - | 769 | 969 | 1206 | 1322 | 22.37% | - |
| pair | - | 306 | 1031 | 1226 | 1369 | 8.17% | - |
| plan set | - | 1153 | 988 | 1226 | 1465 | 23.07% | - |
| start chat | - | 2 | 1585 | 1602 | 1602 | 0.00% | - |

### Stage hold_35b (35 users)

| Operation | Target | Count | p50 ms | p95 ms | p99 ms | Errors | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| open | 1 s | 468 | 978 | 1246 | 4878 | 0.43% | FAIL (p95 1246 ms) |
| check | 1 s | 789 | 834 | 1457 | 1587 | 64.26% | FAIL (p95 1457 ms) |
| reply | 10 s | 45 | 7324 | 11023 | 12882 | 0.00% | FAIL (p95 11023 ms) |
| history | - | 828 | 848 | 1129 | 1243 | 62.08% | - |
| pair | - | 150 | 1035 | 1267 | 1478 | 0.67% | - |
| plan set | - | 1251 | 840 | 1142 | 1257 | 64.83% | - |

## Where the time goes

- Cold start (first request after > 6 minutes idle): before: 6678.0 ms, after: 6638.2 ms.
- Warm /health median 546 ms against /v1/me median 738 ms: about 192 ms is the round trip to the EU database.

## The hosting comparison

At 35 users on 1 vCPU / 2 GiB with one to three replicas (no scale to zero), against the same operations on 0.25 vCPU / 0.5 GiB with scale to zero above.

| Operation | Target | Count | p50 ms | p95 ms | p99 ms | Errors | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| check | 1 s | 541 | 737 | 866 | 1087 | 100.00% | FAIL (p95 866 ms) |
| first plan set | 10 s | 23 | 576 | 938 | 939 | 100.00% | FAIL (p95 938 ms) |
| history | - | 530 | 736 | 878 | 1366 | 100.00% | - |
| me | - | 23 | 707 | 1057 | 1076 | 100.00% | - |
| plan set | - | 871 | 736 | 871 | 1108 | 100.00% | - |
| questionnaire | - | 23 | 574 | 908 | 915 | 100.00% | - |

## Azure over the window

| Metric | Max | Mean |
| --- | --- | --- |
| Replicas | 1 | 0 |
| Requests | 731 | 60 |
| UsageNanoCores | 212750000 | 47513480 |
| WorkingSetBytes | 329942016 | 282840109 |

