#!/usr/bin/env python3
"""Create topic-driven portrait scenes, kinetic photo crops and synchronized Chinese subtitles."""
import argparse, json, math, os, subprocess, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from validate_inputs import validate

W,H,FPS=1080,1920,15
def ass_time(sec):
    x=round(sec*100); h,x=divmod(x,360000);m,x=divmod(x,6000);s,x=divmod(x,100);return f"{h}:{m:02}:{s:02}.{x:02}"
def srt_time(sec):
    ms=round(sec*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000);return f"{h:02}:{m:02}:{s:02},{ms:03}"
def wrap_text(text,font,max_width):
    lines=[];cur=""
    for ch in text:
        if cur and font.getlength(cur+ch)>max_width: lines.append(cur);cur=ch
        else: cur+=ch
    if cur: lines.append(cur)
    return "\\N".join(lines)
def center(draw,y,text,font,fill,stroke_width=2):
    box=draw.textbbox((0,0),text,font=font,stroke_width=stroke_width)
    draw.text(((W-box[2]+box[0])/2,y),text,font=font,fill=fill,stroke_width=stroke_width,stroke_fill=(0,0,0,210))
def make_card(story,segment,asset,fontpath,outpng):
    font=lambda n:ImageFont.truetype(fontpath,n)
    src=Image.open(asset["resolved_path"]).convert("RGB")
    # Full-frame blurred photo atmosphere, with a large sharp source photo in front.
    cover_scale=max(W/src.width,H/src.height)
    cover=src.resize((round(src.width*cover_scale),round(src.height*cover_scale)),Image.Resampling.LANCZOS)
    cx=(cover.width-W)//2; cy=max(0,min(cover.height-H,round((cover.height-H)*0.36)))
    bg=cover.crop((cx,cy,cx+W,cy+H)).filter(ImageFilter.GaussianBlur(34)).convert("RGBA")
    bg=Image.alpha_composite(bg,Image.new("RGBA",(W,H),(2,8,18,128))).convert("RGB")
    crop=src.copy(); crop.thumbnail((W,1080),Image.Resampling.LANCZOS)
    bg.paste(crop,((W-crop.width)//2,420+(1080-crop.height)//2))
    overlay=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(overlay,"RGBA")
    for y in range(360): d.line((0,y,W,y),fill=(3,10,20,int(215*(1-y/360))))
    for y in range(1420,H): d.line((0,y,W,y),fill=(3,8,16,int(220*(y-1420)/(H-1420))))
    d.rounded_rectangle((54,70,1026,130),radius=24,fill=(2,15,28,225),outline=(110,205,229,130),width=2)
    d.text((76,84),asset["attribution"][:64],font=font(23),fill=(235,246,250,255))
    headline=segment.get("headline",story["title"])
    center(d,180,headline[:25],font(53),(255,255,255,255))
    if segment.get("visual_note"):
        center(d,255,segment["visual_note"][:30],font(30),(180,222,237,255),1)
    # Rights provenance and factual status remain clearly visible above the caption safe band.
    d.rounded_rectangle((62,1360,1018,1448),radius=20,fill=(2,14,28,220),outline=(160,195,214,90),width=1)
    label="通用服务器示意画面 · 非 DeepSeek 现场"
    license_short="Public domain" if asset["license"].startswith("Public domain") else asset["license"]
    credit_line=f"{label} · {license_short}"
    credit_font=font(25); box=d.textbbox((0,0),credit_line,font=credit_font)
    if box[2]-box[0] <= 890:
        d.text(((W-(box[2]-box[0]))/2,1388),credit_line,font=credit_font,fill=(235,240,245,255))
    else:
        credit_font=font(21); center(d,1373,label,credit_font,(235,240,245,255),1); center(d,1405,license_short,credit_font,(198,220,233,255),1)
    bg=Image.alpha_composite(bg.convert("RGBA"),overlay)
    bg.convert("RGB").save(outpng,quality=94)
def main(story_path,manifest_path,outdir):
    story,manifest,assets,hot=validate(story_path,manifest_path)
    timing=json.load(open(os.path.join(outdir,"audio_timing.json"),encoding="utf-8")); cues=timing["cues"]
    fonts=os.path.join(str(Path.home()),".local","share","fonts")
    fontpath=os.path.join(fonts,"HotspotVideoPipeline-NotoSansSC-VF.ttf")
    if not os.path.isfile(fontpath): raise FileNotFoundError("Noto Sans SC is not registered; run production/prepare_fonts.py")
    scenes=os.path.join(outdir,"scenes");clips=os.path.join(outdir,"clips");os.makedirs(scenes);os.makedirs(clips)
    for i,(seg,cue) in enumerate(zip(story["script_segments"],cues)):
        asset=assets[seg["asset_id"]]; card=os.path.join(scenes,f"{i:02}.png");make_card(story,seg,asset,fontpath,card)
        duration=cue["duration"]+(0.24 if i<len(cues)-1 else 0)
        # Slow zoom and lateral crop movement prevent static-slide scenes.
        vf=f"scale=1200:2134,zoompan=z='min(zoom+0.00035,1.06)':d=1:x='iw/2-(iw/zoom/2)+sin(on/45)*15':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS},format=yuv420p"
        cmd=["ffmpeg","-y","-v","error","-loop","1","-framerate",str(FPS),"-t",f"{duration:.3f}","-i",card,"-vf",vf,"-an","-c:v","libx264","-preset","veryfast","-crf","20","-t",f"{duration:.3f}",os.path.join(clips,f"{i:02}.mp4")]
        subprocess.run(cmd,check=True)
    concat=os.path.join(outdir,"concat.txt")
    with open(concat,"w",encoding="utf-8") as f:
        for i in range(len(cues)): f.write(f"file '{os.path.join(clips,f'{i:02}.mp4')}'\n")
    picture=os.path.join(outdir,"picture.mp4")
    subprocess.run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",concat,"-c","copy",picture],check=True)
    ass=["[Script Info]","ScriptType: v4.00+","PlayResX: 1080","PlayResY: 1920","WrapStyle: 2","ScaledBorderAndShadow: yes","","[V4+ Styles]","Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding","Style: Default,Noto Sans SC,43,&H00FFFFFF,&H000000FF,&HCC07182D,&HBB07182D,1,0,0,0,100,100,0,0,3,2,1,2,84,84,185,1","","[Events]","Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text"]
    srt=[]
    for i,c in enumerate(cues,1):
        ass.append(f"Dialogue: 0,{ass_time(c['start'])},{ass_time(c['end'])},Default,,0,0,0,,{wrap_text(c['text'],ImageFont.truetype(fontpath,43),880)}")
        srt.extend([str(i),f"{srt_time(c['start'])} --> {srt_time(c['end'])}",c["text"],""])
    open(os.path.join(outdir,"captions.ass"),"w",encoding="utf-8").write("\n".join(ass)+"\n")
    open(os.path.join(outdir,"captions.srt"),"w",encoding="utf-8").write("\n".join(srt))
    final=os.path.join(outdir,"final.mp4");subtitles=os.path.join(outdir,"captions.ass").replace("\\","/").replace(":","\\:")
    fontsdir=fonts if os.path.isdir(fonts) else "/usr/share/fonts/opentype/noto"
    filt=f"subtitles='{subtitles}':fontsdir='{fonts}'"
    cmd=["ffmpeg","-y","-loglevel","verbose","-i",picture,"-i",os.path.join(outdir,"narration_yunxi.wav"),"-vf",filt,"-map","0:v:0","-map","1:a:0","-c:v","libx264","-preset","fast","-crf","20","-pix_fmt","yuv420p","-c:a","aac","-b:a","160k","-ar","48000","-shortest","-movflags","+faststart",final]
    result=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if result.returncode: raise subprocess.CalledProcessError(result.returncode,cmd,output=result.stdout,stderr=result.stderr[-6000:])
    if "Glyph 0x" in result.stderr or "failed to find any fallback" in result.stderr:
        raise RuntimeError("libass failed to find a CJK glyph; refusing to keep an unreadable subtitle render")
    if "HotspotVideoPipeline-NotoSansSC-VF.ttf" not in result.stderr:
        raise RuntimeError("libass did not confirm loading the registered Noto Sans SC font")
    print(final)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--story",required=True);p.add_argument("--assets",required=True);p.add_argument("--outdir",required=True);a=p.parse_args();main(a.story,a.assets,a.outdir)
