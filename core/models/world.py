"""
ワールドモデル

ゲーム世界の状態、天候、時間、場所などを管理するモデル
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum


class WeatherType(Enum):
    """天候タイプ"""
    SUNNY = "晴れ"
    CLOUDY = "曇り"
    RAINY = "雨"
    STORMY = "嵐"
    FOGGY = "霧"
    SNOWY = "雪"
    
    def __str__(self) -> str:
        return self.value


class TimeOfDay(Enum):
    """時間帯"""
    DAWN = "夜明け"
    MORNING = "朝"
    NOON = "昼"
    AFTERNOON = "午後"
    EVENING = "夕方"
    NIGHT = "夜"
    MIDNIGHT = "深夜"
    
    def __str__(self) -> str:
        return self.value


@dataclass
class Location:
    """場所の情報"""
    id: str
    name: str
    description: str
    connected_locations: List[str] = field(default_factory=list)
    items: List[str] = field(default_factory=list)
    characters: List[str] = field(default_factory=list)  # その場所にいるキャラクターのID
    
    # 追加的な情報
    properties: Dict[str, str] = field(default_factory=dict)


@dataclass
class WorldTime:
    """ゲーム内の時間管理"""
    current_time: datetime
    time_scale: float = 1.0  # 現実時間に対するゲーム内時間の進行速度
    
    def advance(self, real_seconds: float) -> None:
        """現実時間の経過に応じてゲーム内時間を進める
        
        Args:
            real_seconds: 経過した現実時間（秒）
        """
        game_seconds = real_seconds * self.time_scale
        self.current_time += timedelta(seconds=game_seconds)
    
    def get_time_of_day(self) -> TimeOfDay:
        """現在の時間帯を取得
        
        Returns:
            現在の時間帯
        """
        hour = self.current_time.hour
        
        if 5 <= hour < 7:
            return TimeOfDay.DAWN
        elif 7 <= hour < 10:
            return TimeOfDay.MORNING
        elif 10 <= hour < 14:
            return TimeOfDay.NOON
        elif 14 <= hour < 17:
            return TimeOfDay.AFTERNOON
        elif 17 <= hour < 20:
            return TimeOfDay.EVENING
        elif 20 <= hour < 23:
            return TimeOfDay.NIGHT
        else:
            return TimeOfDay.MIDNIGHT


@dataclass
class World:
    """ゲーム世界の全体状態"""
    id: str
    name: str
    description: str
    
    # 時間・天候
    time: WorldTime
    current_weather: WeatherType = WeatherType.SUNNY
    
    # 場所
    locations: Dict[str, Location] = field(default_factory=dict)
    current_main_location_id: str = ""  # 現在のメインシーンの場所
    
    # グローバルイベント
    global_events: List[str] = field(default_factory=list)
    
    # 世界の特性
    properties: Dict[str, str] = field(default_factory=dict)
    
    def add_location(self, location: Location) -> None:
        """世界に場所を追加
        
        Args:
            location: 追加する場所
        """
        self.locations[location.id] = location
        
        # 最初の場所であれば、現在の場所として設定
        if not self.current_main_location_id:
            self.current_main_location_id = location.id
    
    def change_weather(self, new_weather: WeatherType) -> None:
        """天候を変更
        
        Args:
            new_weather: 新しい天候
        """
        self.current_weather = new_weather
    
    def add_global_event(self, event_description: str) -> None:
        """グローバルイベントを追加
        
        Args:
            event_description: イベントの説明
        """
        self.global_events.append(event_description)
    
    def get_current_location(self) -> Optional[Location]:
        """現在のメイン場所を取得
        
        Returns:
            現在の場所、または存在しない場合はNone
        """
        return self.locations.get(self.current_main_location_id) 