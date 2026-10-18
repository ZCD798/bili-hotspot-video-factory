#!/usr/bin/env python3
"""Structural/audio/subtitle QA for a topic-agnostic portrait video."""
import argparse, json, math, os, re, struct, subprocess, wave

def check(media, outdir, story_path):
    probe=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_streams","-show_format","-of","json",media]))
    v=next((x for x in probe["streams"] if x.get("codec_type")=="video"),None); a=next((x for x in probe["streams"] if x.get("codec_type")=="audio"),None)
    assert v and a,"missing video or audio stream"
    assert (int(v["width"]),int(v["height"]))==(1080,1920),f"wrong resolution: {v['width']}x{v['height']}"
    duration=float(probe["format"]["duration"]); assert 45<=duration<=75,f"duration outside 45-75s: {duration:.2f}"
    assert a["codec_name"]=="aac" and int(a["sample_rate"])==48000,"unexpected audio encoding"
    subprocess.run(["ffmpeg","-v","error","-i",media,"-f","null","-"],check=True)
    raw=subprocess.check_output(["ffmpeg","-v","error","-i",media,"-map","0:a:0","-ac","1","-ar","16000","-f","s16le","-"])
    samples=struct.unpack("<"+str(len(raw)//2)+"h",raw[:len(raw)//2*2]); rms=math.sqrt(sum(x*x for x in samples)/max(1,len(samples))); peak=max(map(abs,samples),default=0)
    assert rms>200 and peak>1000,"audio appears silent/test-tone-like"
    timing=json.load(open(os.path.join(outdir,"audio_timing.json"),encoding="utf-8")); assert timing["voice"]=="zh-CN-YunxiNeural"
    story=json.load(open(story_path,encoding="utf-8")); srt=open(os.path.join(outdir,"captions.srt"),encoding="utf-8").read(); ass=open(os.path.join(outdir,"captions.ass"),encoding="utf-8").read()
    assert srt.count(" --> ")==len(story["script_segments"]),"subtitle cue count mismatch"
    for seg in story["script_segments"]: assert seg["text"] in srt,f"subtitle missing segment {seg['id']}"
    assert "Noto Sans SC" in ass and ",185,1" in ass,"subtitle font or safe margin missing"
    # Confirm the video has nontrivial visual changes using decoded thumbnail frame fingerprints.
    frames=[]
    for sec in (2,duration*.25,duration*.5,duration*.75,duration-2):
        raw=subprocess.check_output(["ffmpeg","-v","error","-ss",str(max(0,sec)),"-i",media,"-frames:v","1","-vf","scale=32:56,format=gray","-f","rawvideo","-"])
        frames.append(raw)
    transitions=sum(a!=b for a,b in zip(frames,frames[1:])); assert transitions>=3,"sampled frames do not show enough visual change"
    result={"status":"passed","file":os.path.abspath(media),"container":probe["format"]["format_name"],"size_bytes":int(probe["format"]["size"]),"duration_seconds":duration,"video":{"codec":v["codec_name"],"width":int(v["width"]),"height":int(v["height"]),"fps":v.get("avg_frame_rate"),"pixel_format":v.get("pix_fmt")},"audio":{"codec":a["codec_name"],"sample_rate":a["sample_rate"],"channels":a["channels"],"duration_seconds":float(a["duration"]),"rms_s16":round(rms,1),"peak_s16":peak},"subtitle_cues":srt.count(" --> "),"caption_safe_margin": "ASS MarginV 185px", "visual_change_sample_pairs":transitions,"full_decode":"passed","voice":timing["voice"],"edge_tts_requests":timing["request_count"],"edge_tts_elapsed_seconds":timing["elapsed_seconds"],"token_count":"not available from Edge TTS"}
    json.dump(result,open(os.path.join(outdir,"qa_report.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2);return result
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--video",required=True);p.add_argument("--outdir",required=True);p.add_argument("--story",required=True);a=p.parse_args();print(json.dumps(check(a.video,a.outdir,a.story),ensure_ascii=False,indent=2))
