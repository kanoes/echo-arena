# echo-arena

テキスト型TRPG（テーブルトークRPG）サンドボックスシステム

## プロジェクト概要

「EchoArena」は、プレイヤーと複数のAIキャラクターが自然言語で自由にやり取りできる、軽量なテキスト型TRPGシミュレーターです。ChatGPTによって駆動される各キャラクターは、感情・親密度・行動などの状態が動的に変化し、プレイヤーとの対話に応じて独自の記憶を形成します。

ゲーム没入感の提供だけでなく、大規模ゲーム開発でのAI挙動のテストやPrompt設計の検証にも使えるプロトタイピングプラットフォームとして機能します。

## 特徴

- 🤖 **AIキャラクター**: ChatGPTを活用した自然な対話と感情表現
- 🧠 **記憶システム**: キャラクターごとの短期・長期記憶
- 🌍 **ダイナミックな世界**: 時間経過や天候変化に対応
- 🔄 **状態変化**: 感情や関係性が対話によって変化
- 🎭 **自由な世界設定**: 独自の世界やキャラクターを追加可能

## インストール方法

1. リポジトリをクローン:

```
git clone https://github.com/yourusername/echo-arena.git
cd echo-arena
```

2. 依存パッケージをインストール:

```
pip install -r requirements.txt
```

3. `.env`ファイルを作成し、OpenAI APIキーを設定:

```
OPENAI_API_KEY=your_api_key_here
DEFAULT_MODEL=gpt-4-turbo
DEFAULT_TEMPERATURE=0.7
MAX_TOKENS=4096
LOG_LEVEL=INFO
```

> **重要**: 本システムでは各キャラクターに対して個別のOpenAI APIキーを設定する必要があります。キャラクター作成時に、そのキャラクター専用のAPIキーを指定してください。環境変数のAPIキーはサンプルキャラクター用として使用されます。

## 使い方

1. アプリケーションを起動:

```
python main.py
```

2. ブラウザが自動的に開き、Streamlitインターフェースが表示されます
3. サイドバーで名前、世界設定、キャラクターを選択
4. テキスト入力フィールドでキャラクターと会話を開始

### 基本的なコマンド例

- キャラクターとの会話: `こんにちは、アリス。魔法について教えてください。`
- 移動: `中央広場に行く`
- 調査: `この部屋を調べる` または `アリスについて観察する`
- アイテム使用: `水筒を使う`

## プロジェクト構成

```bash
echoarena/
├── app.py                    # Streamlit エントリポイント（メインUI）
├── main.py                   # メインロジックのエントリポイント
├── config/
│   └── settings.py           # 各種設定（APIキー、パス、パラメータ）
├── core/
│   ├── models/               # モデル定義（データ構造）
│   │   ├── player.py         # プレイヤーモデル
│   │   ├── character.py      # NPCキャラクター（状態・記憶など）
│   │   ├── world.py          # 世界・環境の状態（天気、時間など）
│   │   └── enums.py          # 列挙型（感情タイプ、行動タイプなど）
│   ├── logic/
│   │   ├── state_tracker.py  # 状態追跡・更新ロジック
│   │   ├── memory_manager.py # 記憶・履歴管理（短期/長期）
│   │   └── action_router.py  # プレイヤー入力→意図解析→対象ルーティング
├── prompts/
│   ├── base_prompt_template.txt      # ベースプロンプトのテンプレート
│   ├── prompt_builder.py             # プロンプト構築ロジック
│   └── response_parser.py            # LLMレスポンスの解析モジュール
├── services/
│   └── llm_client.py                 # OPENAI API呼び出しラッパー
├── ui/
│   ├── sidebar.py                    # サイドバーUI（初期設定）
│   ├── interaction_panel.py          # 入力UI（プレイヤー入力 + 実行）
│   ├── output_display.py             # 出力表示（応答 + 状態変化）
│   └── log_viewer.py                 # 履歴ログの表示（時系列・グラフ）
├── data/
│   ├── characters/                   # キャラクター設定ファイル（JSON）
│   ├── world_templates/             # 世界観テンプレート
│   └── logs/                        # 各セッションのログファイル
├── utils/
│   ├── file_io.py                   # ファイル入出力ヘルパー
│   ├── decorators.py                # 共通デコレーター（キャッシュ、例外処理など）
│   └── helpers.py                   # 補助関数
├── tests/
│   └── test_character.py            # 単体テストファイル
└── requirements.txt                 # 使用パッケージ一覧
```

## 起動

```bash
python3 -m streamlit run app.py
```
