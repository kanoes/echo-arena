"""
列挙型の定義

感情タイプ、行動タイプなどのシステム全体で使用される列挙型を定義
"""

from enum import Enum, auto
from config.logging import LoggingConfig


# ログ設定
logging_config = LoggingConfig()
logger = logging_config.get_logger()

class EmotionType(Enum):
    """キャラクターの感情タイプ"""
    JOY = "喜び"
    SADNESS = "悲しみ"
    ANGER = "怒り"
    FEAR = "恐れ"
    DISGUST = "嫌悪"
    SURPRISE = "驚き"
    TRUST = "信頼"
    ANTICIPATION = "期待"
    LOVE = "愛情"
    HATE = "憎しみ"
    
    def __str__(self) -> str:
        return self.value


class ActionType(Enum):
    """キャラクターの行動タイプ"""
    TALK = "会話"
    MOVE = "移動"
    ITEM_USE = "アイテム使用"
    ATTACK = "攻撃"
    DEFEND = "防御"
    MAGIC = "魔法"
    SKILL = "特殊スキル"
    REST = "休息"
    EXAMINE = "調査"
    CRAFT = "製作"
    
    def __str__(self) -> str:
        return self.value


class RelationshipType(Enum):
    """キャラクター間の関係性タイプ"""
    STRANGER = "見知らぬ人"
    ACQUAINTANCE = "知人"
    FRIEND = "友人"
    CLOSE_FRIEND = "親友"
    RIVAL = "ライバル"
    ENEMY = "敵"
    FAMILY = "家族"
    LOVER = "恋人"
    MENTOR = "師匠"
    STUDENT = "弟子"
    
    def __str__(self) -> str:
        return self.value 