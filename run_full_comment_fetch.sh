#!/usr/bin/env bash
set -euo pipefail

RAW_DIR="${RAW_DIR:-data/raw}"
OUTPUT_ROOT="${OUTPUT_ROOT:-data/comments_full}"
BATCH_SIZE="${BATCH_SIZE:-100}"
MAX_PAGES="${MAX_PAGES:-5}"
MAX_QUOTA_UNITS="${MAX_QUOTA_UNITS:-10000}"
QUOTA_BUFFER="${QUOTA_BUFFER:-500}"
START_OFFSET="${START_OFFSET:-0}"
REMAINING_QUOTA_UNITS="${REMAINING_QUOTA_UNITS:-}"
RESUME=false
DRY_RUN=false
SUGGEST_BATCH=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --resume)
      RESUME=true
      shift
      ;;
    --start-offset)
      START_OFFSET="$2"
      shift 2
      ;;
    --remaining-quota)
      REMAINING_QUOTA_UNITS="$2"
      shift 2
      ;;
    --suggest-batch)
      SUGGEST_BATCH=true
      shift
      ;;
    --help|-h)
      SHOW_HELP=true
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

if [[ "${SHOW_HELP:-false}" == true ]]; then
  cat <<'EOF'
Usage: ./run_full_comment_fetch.sh [--dry-run] [--resume] [--start-offset N]

Runs the comment fetch in safe batches across all unique video IDs in data/raw.

Environment overrides:
  RAW_DIR          Default: data/raw
  OUTPUT_ROOT      Default: data/comments_full
  BATCH_SIZE       Default: 100
  MAX_PAGES        Default: 5
  MAX_QUOTA_UNITS  Default: 10000
  QUOTA_BUFFER     Default: 500
  START_OFFSET     Default: 0

The script uses a conservative quota guard: it stops before the estimated use would
exceed MAX_QUOTA_UNITS - QUOTA_BUFFER, so you leave headroom for other API work.

Resume behavior:
  --resume loads prior progress from OUTPUT_ROOT/resume_state.json and continues from
  the next unprocessed offset. --start-offset overrides that and begins at the given
  video index.

Quota planning:
  --remaining-quota N lets you enter the amount of quota remaining in your Google Cloud
  account. Combined with --suggest-batch, it prints a safe batch size to use next.

Examples:
  ./run_full_comment_fetch.sh
  ./run_full_comment_fetch.sh --dry-run
  ./run_full_comment_fetch.sh --resume
  START_OFFSET=160 ./run_full_comment_fetch.sh
  ./run_full_comment_fetch.sh --remaining-quota 2000 --suggest-batch
  MAX_QUOTA_UNITS=2000 QUOTA_BUFFER=200 BATCH_SIZE=50 MAX_PAGES=3 ./run_full_comment_fetch.sh
EOF
  exit 0
fi

TOTAL_IDS=$(python - <<'PY'
import json
from pathlib import Path
raw = Path('data/raw')
ids = set()
for p in sorted(raw.glob('*.json')):
    try:
        data = json.loads(p.read_text())
    except Exception:
        continue
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = data.get('items') or data.get('videos') or []
    else:
        items = []
    for item in items:
        vid = item.get('videoId') or item.get('id')
        if isinstance(vid, str) and vid.strip():
            ids.add(vid.strip())
print(len(ids))
PY
)

if [[ "$TOTAL_IDS" -eq 0 ]]; then
  echo "No video IDs found in $RAW_DIR" >&2
  exit 1
fi

if [[ "$SUGGEST_BATCH" == true ]]; then
  if [[ -z "$REMAINING_QUOTA_UNITS" ]]; then
    echo "--remaining-quota is required when using --suggest-batch" >&2
    exit 1
  fi
  if [[ ! "$REMAINING_QUOTA_UNITS" =~ ^[0-9]+$ ]]; then
    echo "REMAINING_QUOTA_UNITS must be a non-negative integer" >&2
    exit 1
  fi
  if [[ ! "$QUOTA_BUFFER" =~ ^[0-9]+$ ]] || (( QUOTA_BUFFER < 0 )); then
    echo "QUOTA_BUFFER must be a non-negative integer" >&2
    exit 1
  fi
  safe_budget=$(( REMAINING_QUOTA_UNITS - QUOTA_BUFFER ))
  if (( safe_budget <= 0 )); then
    echo "No safe batch is available with remaining quota $REMAINING_QUOTA_UNITS and buffer $QUOTA_BUFFER."
    exit 0
  fi
  recommended_batch=$(( safe_budget / MAX_PAGES ))
  if (( recommended_batch <= 0 )); then
    recommended_batch=1
  fi
  if (( recommended_batch > TOTAL_IDS )); then
    recommended_batch=$TOTAL_IDS
  fi
  echo "Remaining quota from Google Cloud: $REMAINING_QUOTA_UNITS units"
  echo "Quota buffer: $QUOTA_BUFFER units"
  echo "Safe budget to spend: $safe_budget units"
  echo "Max pages per video: $MAX_PAGES"
  echo "Recommended safe batch size: $recommended_batch video IDs"
  exit 0
fi

if [[ ! "$START_OFFSET" =~ ^[0-9]+$ ]] || (( START_OFFSET < 0 )); then
  echo "START_OFFSET must be a non-negative integer" >&2
  exit 1
fi

if [[ "$BATCH_SIZE" =~ ^[0-9]+$ ]] && [[ "$BATCH_SIZE" -le 0 ]]; then
  echo "BATCH_SIZE must be a positive integer" >&2
  exit 1
fi

if [[ "$MAX_PAGES" =~ ^[0-9]+$ ]] && [[ "$MAX_PAGES" -le 0 ]]; then
  echo "MAX_PAGES must be a positive integer" >&2
  exit 1
fi

if [[ ! "$MAX_QUOTA_UNITS" =~ ^[0-9]+$ ]] || [[ "$MAX_QUOTA_UNITS" -le 0 ]]; then
  echo "MAX_QUOTA_UNITS must be a positive integer" >&2
  exit 1
fi

if [[ ! "$QUOTA_BUFFER" =~ ^[0-9]+$ ]] || [[ "$QUOTA_BUFFER" -lt 0 ]]; then
  echo "QUOTA_BUFFER must be a non-negative integer" >&2
  exit 1
fi

SAFE_QUOTA_LIMIT=$(( MAX_QUOTA_UNITS - QUOTA_BUFFER ))
if (( SAFE_QUOTA_LIMIT <= 0 )); then
  echo "Quota guard is invalid: MAX_QUOTA_UNITS - QUOTA_BUFFER must be positive." >&2
  exit 1
fi

state_file="$OUTPUT_ROOT/resume_state.json"
resume_offset=0
if [[ "$RESUME" == true ]]; then
  if [[ -f "$state_file" ]]; then
    resume_offset=$(python - <<'PY' "$state_file"
import json, sys
path = sys.argv[1]
try:
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(int(data.get('next_offset', 0)))
except Exception:
    print(0)
PY
)
    echo "Resuming from saved offset: $resume_offset"
  else
    echo "No resume state found at $state_file; starting at offset 0."
  fi
fi

if (( START_OFFSET > 0 )); then
  resume_offset=$START_OFFSET
fi

if (( resume_offset >= TOTAL_IDS )); then
  echo "Start offset $resume_offset is beyond the dataset size ($TOTAL_IDS); nothing to do."
  exit 0
fi

BATCH_COUNT=$(( (TOTAL_IDS - resume_offset + BATCH_SIZE - 1) / BATCH_SIZE ))

estimated_total=$(( (TOTAL_IDS - resume_offset) * MAX_PAGES ))

echo "Total unique video IDs: $TOTAL_IDS"
echo "Starting offset: $resume_offset"
echo "Batch size: $BATCH_SIZE"
echo "Estimated batches remaining: $BATCH_COUNT"
echo "Estimated remaining quota use: ~$estimated_total units"
echo "Safe quota cap: $SAFE_QUOTA_LIMIT units (MAX_QUOTA_UNITS=$MAX_QUOTA_UNITS, QUOTA_BUFFER=$QUOTA_BUFFER)"

echo

used_units=0
batch_number=1
offset=$resume_offset
while (( offset < TOTAL_IDS )); do
  remaining=$((TOTAL_IDS - offset))
  current_batch=$(( remaining < BATCH_SIZE ? remaining : BATCH_SIZE ))
  batch_units=$(( current_batch * MAX_PAGES ))

  if (( used_units + batch_units > SAFE_QUOTA_LIMIT )); then
    remaining_budget=$(( SAFE_QUOTA_LIMIT - used_units ))
    if (( remaining_budget <= 0 )); then
      echo "Quota guard stopped the run: already at or above the safe quota cap ($SAFE_QUOTA_LIMIT units)."
      break
    fi
    reduced_batch=$(( remaining_budget / MAX_PAGES ))
    if (( reduced_batch <= 0 )); then
      echo "Quota guard stopped the run: not enough headroom left to process another batch."
      break
    fi
    current_batch=$(( reduced_batch < current_batch ? reduced_batch : current_batch ))
    batch_units=$(( current_batch * MAX_PAGES ))
    echo "Quota guard reduced this batch to $current_batch videos to stay under the safe cap."
  fi

  output_dir="$OUTPUT_ROOT/batch_$((batch_number + (resume_offset > 0 ? 0 : 0)))"
  if (( offset == resume_offset )); then
    output_dir="$OUTPUT_ROOT/batch_$((resume_offset / BATCH_SIZE + 1))"
  else
    output_dir="$OUTPUT_ROOT/batch_$((offset / BATCH_SIZE + 1))"
  fi

  cmd=(python fetch_video_comments.py --from-json "$RAW_DIR" --output-dir "$output_dir" --batch-size "$current_batch" --batch-offset "$offset" --max-pages "$MAX_PAGES")

  echo "Batch ${batch_number}: offset=$offset size=$current_batch"
  if [[ "$DRY_RUN" == true ]]; then
    echo "Would run: ${cmd[*]}"
  else
    "${cmd[@]}"
    used_units=$(( used_units + batch_units ))
    echo "Used units so far: $used_units / $SAFE_QUOTA_LIMIT"
    echo "Completed batch ${batch_number}"
    mkdir -p "$OUTPUT_ROOT"
    python - <<'PY' "$OUTPUT_ROOT/resume_state.json" "$((offset + current_batch))"
import json, sys
path = sys.argv[1]
next_offset = int(sys.argv[2])
with open(path, 'w', encoding='utf-8') as f:
    json.dump({"next_offset": next_offset, "updated_at": "now"}, f)
PY
    echo "Saved resume state to $OUTPUT_ROOT/resume_state.json"
  fi
  echo

  offset=$((offset + current_batch))
  batch_number=$((batch_number + 1))

  if [[ "$DRY_RUN" == true ]] && (( used_units >= SAFE_QUOTA_LIMIT )); then
    break
  fi

  if [[ "$DRY_RUN" != true ]] && (( used_units >= SAFE_QUOTA_LIMIT )); then
    break
  fi
done

if [[ "$DRY_RUN" == true ]]; then
  echo "Dry run complete. No API calls were made."
else
  if (( offset >= TOTAL_IDS )); then
    echo "All comment batches complete."
  else
    echo "Reached the safe quota cap. Resume later with --resume or START_OFFSET=$offset."
  fi
fi
