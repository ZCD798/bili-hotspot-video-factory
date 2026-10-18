#!/usr/bin/env python3
"""Fetch the OFL Noto Sans SC variable font and register it for libass/fontconfig."""
import os, shutil, subprocess, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parent
FONT_DIR=ROOT/"fonts"; FONT_DIR.mkdir(exist_ok=True)
FONT=FONT_DIR/"NotoSansSC-VF.ttf"; LICENSE=FONT_DIR/"OFL.txt"
SOURCES={FONT:"https://raw.githubusercontent.com/google/fonts/main/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf",LICENSE:"https://raw.githubusercontent.com/google/fonts/main/ofl/notosanssc/OFL.txt"}
for path,url in SOURCES.items():
    if not path.is_file():
        req=urllib.request.Request(url,headers={"User-Agent":"hotspot-video-pipeline/2.0"})
        with urllib.request.urlopen(req,timeout=30) as r: path.write_bytes(r.read())
if FONT.stat().st_size<1000000: raise RuntimeError("Noto Sans SC download is unexpectedly small")
user_fonts=Path.home()/".local/share/fonts";user_fonts.mkdir(parents=True,exist_ok=True)
registered=user_fonts/"HotspotVideoPipeline-NotoSansSC-VF.ttf"
shutil.copy2(FONT,registered)
if shutil.which("fc-cache"):
    subprocess.run(["fc-cache","-f",str(user_fonts)],check=True,stdout=subprocess.DEVNULL)
else: raise RuntimeError("fontconfig fc-cache is unavailable; libass CJK font registration cannot be verified")
match=subprocess.check_output(["fc-match","Noto Sans SC"],text=True).strip()
if not match or "Noto" not in match: raise RuntimeError(f"fontconfig did not resolve Noto Sans SC: {match}")
print(f"Registered Noto Sans SC for Pillow/libass: {registered}; {match}")
