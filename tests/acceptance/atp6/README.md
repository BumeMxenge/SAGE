<!-- What ATP-6's access and privacy sweep tries, its written-down expectations, and how to run it -->
# ATP-6: access and privacy on the live deployment

ATP-6 asks whether every attempt on another student's data or on an administrator action is
blocked, and whether any name, student number or transcript is found where it shouldn't be (NF-5).
The row-level-security tests and the unit guard sweep are the white-box half; this is the black-box
half, on the real deployment. The scripts share ATP-5's uv environment and read the same `.env`, so
they run with `PYTHONPATH` pointing at `../atp5`.

## access.py

For every `/v1` route from the live OpenAPI schema, `access.py run` sends the request as the owner,
as another student using the owner's ids, as staff, signed out and with a forged token, and checks
each outcome against the expectation written in the script before the run. It first checks the
schema lists no route it has no expectation for, so a new route cannot slip the sweep. Then, with
the owner's token and the publishable key, it tries to read, insert, update and delete another
student's rows in every student table straight through PostgREST: row-level security hides the read
and the grants refuse every write. Then it uploads one made-up transcript as a third account that
has not finished setup, and lists the storage buckets and objects, to confirm the transcript was
read in memory and nothing was stored. `access.py expired` is a separate run for the expired-token
visitor, so it can wait until the owner's token is over an hour old; before then it records "not
run".

The expected outcomes mirror the white-box guard sweep in
`backend/tests/unit/shared/api/test_guards.py`: signed out, forged and expired are refused with
`not_signed_in`; staff get `students_only` on everything but `GET /v1/me`; another student with the
owner's plan or chat ids gets `plan_not_found`, `chat_not_found` or an empty list.

## scan.py

`scan.py` searches for every test email and student number, the made-up staff name and the name on
the uploaded transcript, in every public-schema row (read with the secret key), in the window's
container logs (a file exported by an az command, passed with `--logs`), and in ATP-3's saved model
requests (`--requests`, defaulting to `~/SAGE-atp3/.../results/requests`, skipped with a note if not
present yet). SAGE stores no names, numbers or transcripts and sends the model none, so zero hits is
the expected, POPIA-confirming result.

## report.py

`make atp6-report` writes `results/report.md` from `attempts.csv` and `scan.csv`: the attempts by
visitor and the scan, each with a verdict line. NF-5 holds when every attempt was blocked or allowed
exactly as expected and no identifier was found.

## Outputs

`results/` holds `attempts.csv`, `scan.csv` and `report.md`, each made only from a run, so every
line traces to an attempt or a scanned source.
