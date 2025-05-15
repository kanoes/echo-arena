"""
状態追跡ロジック

ゲーム内の状態（キャラクター、世界、プレイヤーなど）を追跡・更新するモジュール
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from core.models.player import Player
from core.models.character import Character
from core.models.world import World, WeatherType, TimeOfDay
from core.models.enums import EmotionType, ActionType


# ロガーの設定
logger = logging.getLogger(__name__)


class StateTracker:
    """ゲーム状態の追跡および更新を管理するクラス"""
    
    def __init__(self, world: World, player: Player):
        """初期化
        
        Args:
            world: ゲーム世界のモデル
            player: プレイヤーモデル
        """
        self.world = world
        self.player = player
        self.characters: Dict[str, Character] = {}  # キャラクターID: キャラクターオブジェクト
        self.session_start_time = datetime.now()
        self.last_update_time = self.session_start_time
        
        # 現在のメイン状態
        self.current_scene_description = ""
        self.current_interaction_target: Optional[str] = None  # 主な対話対象キャラクターID
    
    def add_character(self, character: Character) -> None:
        """キャラクターをゲームに追加
        
        Args:
            character: 追加するキャラクター
        """
        self.characters[character.id] = character
        
        # キャラクターを現在の場所に配置
        current_location = self.world.get_current_location()
        if current_location:
            current_location.characters.append(character.id)
            character.current_location = current_location.id
    
    def update_time(self) -> None:
        """ゲーム内時間を更新"""
        now = datetime.now()
        elapsed_seconds = (now - self.last_update_time).total_seconds()
        self.world.time.advance(elapsed_seconds)
        self.last_update_time = now
        
        # 時間帯の変化がある場合、イベントとして記録
        time_of_day = self.world.time.get_time_of_day()
        logger.info(f"時間が更新されました: {time_of_day}")
    
    def update_character_emotions(self, character_id: str, 
                                 emotions_changes: Dict[EmotionType, float]) -> None:
        """キャラクターの感情を更新
        
        Args:
            character_id: 対象キャラクターのID
            emotions_changes: 感情タイプと変化量の辞書
        """
        character = self.characters.get(character_id)
        if not character:
            logger.warning(f"キャラクター '{character_id}' が見つかりません")
            return
            
        for emotion_type, value_change in emotions_changes.items():
            character.update_emotion(emotion_type, value_change)
            logger.debug(f"キャラクター '{character.name}' の感情 '{emotion_type}' を"
                       f"{value_change:+.2f} 更新しました → {character.emotions[emotion_type]:.2f}")
    
    def update_relationships(self, subject_id: str, target_id: str, 
                            value_change: float) -> None:
        """キャラクター間の関係性を更新
        
        Args:
            subject_id: 主体となるキャラクターID（またはプレイヤーID）
            target_id: 対象キャラクターID
            value_change: 変化量
        """
        # プレイヤーから他のキャラクターへの関係性
        if subject_id == self.player.id:
            self.player.update_relationship(target_id, value_change)
            logger.debug(f"プレイヤーから '{target_id}' への関係性を"
                       f"{value_change:+.2f} 更新しました")
        # キャラクターから他のキャラクターへの関係性
        elif subject_id in self.characters:
            subject = self.characters[subject_id]
            subject.update_relationship(target_id, value_change)
            logger.debug(f"キャラクター '{subject_id}' から '{target_id}' への関係性を"
                       f"{value_change:+.2f} 更新しました")
    
    def add_memory_to_character(self, character_id: str, content: str, 
                               importance: int = 1,
                               emotion: Optional[EmotionType] = None,
                               related_characters: List[str] = None) -> None:
        """キャラクターに記憶を追加
        
        Args:
            character_id: 対象キャラクターのID
            content: 記憶の内容
            importance: 重要度（1-10）
            emotion: 関連する感情
            related_characters: 関連するキャラクターのIDリスト
        """
        character = self.characters.get(character_id)
        if not character:
            logger.warning(f"キャラクター '{character_id}' が見つかりません")
            return
            
        character.add_memory(content, importance, emotion, related_characters)
        logger.debug(f"キャラクター '{character.name}' に記憶を追加しました: {content[:50]}...")
    
    def move_character(self, character_id: str, location_id: str) -> bool:
        """キャラクターを別の場所に移動
        
        Args:
            character_id: 移動するキャラクターのID
            location_id: 移動先の場所ID
            
        Returns:
            移動が成功したかどうか
        """
        character = self.characters.get(character_id)
        if not character:
            logger.warning(f"キャラクター '{character_id}' が見つかりません")
            return False
            
        # 移動先の場所が存在するか確認
        if location_id not in self.world.locations:
            logger.warning(f"場所 '{location_id}' が存在しません")
            return False
            
        # 現在の場所から削除
        current_location = self.world.locations.get(character.current_location)
        if current_location and character_id in current_location.characters:
            current_location.characters.remove(character_id)
            
        # 新しい場所に追加
        self.world.locations[location_id].characters.append(character_id)
        character.current_location = location_id
        
        logger.info(f"キャラクター '{character.name}' を '{self.world.locations[location_id].name}' に移動しました")
        return True
    
    def move_player(self, location_id: str) -> bool:
        """プレイヤーを別の場所に移動
        
        Args:
            location_id: 移動先の場所ID
            
        Returns:
            移動が成功したかどうか
        """
        # 移動先の場所が存在するか確認
        if location_id not in self.world.locations:
            logger.warning(f"場所 '{location_id}' が存在しません")
            return False
            
        # プレイヤーの場所を更新
        self.player.current_location = location_id
        self.world.current_main_location_id = location_id
        
        logger.info(f"プレイヤーを '{self.world.locations[location_id].name}' に移動しました")
        return True
    
    def get_scene_description(self) -> str:
        """現在のシーンの説明を生成
        
        Returns:
            シーンの説明テキスト
        """
        location = self.world.get_current_location()
        if not location:
            return "あなたは何もない空間にいます。"
            
        # 基本的な場所の説明
        description = f"【場所】{location.name}\n{location.description}\n\n"
        
        # 時間と天候
        time_of_day = self.world.time.get_time_of_day()
        description += f"【時間】{time_of_day}（{self.world.time.current_time.strftime('%H:%M')}）\n"
        description += f"【天候】{self.world.current_weather}\n\n"
        
        # その場所にいるキャラクター
        characters_present = []
        for char_id in location.characters:
            if char_id in self.characters:
                characters_present.append(self.characters[char_id].name)
        
        if characters_present:
            description += f"【登場人物】{', '.join(characters_present)}\n\n"
        else:
            description += "【登場人物】この場所には誰もいません。\n\n"
            
        # 利用可能なアイテム
        if location.items:
            description += f"【アイテム】{', '.join(location.items)}"
        else:
            description += "【アイテム】この場所には特に目立ったアイテムはありません。"
        
        self.current_scene_description = description
        return description
    
    def process_user_action(self, action_data: Dict[str, Any]) -> str:
        """ユーザーアクションを処理し、結果を返す
        
        Args:
            action_data: ユーザーアクションのデータ
                {
                    "intent": アクションの意図,
                    "target": 対象オブジェクト,
                    "emotion": 感情（オプション）,
                    "importance": 重要度
                }
                
        Returns:
            アクション処理の結果
        """
        intent = action_data.get("intent", "UNKNOWN")
        target = action_data.get("target", "")
        importance = action_data.get("importance", 1)
        
        result = f"アクション: {intent} → {target}"
        
        # アクションの種類に応じた処理
        if intent == "MOVE":
            # 場所へ移動
            location_found = False
            for loc_id, location in self.world.locations.items():
                if target.lower() in location.name.lower():
                    success = self.move_player(loc_id)
                    result = f"あなたは {location.name} に移動しました。" if success else f"{location.name} への移動に失敗しました。"
                    location_found = True
                    break
            
            if not location_found:
                result = f"場所「{target}」は見つかりませんでした。"
                
        # 他のアクションタイプを処理（実装は省略）
                
        return result 