#!/usr/bin/env python3
"""Small, local character-dialogue video pipeline. No models or media downloads."""
import argparse
import array
import hashlib
import io
import json
import math
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
import wave

RATE = 24000


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def local_file(root, value):
    p = Path(value)
    if p.is_absolute() or '..' in p.parts:
        raise ValueError('Asset paths must be project-relative without ..')
    result = (root / p).resolve()
    if not result.is_relative_to(root.resolve()):
        raise ValueError('Asset escapes project directory')
    if not result.is_file():
        raise ValueError(f'Missing asset: {value}')
    return result


def check_project(path):
    p = read_json(path)
    if p.get('schema_version') != 1:
        raise ValueError('schema_version must be 1')
    for key in ('title', 'characters', 'scenes', 'utterances'):
        if not p.get(key):
            raise ValueError(f'Missing {key}')
    w, h = p.get('width', 1280), p.get('height', 720)
    fps = p.get('fps', 24)
    if any(type(v) is not int for v in (w, h, fps)) or min(w, h) < 320 or max(w, h) > 3840 or w % 2 or h % 2 or not 1 <= fps <= 60:
        raise ValueError('Use even 320..3840 dimensions and integer 1..60 fps')
    root = Path(path).resolve().parent
    if not isinstance(p.get('description', ''), str) or not isinstance(p.get('tags', []), list) or any(not isinstance(t, str) for t in p.get('tags', [])):
        raise ValueError('description must be text and tags must be a list of text')
    if p.get('thumbnail', {}).get('image'): local_file(root, p['thumbnail']['image'])
    for cid, c in p['characters'].items():
        if not c.get('name'):
            raise ValueError(f'Character {cid} needs name')
        for k in ('image', 'mouth_open_image', 'eyes_closed_image'):
            if c.get(k):
                local_file(root, c[k])
    for asset in p.get('assets', []):
        if asset.get('path'): local_file(root, asset['path'])
        if not all(asset.get(k) for k in ('id', 'origin', 'source', 'rights_status', 'credit')):
            raise ValueError('Assets require id, origin, source, rights_status and credit')
    for sid, scene in p['scenes'].items():
        if scene.get('image'): local_file(root, scene['image'])
        if scene.get('kind', 'cards') not in ('cards', 'steps', 'bars'):
            raise ValueError(f'Unknown scene kind: {sid}')
        if len(scene.get('visible', [])) > 3 or any(c not in p['characters'] for c in scene.get('visible', [])):
            raise ValueError('Scene visible must contain up to 3 known characters')
        if len(scene.get('items', [])) > 4:
            raise ValueError('At most four diagram items per scene')
        if scene.get('kind') == 'bars':
            for item in scene.get('items', []):
                if not isinstance(item.get('value'), (float, int)) or not math.isfinite(item['value']) or not 0 <= item['value'] <= 1:
                    raise ValueError('Bar value must be a finite number in 0..1')
    for u in p['utterances']:
        if u.get('speaker') not in p['characters'] or u.get('scene') not in p['scenes'] or not u.get('display_text', '').strip():
            raise ValueError('Every utterance needs known speaker, scene and nonempty text')
        if u.get('speech_text') is not None and not isinstance(u['speech_text'], str):
            raise ValueError('speech_text must be text or omitted')
        gap = u.get('gap_after', 0.2)
        if not isinstance(gap, (int, float)) or not math.isfinite(gap) or not 0 <= gap <= 5:
            raise ValueError('gap_after must be finite and 0..5 seconds')
        if u.get('audio'):
            local_file(root, u['audio'])
    return p


def endpoint(url):
    u = urllib.parse.urlsplit(url)
    if u.scheme != 'http' or u.hostname not in ('127.0.0.1', 'localhost', '::1') or u.username or u.password or u.path not in ('', '/') or u.query or u.fragment:
        raise ValueError('Only a local loopback HTTP VOICEVOX endpoint is supported')
    return url.rstrip('/')


def api(base, route, query=None, body=None, post=False):
    url = endpoint(base) + route
    if query:
        url += '?' + urllib.parse.urlencode(query)
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else (b'' if post else None), headers={'Content-Type': 'application/json'})
    # Do not send the script through configured network proxies or follow redirects.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    with opener.open(req, timeout=180) as r:
        return r.read()


def normalize(src, target):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-protocol_whitelist', 'file,pipe', '-i', str(src), '-ar', str(RATE), '-ac', '1', '-c:a', 'pcm_s16le', str(target)], check=True)


def wav_data(path):
    with wave.open(str(path), 'rb') as f:
        if (f.getnchannels(), f.getsampwidth(), f.getframerate()) != (1, 2, RATE):
            raise ValueError('Expected mono 24kHz PCM16 WAV')
        return f.readframes(f.getnframes())


def wav_write(path, data):
    with wave.open(str(path), 'wb') as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(RATE); f.writeframes(data)


def stamp(t, sep=','):
    ms = round(t * 1000)
    return f'{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02}{sep}{ms % 1000:03}'


def audio(args):
    p = check_project(args.project)
    root = Path(args.project).resolve().parent
    out = Path(args.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    cache = out / 'clips'; cache.mkdir(exist_ok=True)
    speakers = None
    chunks, timeline, cursor = [], [], 0
    for i, u in enumerate(p['utterances']):
        c = p['characters'][u['speaker']]
        if u.get('audio'):
            source = local_file(root, u['audio'])
            key = hashlib.sha256(source.read_bytes()).hexdigest()
        else:
            if speakers is None:
                speakers = json.loads(api(args.engine, '/speakers'))
            match = [s for s in speakers if s['name'] == c.get('voice_name')]
            styles = [st for s in match for st in s['styles'] if st['name'] == c.get('voice_style', 'ノーマル')]
            if len(styles) != 1:
                raise ValueError(f'Voice/style not found uniquely for {c["name"]}; run voices and set exact names')
            style = styles[0]['id']
            tts = u.get('speech_text') or u['display_text']
            if not u.get('speech_text'):
                print(f'WARNING: utterance {i+1}: speech_text missing; display_text used. Review readings.', file=sys.stderr)
            # Include engine version, exact style and text in cache identity.
            version = json.loads(api(args.engine, '/version'))
            key = hashlib.sha256(json.dumps([version, style, tts], ensure_ascii=False).encode()).hexdigest()
            source = cache / f'{key}.source.wav'
            if not source.exists():
                q = json.loads(api(args.engine, '/audio_query', {'text': tts, 'speaker': style}, post=True))
                data = api(args.engine, '/synthesis', {'speaker': style}, q)
                with wave.open(io.BytesIO(data), 'rb') as f:
                    if f.getnframes() == 0:
                        raise ValueError('VOICEVOX returned empty WAV')
                source.write_bytes(data)
        normalized = cache / f'{key}.wav'
        if not normalized.exists():
            normalize(source, normalized)
        data = wav_data(normalized)
        if not data:
            raise ValueError('Empty audio clip')
        n = len(data) // 2
        gap = round(u.get('gap_after', 0.2) * RATE)
        timeline.append({**u, 'start': cursor / RATE, 'end': (cursor + n) / RATE, 'next': (cursor + n + gap) / RATE, 'clip': normalized.relative_to(out).as_posix()})
        chunks += [data, b'\0\0' * gap]; cursor += n + gap
    wav_write(out / 'dialogue.wav', b''.join(chunks))
    # Keep project unchanged; timeline paths are portable relative to output directory.
    write_json(out / 'timeline.json', {'schema_version': 1, 'duration': cursor / RATE, 'audio': 'dialogue.wav', 'utterances': timeline})
    srt = '\n'.join(f'{i+1}\n{stamp(u["start"])} --> {stamp(u["end"])}\n{u["display_text"]}\n' for i, u in enumerate(timeline))
    (out / 'captions.srt').write_text(srt, encoding='utf-8')
    print(f'Audio and subtitles: {out}; {cursor / RATE:.3f}s')


def check_timeline(p, tl):
    if len(tl['utterances']) != len(p['utterances']) or any(any(a.get(k) != b.get(k) for k in ('display_text', 'speaker', 'scene', 'speech_text', 'audio', 'gap_after')) for a, b in zip(tl['utterances'], p['utterances'])):
        raise ValueError('Project dialogue changed; regenerate audio before render or metadata export')

def render(args):
    from PIL import Image, ImageDraw, ImageFont
    p = check_project(args.project)
    root = Path(args.project).resolve().parent
    out = Path(args.out).resolve()
    tl = read_json(out / 'timeline.json')
    check_timeline(p, tl)
    w, h, fps = p.get('width', 1280), p.get('height', 720), p.get('fps', 24)
    font_path = Path(args.font)
    if not font_path.is_file():
        raise ValueError('Supply an installed Japanese-capable .ttf/.otf/.ttc via --font')
    scale = min(w, h) / 720
    font = lambda size: ImageFont.truetype(str(font_path), max(12, round(size * scale)))
    def box_text(draw, text, box, size, fill='white'):
        x, y, bw, bh = box
        f = font(size); lines, line = [], ''
        for ch in text:
            if ch == '\n' or draw.textlength(line + ch, font=f) > bw:
                lines.append(line); line = '' if ch == '\n' else ch
            else:
                line += ch
        if line:
            lines.append(line)
        line_h = round(size * scale * 1.5)
        if len(lines) * line_h > bh:
            raise ValueError(f'Text overflow; shorten text or split scene: {text[:35]}')
        for n, line in enumerate(lines):
            draw.text((x, y + n * line_h), line, font=f, fill=fill)
    images = {}
    for cid, c in p['characters'].items():
        for k in ('image', 'mouth_open_image', 'eyes_closed_image'):
            if c.get(k):
                images[(cid, k)] = Image.open(local_file(root, c[k])).convert('RGBA')
    samples = array.array('h', wav_data(out / tl['audio']))
    if sys.byteorder != 'little':
        samples.byteswap()
    frames = math.ceil(tl['duration'] * fps)
    cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w}x{h}', '-r', str(fps), '-i', '-', '-i', str(out / tl['audio']), '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', '-t', str(tl['duration']), str(out / 'video.mp4')]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    idx = 0
    try:
        for frame in range(frames):
            t = frame / fps
            while idx + 1 < len(tl['utterances']) and t >= tl['utterances'][idx]['next']:
                idx += 1
            u = tl['utterances'][idx]; scene = p['scenes'][u['scene']]
            im = Image.new('RGB', (w, h), scene.get('background', '#112035'))
            if scene.get('image'):
                from PIL import ImageOps
                bg = ImageOps.fit(Image.open(local_file(root, scene['image'])).convert('RGB'), (w,h))
                im = Image.blend(bg, im, .35)
            d = ImageDraw.Draw(im)
            pad = int(min(w, h) * .05)
            box_text(d, scene.get('title', p['title']), (pad, pad, w - 2*pad, h*.17), 38)
            items = scene.get('items', [])
            top, bottom = int(h*.23), int(h*.49)
            step = (bottom-top) / max(1, len(items))
            for j, item in enumerate(items):
                y = top + j*step
                label = item if isinstance(item, str) else item['label']
                if scene.get('kind') == 'steps':
                    label = f'{j+1}. ' + label
                d.rounded_rectangle((pad, y, w-pad, y+step*.88), radius=8, fill='#253c59')
                if scene.get('kind') == 'bars':
                    d.rectangle((pad, y+step*.72, pad+(w-2*pad)*item['value'], y+step*.87), fill='#52b5c8')
                box_text(d, label, (pad+10, y, w-2*pad-20, step*.72), 22)
            visible = scene.get('visible', [])
            for j, cid in enumerate(visible):
                c = p['characters'][cid]; cell = (w-2*pad)/max(1,len(visible)); cx = int(pad+cell*(j+.5)); cy = int(h*.62)
                segment = samples[int(t*RATE):int((t+.035)*RATE)]
                energy = math.sqrt(sum(v*v for v in segment)/max(1,len(segment)))
                speaking = cid == u['speaker'] and t < u['end'] and energy > 500
                blink = (frame + j*19) % (fps*4) < max(1, fps//8)
                k = 'mouth_open_image' if speaking and (cid, 'mouth_open_image') in images else 'image'
                if blink and not speaking and (cid, 'eyes_closed_image') in images: k='eyes_closed_image'
                if (cid, k) in images:
                    pic = images[(cid,k)].copy(); pic.thumbnail((int(cell*.85), int(h*.22)))
                    im.paste(pic, (cx-pic.width//2, int(h*.51)), pic)
                else:
                    radius = max(18, int(min(cell*.16, h*.065)))
                    d.ellipse((cx-radius, cy-radius, cx+radius, cy+radius), fill=c.get('color','#88b9db'))
                    blink = (frame + j*19) % (fps*4) < max(1, fps//8)
                    for dx in (-radius*.35, radius*.35):
                        d.line((cx+dx-2,cy-radius*.15,cx+dx+2,cy-radius*.15),fill='#112035',width=3 if blink else 6)
                    d.ellipse((cx-radius*.25,cy+radius*.23,cx+radius*.25,cy+radius*(.65 if speaking else .29)),fill='#112035')
                box_text(d,c['name'],(pad+j*cell,int(h*.72),cell-8,h*.055),20)
            d.rectangle((0,int(h*.79),w,h),fill='#071321')
            if t < u['end']:
                name = p['characters'][u['speaker']]['name']
                box_text(d,name,(pad,int(h*.805),w-2*pad,h*.05),19,fill='#b4dbef')
                box_text(d,u['display_text'],(pad,int(h*.85),w-2*pad,h*.14),28,fill='#ffe28d' if p['characters'][u['speaker']].get('role')=='narrator' else 'white')
            if frame == 0 or (idx and abs(t-u['start']) < 1/fps):
                im.save(out / f'preview-{idx:03}.png')
            proc.stdin.write(im.tobytes())
        proc.stdin.close()
        if proc.wait() != 0:
            raise RuntimeError('FFmpeg render failed')
    except BaseException:
        proc.kill(); proc.wait()
        (out / 'video.mp4').unlink(missing_ok=True)
        raise
    print(out / 'video.mp4')


def package(args):
    p = check_project(args.project); out=Path(args.out)
    tl=read_json(out/'timeline.json')
    check_timeline(p, tl)
    chapters=[]; seen=set()
    for u in tl['utterances']:
        sid=u['scene']
        if sid not in seen:
            seen.add(sid); seconds=int(u['start'])
            chapters.append(f'{seconds//60:02}:{seconds%60:02} {p["scenes"][sid].get("title",sid)}')
    credits = list(dict.fromkeys(p.get('credits', []) + [a['credit'] for a in p.get('assets', [])]))
    for name, value in [('title.txt',p['title']), ('description.txt',p.get('description','')), ('tags.txt',', '.join(p.get('tags',[]))), ('chapters.txt','\n'.join(chapters)), ('credits.txt','\n'.join(credits))]:
        (out/name).write_text(value+'\n',encoding='utf-8')
    write_json(out/'asset-ledger.json',p.get('assets',[]))
    (out/'upload-checklist.txt').write_text('公開前に確認：実音声の読み／字幕切れ／根拠／素材と音声の権利／クレジット／サムネとの一致／個人情報。章は候補です。短尺では公開先の章条件を満たさない場合があります。アップロードは利用者が行います。\n',encoding='utf-8')
    print('Metadata written:', out)


def thumbnail(args):
    from PIL import Image, ImageDraw, ImageFont, ImageOps
    p=check_project(args.project); root=Path(args.project).resolve().parent
    out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
    spec=p.get('thumbnail',{})
    im=Image.new('RGB',(1280,720),'#13273d')
    if spec.get('image'):
        pic=ImageOps.fit(Image.open(local_file(root,spec['image'])).convert('RGB'),(570,620))
        im.paste(pic,(660,50))
    else:
        d=ImageDraw.Draw(im)
        d.rounded_rectangle((720,100,1150,620),radius=40,fill='#55c3b6')
        d.rectangle((800,220,1070,500),fill='#13273d')
    d=ImageDraw.Draw(im)
    lines=spec.get('lines',[p['title']])
    if not 1 <= len(lines) <= 3: raise ValueError('Thumbnail requires 1..3 short lines')
    f=ImageFont.truetype(args.font,72)
    for i,line in enumerate(lines):
        if d.textlength(line,font=f)>560: raise ValueError('Thumbnail line too long; use shorter wording')
        d.text((60,150+i*110),line,font=f,fill='#fff4cf',stroke_width=1)
    im.save(out/'thumbnail.png')
    im.resize((320,180)).save(out/'thumbnail-mobile-preview.png')
    print(out/'thumbnail.png')


def doctor(args):
    print(json.dumps({'python':platform.python_version(),'os':platform.system(),'architecture':platform.machine(),'ffmpeg':shutil.which('ffmpeg'),'ffprobe':shutil.which('ffprobe'),'pillow':__import__('importlib.util',fromlist=['find_spec']).find_spec('PIL') is not None,'voicevox':'Not checked; run voices against your already-started local engine'},indent=2))


def main():
    ap=argparse.ArgumentParser(description=__doc__); sub=ap.add_subparsers(dest='command',required=True)
    sub.add_parser('doctor').set_defaults(run=doctor)
    vo=sub.add_parser('voices'); vo.add_argument('--engine',default='http://127.0.0.1:50021'); vo.set_defaults(run=lambda a:print(api(a.engine,'/speakers').decode()))
    for name,func in [('validate',lambda a:print('Project valid:',check_project(a.project)['title'])),('audio',audio),('render',render),('package',package),('thumbnail',thumbnail)]:
        sp=sub.add_parser(name);sp.add_argument('project');sp.add_argument('--out',default='build');sp.set_defaults(run=func)
        if name=='audio':sp.add_argument('--engine',default='http://127.0.0.1:50021')
        if name in ('render','thumbnail'):sp.add_argument('--font',required=True)
    args=ap.parse_args();args.run(args)


if __name__=='__main__':
    try:main()
    except (ValueError,OSError,subprocess.CalledProcessError) as e:
        print(f'Error: {e}',file=sys.stderr);sys.exit(1)
