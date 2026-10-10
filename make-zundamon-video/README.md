# ずんだもん解説動画 Skill：独立再構成版

2026-10-10に制作した新規パッケージです。過去動画の元Skill・最終レンダラーの復元ではありません。利用者固有の台本・動画・素材は含みません。

## 含むものと含まないもの

- 企画、参考調査、20案、選定、会話・ナレーション・場面設計、素材調達、音声、字幕、動画、タイトル、サムネイル、概要、タグ、投稿前確認の手順
- ローカルVOICEVOX HTTP API／利用者音声から、WAV・SRT・相対パスのタイムラインを作るPythonコード
- 静止背景、人物画像の差分切替、汎用図形、三種の図、字幕をMP4にする最小実装
- サムネPNGと個別投稿用テキストの実出力

キャラ素材、VOICEVOXエンジン・音声モデル、フォント、BGM、他人の画像は同梱しません。音声モデルの導入や画像検索・画像生成をコードが自動実行するものではありません。ソフトの準備と利用条件確認が必要です。複雑な人物アクション、動的図解、動画挿入、BGMミックス、音素単位の口パクは未実装です。長尺の処理速度・全OS互換性は未測定です。

## 前提

Python 3.10以上、FFmpeg＋FFprobe（libx264/AACが使える構成）、Pillow、日本語対応のTrueType/OpenTypeフォント。音声生成する場合は、公式配布元から別途準備した対応VOICEVOXエンジンを同じ実行環境で起動します。既存音声のみなら不要です。Windows/macOS/Linuxで依存関係の用意の仕方は異なります。スマホからの入力だけでスマホ内部にこれらが使えるとは限りません。クラウドやPCを使う場合は、その環境とファイルへのアクセスを確認してください。

依存のインストールは利用者の環境・許可に従います。Pillowの依存宣言は `requirements.txt` にあります。自動インストーラはありません。

## 利用手順

ホストがローカルSkillフォルダに対応していれば、この `make-zundamon-video` フォルダをそのホスト指定のSkill置き場へ置きます。ホスト固有のインストール方法はそのホストで確認してください。導入済みとは自動的に扱いません。

まずこのフォルダで実行：

```sh
python scripts/pipeline.py doctor
python scripts/pipeline.py validate examples/project.json
python scripts/pipeline.py voices
```

`voices` は既に起動中の `http://127.0.0.1:50021` を読むだけです。別ポートなら `--engine http://127.0.0.1:PORT`。外部ホストへの送信はサポートしません。ホストPCのVOICEVOXは、別のクラウド環境のlocalhostではありません。

サンプルを自分の作業フォルダへコピーし、声の実名・スタイル、台本、素材、権利台帳を確認してから：

```sh
python scripts/pipeline.py audio examples/project.json --out build
python scripts/pipeline.py render examples/project.json --out build --font /path/to/japanese-font.ttf
python scripts/pipeline.py thumbnail examples/project.json --out build --font /path/to/japanese-font.ttf
python scripts/pipeline.py package examples/project.json --out build
ffprobe -v error -show_streams -show_format build/video.mp4
ffmpeg -v error -i build/video.mp4 -f null -
```

`/path/to/japanese-font.ttf` は実在する日本語フォントへ置き換えます。フォントファイルの再配布は別途条件を確認してください。幅のある文字は行を分け、字幕は一発話を短くしてください。文字領域を超える場合、動画描画はエラーで止まり、不完全なMP4を除きます。

`audio` は音声を標準形式へ変換し、`build/clips` をキャッシュに使います。完成出力は同名なら上書きされるため、案件ごとに別の `--out` を指定してください。表示台本等を変えたら音声工程からやり直してください。既存キャッシュが不正なら利用者が該当クリップを手動で別名に退避し、再生成してください（自動修復はありません）。再配布する編集素材は許可されたものだけにし、元projectと素材フォルダ、buildを相対位置を保ってまとめてください。

## 動作テスト

```sh
python -m unittest discover -s tests -v
python tests/smoke.py --font /path/to/japanese-font.ttf --out /tmp/video-skill-smoke
```

smokeテストは合成した正弦波を使います。人声・VOICEVOXの発声テストではありません。結果の動画にも「音声合成未検証」と表示します。本番の発音・声質・アクセント・権利の検証には代用できません。

実施した確認と未検証範囲は `TEST_REPORT.md` に記載しています。

## 権利と公開

本パッケージのコード・文書に対するライセンスは作者の決定待ちです。このパッケージは利用許諾の付与を表しません。配布・改変・再配布の条件を作者が確定するまでは、無制限の利用や再配布が許可されたとは扱わないでください。第三者のキャラ・声・画像・フォント等の条件は別です。`references/assets-and-rights.md` を確認してください。動画を作れることと、特定の宣伝・商用用途で利用できることは別です。
