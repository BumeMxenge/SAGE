#!/bin/sh
# make atp4, start to finish. It refuses to start while either test port is taken, then starts the
# test's API on 8001 and frontend on 3001, makes the student and drives every scenario. Then it applies
# the planted fault, drives S1 and S5 again, and reverts the fault. Whatever happens, the trap reverts
# the fault, deletes the student and stops both servers. Last, it checks the runs and writes the
# report, which need no server. It calls no model: the API's OpenAI key is a stand-in.
set -eu

here=$(cd "$(dirname "$0")" && pwd)
repo=$(cd "$here/../../.." && pwd)
results="$here/results"
patch="$here/planted-fault.patch"
python="$repo/backend/.venv/bin/python"

for port in 8001 3001; do
  if lsof -nP -iTCP:"$port" -sTCP:LISTEN > /dev/null 2>&1; then
    echo "Port $port is in use, and ATP-4 needs it: stop what holds it first"
    exit 1
  fi
done

# Local Supabase's address and keys, as the Makefile's targets take them, never from backend/.env
env=$(cd "$repo" && npx supabase@2.120.0 status -o env) && eval "$env"
export SUPABASE_URL="$API_URL" SUPABASE_SECRET_KEY="$SECRET_KEY" OPENAI_API_KEY=atp4-stand-in

stop() {
  if git -C "$repo" apply --reverse --check "$patch" 2> /dev/null; then
    git -C "$repo" apply --reverse "$patch"
  fi
  (cd "$repo/backend" && "$python" "$here/student.py" delete) || true
  for port in 8001 3001; do
    lsof -nP -tiTCP:"$port" -sTCP:LISTEN | xargs kill 2> /dev/null || true
  done
}
trap stop EXIT
trap 'exit 1' INT TERM

(cd "$repo/backend" && exec "$python" "$here/serve.py") &
(cd "$repo/frontend" && VITE_API_URL=http://localhost:8001 VITE_SUPABASE_URL="$API_URL" \
  VITE_SUPABASE_PUBLISHABLE_KEY="$PUBLISHABLE_KEY" exec ./node_modules/.bin/vite --port 3001 --strictPort) &
for address in http://localhost:8001/health http://localhost:3001; do
  tries=0
  until curl --silent --fail --max-time 2 --output /dev/null "$address"; do
    tries=$((tries + 1))
    if [ "$tries" -gt 120 ]; then
      echo "$address didn't start within a minute"
      exit 1
    fi
    sleep 0.5
  done
done

mkdir -p "$results"
link=$(cd "$repo/backend" && "$python" "$here/student.py" create)
node "$here/drive.mjs" "$link" "$results/observations.json" no S1 S2 S3 S4 S5 S6

git -C "$repo" apply "$patch"
link=$(cd "$repo/backend" && "$python" "$here/student.py" link)
node "$here/drive.mjs" "$link" "$results/planted.json" yes S1 S5
git -C "$repo" apply --reverse "$patch"

(cd "$repo/backend" && "$python" "$here/check.py" && "$python" "$here/report.py")
