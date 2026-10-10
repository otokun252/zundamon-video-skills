"""Integration check with synthetic tones only; no VOICEVOX install or voice claim."""
import argparse
import array
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import wave

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--font',required=True);p.add_argument('--out',required=True);args=p.parse_args()
out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=True)
script=ROOT/'scripts/pipeline.py'
def run(*a):subprocess.run([sys.executable,str(script),*map(str,a)],check=True)
results=[]
for name,w,h in [('landscape',960,540),('portrait',540,960)]:
    work=out/name;work.mkdir(exist_ok=True)
    project=json.loads((ROOT/'examples/project.json').read_text())
    project.update(width=w,height=h,fps=12,title='合成音テスト：音声合成未検証',credits=['合成正弦波と汎用図形によるテスト。VOICEVOX音声ではありません。'])
    for i,u in enumerate(project['utterances']):
        f=work/f'{i}.wav';samples=array.array('h',(int(5000*math.sin(2*math.pi*(220+40*i)*n/24000)) if n<15000 else 0 for n in range(18000)))
        if sys.byteorder!='little':samples.byteswap()
        with wave.open(str(f),'wb') as wf:wf.setparams((1,2,24000,0,'NONE','not compressed'));wf.writeframes(samples.tobytes())
        u['audio']=f.name;u['display_text']='音声合成未検証。合成音のテストです。';u['speech_text']='おんせいごうせいみけんしょう。'
    project_path=work/'project.json';project_path.write_text(json.dumps(project,ensure_ascii=False),encoding='utf-8')
    build=work/'build'
    run('validate',project_path)
    run('audio',project_path,'--out',build)
    run('render',project_path,'--out',build,'--font',args.font)
    run('thumbnail',project_path,'--out',build,'--font',args.font)
    run('package',project_path,'--out',build)
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(build/'video.mp4')]))
    v=next(s for s in probe['streams'] if s['codec_type']=='video');a=next(s for s in probe['streams'] if s['codec_type']=='audio')
    assert (v['width'],v['height'])==(w,h)
    assert a['codec_name']=='aac'
    subprocess.run(['ffmpeg','-v','error','-i',str(build/'video.mp4'),'-f','null','-'],check=True)
    timeline=json.loads((build/'timeline.json').read_text());assert all(not Path(u['clip']).is_absolute() for u in timeline['utterances'])
    assert '音声合成未検証' in (build/'captions.srt').read_text()
    for file in ['title.txt','description.txt','tags.txt','chapters.txt','credits.txt','thumbnail.png']:
        assert (build/file).stat().st_size>0
    # Confirm relative-path inputs work after relocation, with no engine running.
    moved=out/(name+'-relocated');shutil.copytree(work,moved,dirs_exist_ok=True)
    run('audio',moved/'project.json','--out',moved/'build')
    results.append({'orientation':name,'width':w,'height':h,'duration':probe['format']['duration'],'video_codec':v['codec_name'],'audio_codec':a['codec_name'],'complete_decode':'pass','portable_audio':'pass','real_voicevox':'not tested'})
(out/'results.json').write_text(json.dumps(results,indent=2),encoding='utf-8');print(json.dumps(results,indent=2))
