"""
出力表示UI

ゲーム状態やキャラクター情報を表示するUIコンポーネント
"""

import streamlit as st
from typing import Dict, List, Optional, Any
import random

from core.models.character import Character
from core.models.world import World, WeatherType, TimeOfDay
from core.models.player import Player


def render_scene_description(scene_description: str) -> None:
    """シーン説明を表示
    
    Args:
        scene_description: シーン説明テキスト
    """
    with st.container():
        st.markdown("## 🌍 現在の状況")
        
        # より読みやすいスタイルを適用
        styled_description = scene_description.replace(
            "【場所】", "**【場所】**"
        ).replace(
            "【時間】", "**【時間】**"
        ).replace(
            "【天候】", "**【天候】**"
        ).replace(
            "【登場人物】", "**【登場人物】**"
        ).replace(
            "【アイテム】", "**【アイテム】**"
        )
        
        # 各セクション間に適切な行間を確保
        styled_description = styled_description.replace("\n\n", "\n")
        
        st.markdown(styled_description)
        
        # 明確な境界線を追加
        st.markdown("---")


def render_character_info(character: Character, show_details: bool = False) -> None:
    """キャラクター情報を表示
    
    Args:
        character: キャラクターオブジェクト
        show_details: 詳細情報を表示するかどうか
    """
    with st.expander(f"ℹ️ {character.name} の情報", expanded=False):
        st.markdown(f"**説明**: {character.description}")
        
        if show_details:
            st.markdown(f"**性格**: {character.personality}")
            st.markdown(f"**背景**: {character.background}")
            
            # 感情状態
            st.markdown("**感情状態**:")
            emotions_sorted = sorted(
                [(emotion, value) for emotion, value in character.emotions.items() if value > 0.2],
                key=lambda x: x[1],
                reverse=True
            )
            
            if emotions_sorted:
                cols = st.columns(min(3, len(emotions_sorted)))
                for i, (emotion, value) in enumerate(emotions_sorted):
                    with cols[i % 3]:
                        st.progress(value, text=f"{emotion} ({value:.1f})")
            else:
                st.markdown("特に強い感情はありません")


def render_player_status(player: Player) -> None:
    """プレイヤーステータスを表示
    
    Args:
        player: プレイヤーオブジェクト
    """
    with st.container():
        st.markdown("### 📊 プレイヤーステータス")
        
        # 基本情報
        st.markdown(f"**キャラクター名**: {player.character_name}")
        
        # インベントリ
        if player.inventory:
            st.markdown("**所持品**:")
            st.markdown(", ".join(player.inventory))
        else:
            st.markdown("**所持品**: なし")
        
        # 関係性
        if player.relationships:
            st.markdown("**関係性**:")
            relationships_sorted = sorted(
                [(name, value) for name, value in player.relationships.items()],
                key=lambda x: x[1],
                reverse=True
            )
            
            for name, value in relationships_sorted:
                relation_text = _get_relation_text(value)
                st.markdown(f"* {name}: {relation_text} ({value:.1f})")


def render_world_status(world: World) -> None:
    """世界ステータスを表示
    
    Args:
        world: 世界オブジェクト
    """
    with st.container():
        # タイトルを追加して、セクションとして明確に識別できるようにする
        st.markdown("### 🗺️ 世界情報")
        
        cols = st.columns(3)
        
        with cols[0]:
            st.markdown(f"**時間**: {world.time.get_time_of_day()} ({world.time.current_time.strftime('%H:%M')})")
            
        with cols[1]:
            st.markdown(f"**天候**: {world.current_weather}")
            
        with cols[2]:
            location = world.get_current_location()
            if location:
                st.markdown(f"**場所**: {location.name}")
        
        # 世界情報の後にも境界線を追加
        st.markdown("---")


def render_event_log(events: List[str], max_display: int = 5) -> None:
    """イベントログを表示
    
    Args:
        events: イベントリスト
        max_display: 表示する最大数
    """
    with st.expander("📜 イベントログ", expanded=False):
        if events:
            for event in events[-max_display:]:
                st.markdown(f"* {event}")
        else:
            st.markdown("イベントはまだありません")


def _get_relation_text(value: float) -> str:
    """関係値からテキスト表現を取得
    
    Args:
        value: 関係値 (-1.0〜1.0)
        
    Returns:
        関係性のテキスト表現
    """
    if value >= 0.8:
        return "親密"
    elif value >= 0.5:
        return "友好的"
    elif value >= 0.2:
        return "好意的"
    elif value > -0.2:
        return "中立"
    elif value > -0.5:
        return "警戒"
    elif value > -0.8:
        return "敵対的"
    else:
        return "憎悪" 