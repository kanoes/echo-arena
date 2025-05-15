"""
EchoArena の設定ファイル
APIキー、パス、各種パラメータなどの設定を管理
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# .env ファイルの読み込み
load_dotenv()

# 基本パス
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CHARACTERS_DIR = DATA_DIR / "characters"
WORLD_TEMPLATES_DIR = DATA_DIR / "world_templates"
LOGS_DIR = DATA_DIR / "logs"

# 各ディレクトリが存在しない場合は作成
for dir_path in [DATA_DIR, CHARACTERS_DIR, WORLD_TEMPLATES_DIR, LOGS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# OpenAI API設定
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
DEFAULT_TEMPERATURE = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4096"))

# ゲーム設定
DEFAULT_WORLD_NAME = "ファンタジー世界"
MAX_CHARACTERS = 5  # 一度に扱えるキャラクターの最大数
MEMORY_RETENTION = 100  # キャラクターが記憶する過去のメッセージ数

# ログ設定
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
