#!/usr/bin/env python3
"""Download only manifest assets marked rights_reviewed; validate bytes and record SHA-256."""
import argparse, hashlib, json, os, urllib.request
from pathlib import Path
from PIL import Image

def run(manifest_path):
    p=Path(manifest_path).resolve(); data=json.load(open(p,encoding="utf-8"));
    for asset in data.get("assets",[]):
        if asset.get("rights_reviewed") is not True: raise ValueError(f"asset {asset.get('id')} requires explicit rights_reviewed=true")
        for key in ("download_url","source_url","creator","license","license_url","use_basis","path"):
            if not asset.get(key): raise ValueError(f"asset {asset.get('id')} missing {key}")
        if not asset["download_url"].startswith("https://") or not asset["source_url"].startswith("https://"):
            raise ValueError(f"asset {asset['id']} URLs must use HTTPS")
        dst=(p.parent/asset["path"]).resolve()
        if not dst.is_relative_to(p.parent): raise ValueError(f"asset {asset['id']} path escapes the manifest directory")
        dst.parent.mkdir(parents=True,exist_ok=True)
        req=urllib.request.Request(asset["download_url"],headers={"User-Agent":"HotspotVideoPipeline/2.0 (approved-assets-downloader)"})
        with urllib.request.urlopen(req,timeout=35) as r: content=r.read()
        dst.write_bytes(content)
        with Image.open(dst) as im:
            im.verify();asset["sha256"]=hashlib.sha256(content).hexdigest();asset["downloaded_bytes"]=len(content);asset["verified_dimensions"]=list(im.size)
    json.dump(data,open(p,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
    return [{"id":a["id"],"sha256":a["sha256"],"bytes":a["downloaded_bytes"]} for a in data["assets"]]
if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--manifest",required=True);args=ap.parse_args();print(json.dumps(run(args.manifest),ensure_ascii=False,indent=2))
