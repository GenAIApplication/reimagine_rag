#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./concurrent_curl.sh [URL]
# Default URL: http://localhost:8000/query

URL=${1:-http://localhost:8000/query}

questions=(
  "By how many years did global life expectancy at birth increase between 2000 and 2019, and how did COVID-19 affect this trend between 2019 and 2021?"
  "Where did COVID-19 rank among the leading causes of death globally in 2020 and 2021, and how many lives did it claim in those years?"
  "What was the global percentage of deaths caused by noncommunicable diseases (NCDs) in 2000, 2019, and 2021?"
  "How many children under five were affected by stunting, wasting, and overweight in 2022?"
  "What was the global crude death rate (CDR) from road traffic injuries in 2010 compared to 2021, and which WHO region had the highest CDR in 2021?"
)

tmpdir=$(mktemp -d)
declare -a pids=()
declare -a outfiles=()
declare -a start_times=()
declare -a end_times=()

echo "Starting concurrent requests to $URL..."

total_start_ts=$(date +%s)

for i in "${!questions[@]}"; do
  q="${questions[$i]}"
  body=$(printf '{"query":"%s"}' "${q//\"/\\\"}")
  out="$tmpdir/resp_$i.json"
  outfiles+=("$out")

  start_ts=$(date +%s)
  start_times+=("$start_ts")

  (
    curl_start=$(date +%s)
    curl -sS -X POST "$URL" \
      -H "Content-Type: application/json" \
      -d "$body" > "$out"
    curl_end=$(date +%s)
    echo "Request $i took $((curl_end - curl_start))s" >&2
  ) &
  pids+=("$!")
done

# Wait for all background curls
for pid in "${pids[@]}"; do
  wait "$pid"
done

total_end_ts=$(date +%s)
total_time=$((total_end_ts - total_start_ts))

echo "===== Results ====="
for i in "${!questions[@]}"; do
  q="${questions[$i]}"
  out="${outfiles[$i]}"
  ans=$(python3 - "$out" <<'PY'
import sys, json
path = sys.argv[1]
try:
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(data.get('response',''))
except Exception as e:
    print(f"[Parse error] {e}")
PY
)
  echo "Question: $q"
  echo "Answer: $ans"
  echo "------------------------"
done

echo "Total concurrent execution time: ${total_time}s"

# Cleanup
rm -rf "$tmpdir"
