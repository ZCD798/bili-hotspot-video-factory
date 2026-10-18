#!/usr/bin/env python3
"""Generate Yunxi Mandarin audio and captions timed from actual decoded audio."""
import argparse, asyncio, json, os, ssl, subprocess, time, wave
import edge_tts
import edge_tts.communicate as communicate

VOICE="zh-CN-YunxiNeural"
# The Work runtime's bundled Python does not pick up the system CA bundle by
# default. Use the installed system trust store; certificate verification stays on.
SYSTEM_CA="/etc/ssl/certs/ca-certificates.crt"
if os.path.isfile(SYSTEM_CA): communicate._SSL_CTX=ssl.create_default_context(cafile=SYSTEM_CA)
async def run(story_file, outdir):
    story=json.load(open(story_file,encoding="utf-8")); audio_dir=os.path.join(outdir,"audio"); os.makedirs(audio_dir)
    t0=time.perf_counter(); cues=[]; request_count=0; params=None
    for i,seg in enumerate(story["script_segments"]):
        stem=f"{i:02d}_{seg['id']}"; mp3=os.path.join(audio_dir,stem+".mp3"); wavp=os.path.join(audio_dir,stem+".wav")
        for attempt in range(2):
            try:
                request_count+=1
                await edge_tts.Communicate(seg["text"],VOICE).save(mp3); break
            except Exception:
                if attempt: raise
                await asyncio.sleep(1)
        subprocess.run(["ffmpeg","-y","-v","error","-i",mp3,"-ar","24000","-ac","1","-c:a","pcm_s16le",wavp],check=True)
        with wave.open(wavp,"rb") as f:
            if params is None: params=f.getparams()
            n=f.getnframes(); duration=n/params.framerate
        cues.append({"index":i,"segment_id":seg["id"],"start":None,"end":None,"duration":duration,"text":seg["text"],"wav":os.path.relpath(wavp,outdir)})
    pause_frames=round(params.framerate*.24); cursor=0
    combined=os.path.join(outdir,"narration_yunxi.wav")
    with wave.open(combined,"wb") as out:
        out.setparams(params)
        for i,c in enumerate(cues):
            c["start"]=cursor/params.framerate
            with wave.open(os.path.join(outdir,c["wav"]),"rb") as f: data=f.readframes(f.getnframes())
            out.writeframes(data); cursor+=len(data)//(params.sampwidth*params.nchannels); c["end"]=cursor/params.framerate
            if i<len(cues)-1: out.writeframes(b"\0"*(pause_frames*params.sampwidth*params.nchannels));cursor+=pause_frames
    total=cursor/params.framerate
    meta={"voice":VOICE,"rate":"default","sample_rate":params.framerate,"duration":total,"request_count":request_count,"retry_limit_per_segment":1,"elapsed_seconds":round(time.perf_counter()-t0,3),"token_count":None,"cues":cues}
    json.dump(meta,open(os.path.join(outdir,"audio_timing.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
    return meta
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--story",required=True);p.add_argument("--outdir",required=True);a=p.parse_args();m=asyncio.run(run(a.story,a.outdir))
    print(json.dumps({k:m[k] for k in ("voice","duration","request_count","elapsed_seconds","token_count")},ensure_ascii=False))
