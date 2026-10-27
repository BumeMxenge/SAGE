# ATP-6: access and privacy on the live deployment

report.py wrote this from attempts.csv and scan.csv. Every expectation was written down in access.py before the run.

## NF-5: access control

**PASS: every access attempt was blocked or allowed exactly as expected.**

| Visitor | Attempts | As expected | Differed |
| --- | --- | --- | --- |
| C | 1 | 1 | 0 |
| expired | 36 | 36 | 0 |
| forged | 18 | 18 | 0 |
| other | 18 | 18 | 0 |
| other (A's token) | 40 | 40 | 0 |
| owner | 18 | 18 | 0 |
| secret key | 1 | 1 | 0 |
| signed_out | 18 | 18 | 0 |
| staff | 18 | 18 | 0 |

### Attempts that differed from the expectation

Every attempt matched its written-down expectation.

## NF-5: the identifier scan

**PASS: no test email, student number or name was found in any scanned source.**

| Source | Items scanned | Identifiers | Hits |
| --- | --- | --- | --- |
| public schema (every row) | 7741 | 221 | none |
| container logs (/Users/bumemxenge/SAGE-load/tests/acceptance/atp5/results/container_logs.tsv) | 82316 | 221 | none |
| ATP-3 model requests (/Users/bumemxenge/SAGE-atp3/tests/acceptance/atp3/results/requests) | 401 | 221 | none |

