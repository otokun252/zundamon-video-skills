# 素材と権利

このパッケージは第三者素材や音声モデルを含まない。利用条件は音声ソフト、音源、キャラクター、立ち絵作者、背景、BGM、フォントで分けて確認する。無料の素材でも商用・加工・配布・クレジットの条件がある。規約の要約を法的適合の保証としない。

## 入手手順

1. 場面に必要な「場所、物、人物、表情、行動」を列挙する。
2. 利用者所有の素材を確認し、足りなければ公式配布元やフリー素材提供元を探す。
3. 使用する実ファイルに適用される規約を読み、商用利用、加工、動画への組込み、素材そのものの再配布、クレジット、禁止用途を確認する。出典ページURL、作者、規約URL、取得日、用途、確認状態を記録する。
4. 条件が不明・用途に不適合なら取得済みでも使わず、別素材または画像生成を検討する。生成の場合もサービス条件と描くキャラの条件を確認する。第三者キャラを生成すれば無条件に自由になるわけではない。
5. プロジェクト用素材と配布用Skillを分離する。動画への組込みが許可されても、元PNGや編集ZIPへの同梱が許可されるとは限らない。

## 確認先（利用時に最新を読む）

- VOICEVOX公式：https://voicevox.hiroshiba.jp/term/
- VOICEVOXエンジン・HTTP API：https://github.com/VOICEVOX/voicevox_engine
- 音声モデル規約：https://github.com/VOICEVOX/voicevox_vvm/blob/main/TERMS.txt
- ずんだもん・四国めたん等の音源：https://zunko.jp/con_ongen_kiyaku.html
- キャラクターガイドライン：https://zunko.jp/guideline.html
- 春日部つむぎ：https://tsumugi-official.studio.site/rule
- いらすとや：https://www.irasutoya.com/p/terms.html
- みんちりえ：https://min-chi.material.jp/

公式VOICEVOX利用規約・エンジンREADME・キャラクターガイドラインのページは2026-10-10に確認した。各作品の具体的な素材・用途について許可を得たという意味ではない。VOICEVOX音声には規約に従ったクレジットを付け、音源ごとの条件も確認する。キャラを使った商品宣伝、販売導線、情報商材等の用途は一般的な動画利用と同じと決めつけない。

## assets台帳の例

```json
{
  "id": "desk-background",
  "path": "media/desk.png",
  "origin": "user-owned",
  "source": "利用者が提供した画像",
  "author": "実際の作者名",
  "terms_url": "確認した規約のURLまたは所有根拠",
  "acquired_date": "2026-10-10",
  "usage": "本編の机の場面、サムネイル",
  "rights_status": "reviewed-for-this-use",
  "redistributable": false,
  "credit": "実際に必要なクレジット"
}
```

この例のまま作者名や権利を確定しない。画像生成の場合は origin を `generated`、source に利用ツールと生成記録の参照、確認した利用条件を記録する。`package` は台帳を転記するが、法的条件を自動判定しない。公開前に人が確認する。
