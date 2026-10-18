#!/usr/bin/env python3
"""Find candidate images on Wikimedia Commons and return source/license metadata for human review."""
import argparse, html, json, re, urllib.parse, urllib.request

def plain(value): return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>"," ",value or ""))).strip()
def search(query, limit=12):
    params={"action":"query","generator":"search","gsrsearch":query,"gsrnamespace":6,"gsrlimit":limit,"prop":"imageinfo","iiprop":"url|extmetadata","iiurlwidth":1800,"format":"json"}
    url="https://commons.wikimedia.org/w/api.php?"+urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers={"User-Agent":"HotspotVideoPipeline/2.0 (license-candidate-review)"})
    data=json.load(urllib.request.urlopen(req,timeout=25)); candidates=[]
    for page in data.get("query",{}).get("pages",{}).values():
        info=page.get("imageinfo",[{}])[0];meta=info.get("extmetadata",{})
        candidates.append({"title":page.get("title"),"source_url":info.get("descriptionurl"),"download_url":info.get("thumburl") or info.get("url"),"creator":plain(meta.get("Artist",{}).get("value")),"license":plain(meta.get("LicenseShortName",{}).get("value")),"license_url":meta.get("LicenseUrl",{}).get("value"),"width":info.get("width"),"height":info.get("height"),"human_rights_review_required":True})
    return {"query":query,"source":"https://commons.wikimedia.org/w/api.php","count":len(candidates),"candidates":candidates}
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("query");p.add_argument("--limit",type=int,default=12);p.add_argument("--out",required=True);a=p.parse_args();r=search(a.query,a.limit);json.dump(r,open(a.out,"w",encoding="utf-8"),ensure_ascii=False,indent=2);print(json.dumps({"out":a.out,"count":r["count"]},ensure_ascii=False))
