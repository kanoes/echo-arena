"""
キャラクターモデルとメモリ管理

キャラクターデータ構造と記憶システムを定義
"""

from datetime import datetime
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, field
from config.logging import LoggingConfig


# ログ設定
logging_config = LoggingConfig()
logger = logging_config.get_logger()

class Memory:
    """キャラクターの記憶クラス"""
    
    def __init__(self, content: str, 
                 importance: int = 1, 
                 emotion: Optional[str] = None,
                 related_characters: Optional[List[str]] = None):
        """
        初期化
        
        Args:
            content: 記憶の内容
            importance: 重要度 (1-10)
            emotion: 関連する感情
            related_characters: 関連するキャラクターのIDリスト
        """
        self.content = content
        self.importance = min(max(importance, 1), 10)  # 1-10の範囲に制限
        self.emotion = emotion
        self.related_characters = related_characters or []
        self.timestamp = datetime.now()
        self.accessed_count = 0  # この記憶が想起された回数
        
    def access(self):
        """この記憶へのアクセスを記録"""
        self.accessed_count += 1


class Character:
    """ゲーム内のNPCキャラクター"""
    
    def __init__(self, id: str, name: str, description: str = "", 
                 personality: str = "", background: str = ""):
        """
        初期化
        
        Args:
            id: キャラクターの一意識別子
            name: キャラクターの名前
            description: 外見や特徴の説明
            personality: 性格の説明
            background: 背景設定
        """
        self.id = id
        self.name = name
        self.description = description
        self.personality = personality
        self.background = background
        
        # 現在の場所
        self.current_location: Optional[str] = None
        
        # 感情状態 (EmotionType: 値)
        self.emotions: Dict[str, float] = {
            "JOY": 0.0,
            "SADNESS": 0.0,
            "ANGER": 0.0, 
            "FEAR": 0.0,
            "DISGUST": 0.0,
            "SURPRISE": 0.0,
            "TRUST": 0.0,
            "ANTICIPATION": 0.0
        }
        
        # 関係性 (相手のキャラクターID: 関係値 -1.0〜1.0)
        self.relationships: Dict[str, float] = {}
        
        # 記憶システム
        self.short_term_memory: List[Memory] = []  # 短期記憶
        self.long_term_memory: List[Memory] = []   # 長期記憶
        
        # 最後の対話時間
        self.last_interaction = datetime.now()
    
    def update_emotion(self, emotion_type: str, value_change: float) -> None:
        """
        感情値を更新
        
        Args:
            emotion_type: 感情タイプ
            value_change: 変化量（-1.0〜1.0）
        """
        if emotion_type in self.emotions:
            self.emotions[emotion_type] += value_change
            # 0.0〜1.0の範囲に制限
            self.emotions[emotion_type] = min(max(self.emotions[emotion_type], 0.0), 1.0)
    
    def update_relationship(self, target_id: str, value_change: float) -> None:
        """
        他のキャラクターとの関係値を更新
        
        Args:
            target_id: 対象キャラクターID
            value_change: 変化量（-1.0〜1.0）
        """
        if target_id not in self.relationships:
            self.relationships[target_id] = 0.0
            
        self.relationships[target_id] += value_change
        # -1.0〜1.0の範囲に制限
        self.relationships[target_id] = min(max(self.relationships[target_id], -1.0), 1.0)
    
    def add_memory(self, content: str, importance: int = 1, 
                  emotion: Optional[str] = None,
                  related_characters: Optional[List[str]] = None) -> None:
        """
        記憶を追加
        
        Args:
            content: 記憶の内容
            importance: 重要度 (1-10)
            emotion: 関連する感情
            related_characters: 関連するキャラクターのIDリスト
        """
        memory = Memory(content, importance, emotion, related_characters)
        
        # 重要度が高い (7以上) なら直接長期記憶に追加
        if importance >= 7:
            self.long_term_memory.append(memory)
        else:
            # それ以外は短期記憶に追加
            self.short_term_memory.append(memory)
    
    def update_last_interaction(self) -> None:
        """最後の対話時間を更新"""
        self.last_interaction = datetime.now() 