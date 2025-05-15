"""
出力表示UI

ゲーム状態、キャラクター情報、プレイヤーステータスなどの表示UIコンポーネント
"""

import streamlit as st
from typing import Dict, List, Optional, Any
import random
from datetime import datetime

from core.models.character import Character
from core.models.world import World, WeatherType, TimeOfDay
from core.models.player import Player
from config.logging import LoggingConfig


# ログ設定
logging_config = LoggingConfig()
logger = logging_config.get_logger()

def render_scene_description(description: str) -> None:
    """シーン説明を表示
    
    Args:
        description: シーン説明テキスト
    """
    st.markdown(f"## 🌍 現在の状況")
    st.markdown(description)


def render_character_info(character: Character, show_details: bool = False, player_relationships: dict = None) -> None:
    """キャラクター情報を表示
    
    Args:
        character: キャラクターオブジェクト
        show_details: 詳細情報を表示するかどうか
        player_relationships: プレイヤーとNPCの関係性辞書
    """
    with st.expander(f"ℹ️ {character.name} の情報", expanded=False):
        st.markdown(f"**説明**: {character.description}")
        
        if show_details:
            st.markdown(f"**性格**: {character.personality}")
            st.markdown(f"**背景**: {character.background}")
            
            # 親密度の表示
            if player_relationships and character.id in player_relationships:
                intimacy = player_relationships[character.id]
                intimacy_value = (intimacy + 1) / 2  # -1.0〜1.0 から 0.0〜1.0 に変換
                
                intimacy_text = "親密度"
                if intimacy > 0.8:
                    intimacy_text = "👍 親密度（非常に良好）"
                elif intimacy > 0.5:
                    intimacy_text = "😊 親密度（良好）"
                elif intimacy > 0.1:
                    intimacy_text = "🙂 親密度（やや良好）"
                elif intimacy > -0.1:
                    intimacy_text = "😐 親密度（中立）"
                elif intimacy > -0.5:
                    intimacy_text = "🙁 親密度（やや低い）"
                elif intimacy > -0.8:
                    intimacy_text = "😠 親密度（低い）"
                else:
                    intimacy_text = "👎 親密度（非常に低い）"
                
                st.progress(intimacy_value, text=f"{intimacy_text} ({intimacy:.2f})")
            
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
            
            # 最終交流時間
            if hasattr(character, 'last_interaction') and character.last_interaction:
                time_diff = datetime.now() - character.last_interaction
                hours, remainder = divmod(time_diff.total_seconds(), 3600)
                minutes, _ = divmod(remainder, 60)
                
                if hours > 0:
                    time_str = f"{int(hours)}時間{int(minutes)}分前"
                else:
                    time_str = f"{int(minutes)}分前"
                
                st.caption(f"最後の交流: {time_str}")


def render_player_status(player: Player) -> None:
    """プレイヤーステータスを表示
    
    Args:
        player: プレイヤーオブジェクト
    """
    with st.expander("👤 プレイヤー情報", expanded=False):
        st.markdown(f"**名前**: {player.name}")
        st.markdown(f"**キャラクター名**: {player.character_name}")
        st.markdown(f"**現在地**: {player.current_location}")
        
        if player.inventory:
            st.markdown("**所持品**:")
            for item in player.inventory:
                st.markdown(f"- {item}")


def render_world_status(world: World) -> None:
    """世界の状態を表示
    
    Args:
        world: 世界オブジェクト
    """
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 場所表示
        current_location = world.get_current_main_location()
        if current_location:
            st.info(f"📍 **場所**: {current_location.name}")
    
    with col2:
        # 時間表示
        current_time = world.time.current_time
        time_str = current_time.strftime("%H:%M")
        st.info(f"🕒 **時間**: {time_str}")
    
    with col3:
        # 天気表示
        st.info(f"☁️ **天気**: {world.current_weather.value}")


def render_event_log(events: list) -> None:
    """イベントログを表示
    
    Args:
        events: イベントログのリスト
    """
    with st.expander("📜 イベントログ", expanded=False):
        for event in events[-10:]:  # 最新の10件のみ表示
            st.text(event)


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