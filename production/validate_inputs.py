#!/usr/bin/env python3
"""Validate topic-specific editorial and image-rights inputs before production."""
import argparse, hashlib, json, os, re
from pathlib import Path

def load(path):
    with open(path, encoding="utf-8") as f: return json.load(f)

def validate(story_path, manifest_path):
    story_path=Path(story_path).resolve(); manifest_path=Path(manifest_path).resolve()
    story=load(story_path); manifest=load(manifest_path)
    for key in ("task_id", "title", "description", "tags", "hot_search", "claims", "script_segments"):
        if key not in story: raise ValueError(f"story.json missing {key}")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", story["task_id"]): raise ValueError("task_id must contain only letters, digits, dot, underscore or dash")
    if not story["script_segments"]: raise ValueError("script_segments is empty")
    if story.get("language") != "zh-CN": raise ValueError("only zh-CN script generation is enabled")
    hs=story["hot_search"]
    for key in ("snapshot_path", "keyword", "rank", "collected_at"):
        if key not in hs: raise ValueError(f"hot_search missing {key}")
    if not isinstance(hs["rank"], int) or hs["rank"] < 1: raise ValueError("hot_search.rank must be a positive integer")
    for i, claim in enumerate(story["claims"]):
        if not claim.get("text") or not claim.get("sources") or not all(str(u).startswith("https://") for u in claim["sources"]):
            raise ValueError(f"claim {i} needs text and at least one https source")
        if claim.get("status") != "verified": raise ValueError(f"claim {i} is not marked verified")
    entries=manifest.get("assets")
    if not isinstance(entries, list) or not entries: raise ValueError("assets_manifest.json must contain assets")
    assets={}
    for a in entries:
        for key in ("id", "path", "source_url", "creator", "license", "license_url", "attribution", "use_basis", "visual_kind", "modifications"):
            if not a.get(key): raise ValueError(f"asset {a.get('id','?')} missing {key}")
        if not a["source_url"].startswith("https://") or not a["license_url"].startswith("https://"):
            raise ValueError(f"asset {a['id']} needs https source/license URLs")
        if a.get("rights_reviewed") is not True:
            raise ValueError(f"asset {a['id']} has not passed explicit human rights review")
        if a["visual_kind"] == "historical_photo" and a.get("represents_current_event") is True:
            raise ValueError(f"historical asset {a['id']} cannot represent the current event")
        p=(manifest_path.parent / a["path"]).resolve()
        if not p.is_relative_to(manifest_path.parent): raise ValueError(f"asset {a['id']} path escapes the manifest directory")
        if not p.is_file(): raise ValueError(f"asset file missing: {p}")
        if a.get("sha256") and hashlib.sha256(p.read_bytes()).hexdigest()!=a["sha256"]:
            raise ValueError(f"asset hash mismatch: {a['id']}")
        a["resolved_path"]=str(p); assets[a["id"]]=a
    for i, seg in enumerate(story["script_segments"]):
        if not seg.get("id") or not seg.get("text"): raise ValueError(f"script segment {i} missing id/text")
        if seg.get("asset_id") not in assets: raise ValueError(f"script segment {seg.get('id')} references unknown asset")
    hot_path=(story_path.parent / hs["snapshot_path"]).resolve()
    if not hot_path.is_file(): raise ValueError(f"hot search snapshot missing: {hot_path}")
    snapshot=load(hot_path)
    if snapshot.get("collected_at") != hs["collected_at"]: raise ValueError("story hot_search timestamp does not match source snapshot")
    hits=[x for x in snapshot.get("items",[]) if x.get("rank")==hs["rank"] and x.get("keyword")==hs["keyword"]]
    if not hits: raise ValueError("story hot_search rank/keyword absent from the captured snapshot")
    return story, manifest, assets, hot_path

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--story",required=True); ap.add_argument("--assets",required=True); args=ap.parse_args()
    story,manifest,assets,hot=validate(args.story,args.assets)
    print(json.dumps({"valid":True,"task_id":story["task_id"],"segments":len(story["script_segments"]),"assets":len(assets),"hot_search_snapshot":str(hot)},ensure_ascii=False))
