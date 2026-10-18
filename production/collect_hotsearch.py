#!/usr/bin/env python3
"""Save an unfiltered Bilibili public hotword snapshot as a per-run source record."""
import argparse, datetime, json, urllib.request, zoneinfo
URL="https://s.search.bilibili.com/main/hotword?limit=50&platform=pc"
def collect(out):
    req=urllib.request.Request(URL,headers={"User-Agent":"Mozilla/5.0 (compatible; hotspot-video-pipeline/2.0)","Referer":"https://www.bilibili.com/"})
    with urllib.request.urlopen(req,timeout=25) as r: payload=json.load(r)
    if payload.get("code")!=0 or not isinstance(payload.get("list"),list): raise RuntimeError("Bilibili hotword API returned an unexpected payload")
    rows=[]
    for rank,x in enumerate(payload["list"],1):
        rows.append({"rank":rank,"keyword":x.get("keyword"),"hot_id":x.get("hot_id"),"heat_score":x.get("heat_score"),"heat_layer":x.get("heat_layer")})
    result={"collected_at":datetime.datetime.now(zoneinfo.ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds"),"timezone":"Asia/Shanghai","source_url":URL,"hot_search_page":"https://www.bilibili.com/v/popular/rank/all","item_count":len(rows),"items":rows}
    with open(out,"w",encoding="utf-8") as f: json.dump(result,f,ensure_ascii=False,indent=2)
    return result
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--out",required=True);a=p.parse_args();d=collect(a.out)
    print(json.dumps({"out":a.out,"collected_at":d["collected_at"],"item_count":d["item_count"]},ensure_ascii=False))
