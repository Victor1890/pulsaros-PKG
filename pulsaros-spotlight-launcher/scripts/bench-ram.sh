#!/bin/bash
# Usage: bench-ram.sh <binary> [args...]   (default arg: --hidden)
# Starts the binary, waits 6 s, prints memory split. 3 runs. Fails if RSS > $MAX_RSS_KB (optional).
B=${1:?binary}; shift; ARGS=${*:---hidden}
for i in 1 2 3; do
  "$B" $ARGS >/dev/null 2>&1 & pid=$!
  sleep 6
  rss=$(awk '/VmRSS/{print $2}' /proc/$pid/status)
  echo "run$i rss=${rss}KB anon=$(awk '/RssAnon/{print $2}' /proc/$pid/status)KB file=$(awk '/RssFile/{print $2}' /proc/$pid/status)KB pss=$(awk '/^Pss:/{print $2}' /proc/$pid/smaps_rollup)KB threads=$(awk '/Threads/{print $2}' /proc/$pid/status)"
  kill $pid; wait $pid 2>/dev/null
  [ -n "$MAX_RSS_KB" ] && [ "$rss" -gt "$MAX_RSS_KB" ] && { echo "FAIL: rss over $MAX_RSS_KB"; exit 1; }
done
