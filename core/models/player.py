"""
プレイヤーモデル

ユーザープレイヤーの状態やセッション情報を管理するモデル
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime

from core.models.character import Character


@dataclass
class Player:
    """プレイヤーモデル"""
    id: str
    name: str
    
    # プレイヤーのインゲーム情報
    character_name: str
    character_description: str = ""
    current_location: str = "不明"
    
    # セッション情報
    session_id: str = ""
    session_start_time: Optional[datetime] = None
    last_interaction_time: Optional[datetime] = None
    
    # 特性・所持品など
    traits: Dict[str, str] = field(default_factory=dict)
    inventory: List[str] = field(default_factory=list)
    stats: Dict[str, int] = field(default_factory=dict)
    
    # 関係性
    relationships: Dict[str, float] = field(default_factory=dict)  # キャラクターID: 親密度
    
    def __post_init__(self):
        """初期化後の処理"""
        if not self.session_start_time:
            self.session_start_time = datetime.now()
        self.last_interaction_time = self.session_start_time
    
    def update_last_interaction(self):
        """最終インタラクション時間を更新"""
        self.last_interaction_time = datetime.now()
    
    def update_relationship(self, character_id: str, value_change: float) -> None:
        """キャラクターとの関係性を更新する
        
        Args:
            character_id: 対象キャラクターのID
            value_change: 変化量（正または負）
        """
        current = self.relationships.get(character_id, 0.0)
        new_value = max(-1.0, min(1.0, current + value_change))  # -1.0-1.0の範囲に制限
        self.relationships[character_id] = new_value
    
    def add_item(self, item_name: str) -> None:
        """アイテムをインベントリに追加
        
        Args:
            item_name: アイテム名
        """
        self.inventory.append(item_name)
    
    def remove_item(self, item_name: str) -> bool:
        """インベントリからアイテムを削除
        
        Args:
            item_name: アイテム名
            
        Returns:
            削除が成功したかどうか
        """
        if item_name in self.inventory:
            self.inventory.remove(item_name)
            return True
        return False
    
    def get_interaction_duration(self) -> float:
        """現在のセッションの経過時間を分単位で取得
        
        Returns:
            経過時間（分）
        """
        if not self.session_start_time:
            return 0.0
        
        delta = datetime.now() - self.session_start_time
        return delta.total_seconds() / 60.0 