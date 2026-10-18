#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
STORY=""; MANIFEST=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --story) STORY="$2"; shift 2;;
    --assets) MANIFEST="$2"; shift 2;;
    *) echo "Unknown argument: $1" >&2; exit 2;;
  esac
done
[[ -n "$STORY" && -n "$MANIFEST" ]] || { echo 'Usage: production/run_production.sh --story story.json --assets assets_manifest.json' >&2; exit 2; }
STORY="$(realpath "$STORY")"; MANIFEST="$(realpath "$MANIFEST")"
python "$HERE/validate_inputs.py" --story "$STORY" --assets "$MANIFEST"
TASK_ID="$(python -c 'import json,sys; print(json.load(open(sys.argv[1],encoding="utf-8"))["task_id"])' "$STORY")"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUNS="$ROOT/runs"; mkdir -p "$RUNS"
OUT="$RUNS/${STAMP}-${TASK_ID}"
mkdir "$OUT" || { echo "Run directory already exists; refusing to overwrite: $OUT" >&2; exit 1; }
cp "$STORY" "$OUT/story.json"; cp "$MANIFEST" "$OUT/assets_manifest.json"
python - "$MANIFEST" "$OUT" <<'PY'
import json,sys,os,shutil,pathlib
manifest=json.load(open(sys.argv[1],encoding="utf-8")); source=pathlib.Path(sys.argv[1]).resolve().parent; dest=pathlib.Path(sys.argv[2])
for asset in manifest["assets"]:
    rel=pathlib.Path(asset["path"])
    src=(source/rel).resolve(); target=(dest/rel).resolve()
    if not src.is_file(): raise SystemExit(f"missing source asset: {src}")
    target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,target)
PY
cp "$(dirname "$STORY")/$(python -c 'import json,sys,os; print(json.load(open(sys.argv[1],encoding="utf-8"))["hot_search"]["snapshot_path"])' "$STORY")" "$OUT/hotsearch_snapshot.json"
cp "$ROOT/production/README.md" "$OUT/pipeline_version.md"
python - "$OUT/task.json" "$TASK_ID" "$STAMP" <<'PY'
import json,sys,datetime
json.dump({"task_id":sys.argv[2],"run_id":sys.argv[3],"started_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"status":"running","attempt":1},open(sys.argv[1],"w"),indent=2)
PY
finish(){ rc=$?; python - "$OUT/task.json" "$rc" <<'PY'
import json,sys,datetime,os
p=sys.argv[1]
if os.path.exists(p):
 d=json.load(open(p));d["status"]="succeeded" if int(sys.argv[2])==0 and os.path.isfile(os.path.join(os.path.dirname(p),"final.mp4")) else "failed";d["exit_code"]=int(sys.argv[2]);d["finished_at_utc"]=datetime.datetime.now(datetime.timezone.utc).isoformat();json.dump(d,open(p,"w"),indent=2)
PY
  if [[ $rc -ne 0 ]]; then printf '{"status":"failed","exit_code":%s,"run_dir":"%s"}\n' "$rc" "$OUT" > "$OUT/failure_summary.json"; fi
  exit "$rc"
}
trap finish EXIT
python "$HERE/prepare_fonts.py" 2>&1 | tee "$OUT/font_setup.log"
mkdir -p "$OUT/licenses"
cp "$HERE/fonts/OFL.txt" "$OUT/licenses/NotoSansSC_OFL.txt"
python "$HERE/make_audio.py" --story "$OUT/story.json" --outdir "$OUT" 2>&1 | tee "$OUT/tts.log"
python "$HERE/render.py" --story "$OUT/story.json" --assets "$OUT/assets_manifest.json" --outdir "$OUT" 2>&1 | tee "$OUT/render.log"
python "$HERE/verify_media.py" --video "$OUT/final.mp4" --outdir "$OUT" --story "$OUT/story.json" 2>&1 | tee "$OUT/qa.log"
python - "$OUT/task.json" "$OUT/qa_report.json" <<'PY'
import json,sys
p=sys.argv[1]; d=json.load(open(p)); d["qa_report"]="qa_report.json";d["media"]="final.mp4";json.dump(d,open(p,"w"),indent=2)
PY
echo "$OUT/final.mp4"
