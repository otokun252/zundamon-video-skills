# project.json v1

UTF-8のJSON。パスはproject.jsonのあるフォルダからの相対パス。絶対パス、親ディレクトリへの参照は不可。すべての発話を順番に並べ、固定時刻を入力せず、実音声で時刻を確定する。

- `schema_version`: 1
- `title`, `description`, `tags`: 投稿用のタイトル・概要・タグ配列
- `width`, `height`, `fps`: 偶数の320〜3840px、1〜60fps。横1280×720・24fpsがサンプル
- `characters`: 役IDから役情報への辞書。`name`, `role`（narrator等）, `voice_name`, `voice_style`, `color`
- 任意の人物画像：`image`, `mouth_open_image`, `eyes_closed_image`。透過PNG推奨。同じ寸法・位置を揃える。描画コードは画像全体を切り替えるので、差分がずれていると揺れる。口パクは音量ベースで、音素対応ではない。目閉じ差分は非発声時に使う
- `scenes`: 場面IDから場面情報への辞書。`title`, `background`色、任意の背景`image`, `visible`（その場面に出る役ID、0〜3人）, `kind`（cards/steps/bars）, `items`（最大4個）
- cards/stepsのitemsは短文配列。barsのみ `{"label":"表示","value":0.6}` の配列。valueは0〜1の表示比率。根拠のない比較値を作らない
- `utterances`: `speaker`（音声役ID）, `scene`, `display_text`, `speech_text`, 任意の`gap_after`（0〜5秒、初期0.2）
- 既存音声を使う発話には `audio`: `audio/001.wav` 等を指定。FFmpegでモノラル24kHzに変換する。音声を持つ発話はVOICEVOXへ送らない
- `speech_text`が無い場合は表示文を読み上げるが警告を出す。本制作では全発話に確認済みの音声文を入れる。表示文とは別に管理する
- `credits`: 実際に使用した音声・素材のクレジット配列
- `assets`: 出典台帳。権利資料を参照。クレジットはcreditsと重複除去して出力
- `thumbnail`: `lines`（1〜3行の短い文字）、任意の`image`（右側へトリミングする画像）。1280×720の固定レイアウトで出力。人物の顔が切れないよう出力を確認する

ナレーターを `speaker` にし、scene.visibleに含めなければ、音声と黄色字幕だけを出せる。人物IDと声名を別にすることで、同じ声の複数役、または役に合わせた異なる声に対応する。登場キャラの公式設定や声の利用条件は別途確認する。

出力：`dialogue.wav`, `timeline.json`, `captions.srt`, `video.mp4`, `preview-*.png`, `thumbnail.png`, `thumbnail-mobile-preview.png`, `title.txt`, `description.txt`, `tags.txt`, `chapters.txt`, `credits.txt`, `asset-ledger.json`, `upload-checklist.txt`。台本を変えたらaudioから実行する。字幕は発話単位で、単語単位ハイライトはない。
