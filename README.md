# ずんだもん解説動画 Skills

企画から台本・音声・字幕・動画・投稿準備までを整理した、2026-10-10制作の独立再構成版です。

**過去動画の元Skill・最終レンダラーそのものではありません。** 公開用に作り直した最小実装で、過去動画の再生実績を再現・保証するものでもありません。**実VOICEVOXの人声合成は未検証**です。動画テストには模擬APIと合成した正弦波を使っています。

## はじめる

1. リポジトリの「Code」→「Download ZIP」で取得し、展開します。
2. `make-zundamon-video` フォルダ内の [README](make-zundamon-video/README.md) を読み、Python・FFmpeg・Pillow・日本語フォント等を準備します。
3. ローカルSkillフォルダを扱えるホストでは、`make-zundamon-video` フォルダ全体をホスト指定の置き場へ配置します。チャットにリンクを貼るだけで導入されたことにはなりません。
4. [SKILL.md](make-zundamon-video/SKILL.md) の進め方と、[検証記録](make-zundamon-video/TEST_REPORT.md)・[素材と権利](make-zundamon-video/references/assets-and-rights.md) を確認してください。

キャラ素材、音声モデル、フォント、BGM、過去動画や個人用の台本は含みません。Windows・macOS・スマホでの実行、長尺の安定性、実音声の発音・声質は未確認です。

## ライセンス

コード・文書の利用許諾は作者の決定待ちです。公開されていることだけで、無制限の利用・改変・再配布が許可されたとは扱わないでください。第三者素材の利用条件は別途確認が必要です。
