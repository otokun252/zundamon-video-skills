import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import argparse
import io
import wave
import shutil

ROOT = Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('pipeline',ROOT/'scripts/pipeline.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)

class Tests(unittest.TestCase):
    def test_example(self):
        project=p.check_project(ROOT/'examples/project.json')
        self.assertEqual(project['scenes']['diagram']['visible'],[])
        self.assertEqual(len(project['characters']),4)
        self.assertNotEqual(project['utterances'][0]['display_text'],project['utterances'][0]['speech_text'])
    def test_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            for path in ('../secret','/etc/passwd'):
                with self.assertRaises(ValueError):p.local_file(Path(tmp),path)
    def test_endpoint(self):
        self.assertEqual(p.endpoint('http://127.0.0.1:50021/'),'http://127.0.0.1:50021')
        for url in ('https://example.com','http://localhost@evil.com','http://127.0.0.1:50021/else'):
            with self.assertRaises(ValueError):p.endpoint(url)
    def test_time(self):
        self.assertEqual(p.stamp(61.25),'00:01:01,250')
    def test_invalid(self):
        project=p.read_json(ROOT/'examples/project.json');project['utterances'][0]['gap_after']=-1
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'project.json';p.write_json(path,project)
            with self.assertRaises(ValueError):p.check_project(path)

    def test_speech_and_display_separated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);project=p.read_json(ROOT/'examples/project.json')
            project['utterances']=project['utterances'][:1]
            project['utterances'][0].update(display_text='ChatGPTで月3万円',speech_text='ちゃっとじーぴーてぃーでつきさんまんえん')
            path=root/'project.json';p.write_json(path,project)
            buf=io.BytesIO()
            with wave.open(buf,'wb') as w:
                w.setparams((1,2,24000,0,'NONE','not compressed'));w.writeframes(b'\0\0'*2400)
            received=[]
            def fake_api(base,route,query=None,body=None,post=False):
                if route=='/speakers':return json.dumps([{'name':'ずんだもん','styles':[{'name':'ノーマル','id':3}]}]).encode()
                if route=='/version':return b'"mock-only"'
                if route=='/audio_query':received.append(query['text']);return b'{}'
                if route=='/synthesis':return buf.getvalue()
                raise AssertionError(route)
            with patch.object(p,'api',fake_api),patch.object(p,'normalize',lambda a,b:shutil.copyfile(a,b)):
                p.audio(argparse.Namespace(project=str(path),out=str(root/'build'),engine='http://127.0.0.1:50021'))
            self.assertEqual(received,['ちゃっとじーぴーてぃーでつきさんまんえん'])
            self.assertIn('ChatGPTで月3万円',(root/'build/captions.srt').read_text())
            self.assertNotIn('ちゃっと',(root/'build/captions.srt').read_text())
            tl=p.read_json(root/'build/timeline.json')
            project['utterances'][0]['display_text']='changed'
            with self.assertRaises(ValueError):p.check_timeline(project,tl)

if __name__=='__main__':unittest.main()
