"""
サイドバーUI

ゲーム設定パネルとキャラクター選択パネルを含むサイドバーUIコンポーネント
"""

import streamlit as st
from typing import Dict, List, Optional, Any, Callable
import os
import json
from datetime import datetime
from pathlib import Path

from core.models.character import Character
from core.models.world import World, WeatherType, TimeOfDay
from config.settings import CHARACTERS_DIR
from config.logging import LoggingConfig


# ログ設定
logging_config = LoggingConfig()
logger = logging_config.get_logger()

def render_sidebar(on_character_select: Callable[[str], None],
                  on_world_select: Callable[[str], None],
                  available_characters: Dict[str, str],
                  available_worlds: Dict[str, str],
                  selected_character_id: Optional[str] = None,
                  selected_world_id: Optional[str] = None) -> Dict[str, Any]:
    """サイドバーを表示
    
    Args:
        on_character_select: キャラクター選択時のコールバック
        on_world_select: 世界選択時のコールバック
        available_characters: 利用可能なキャラクター辞書 {id: name}
        available_worlds: 利用可能な世界辞書 {id: name}
        selected_character_id: 現在選択されているキャラクターID
        selected_world_id: 現在選択されている世界ID
        
    Returns:
        ユーザー設定の辞書
    """
    # 結果辞書を初期化
    result = {
        "player": {
            "name": "",
            "character_name": ""
        },
        "session": {
            "world_id": selected_world_id,
            "selected_character_id": selected_character_id
        },
        "model": {
            "name": "gpt-4-turbo",
            "temperature": 0.7,
            "max_tokens": 4000,
            "memory_retention": 100
        }
    }
    
    with st.sidebar:
        st.title("🎮 EchoArena")
        st.markdown("---")
        
        # プレイヤー設定
        st.header("👤 プレイヤー設定")
        
        # セッション状態の初期化
        if "player_name" not in st.session_state:
            st.session_state.player_name = ""
            
        # プレイヤー名の入力
        player_name = st.text_input("あなたの名前", value=st.session_state.player_name)
        st.session_state.player_name = player_name
        result["player"]["name"] = player_name
        
        # キャラクター名の入力
        if "character_name" not in st.session_state:
            st.session_state.character_name = ""
            
        character_name = st.text_input("キャラクター名", value=st.session_state.character_name)
        st.session_state.character_name = character_name
        result["player"]["character_name"] = character_name
        
        # セッション情報を表示
        st.markdown("---")
        st.header("🌐 セッション情報")
        
        # 世界選択
        world_options = list(available_worlds.items())
        world_names = [name for _, name in world_options]
        world_ids = [id for id, _ in world_options]
        
        selected_world_index = world_ids.index(selected_world_id) if selected_world_id in world_ids else 0
        selected_world_name = st.selectbox("世界", world_names, index=selected_world_index)
        
        # 選択された世界名からIDを取得
        selected_world_id = world_ids[world_names.index(selected_world_name)]
        result["session"]["world_id"] = selected_world_id
        
        # 世界が変更された場合、コールバックを呼び出す
        if "previous_world_id" not in st.session_state or st.session_state.previous_world_id != selected_world_id:
            on_world_select(selected_world_id)
            st.session_state.previous_world_id = selected_world_id
        
        # NPCキャラクター選択
        st.markdown("---")
        st.header("🧙 NPCキャラクター")
        
        # キャラクター選択
        character_options = list(available_characters.items())
        character_names = [name for _, name in character_options]
        character_ids = [id for id, _ in character_options]
        
        # 他に選択肢がない場合は「なし」を表示
        if not character_names:
            character_names = ["利用可能なNPCがありません"]
            character_ids = [""]
        
        selected_character_index = character_ids.index(selected_character_id) if selected_character_id in character_ids else 0
        selected_character_name = st.selectbox("NPCキャラクター", character_names, index=selected_character_index)
        
        # 選択されたキャラクター名からIDを取得（選択肢がある場合）
        if character_ids[0]:
            selected_character_id = character_ids[character_names.index(selected_character_name)]
            result["session"]["selected_character_id"] = selected_character_id
            
            # キャラクターが変更された場合、コールバックを呼び出す
            if "previous_character_id" not in st.session_state or st.session_state.previous_character_id != selected_character_id:
                on_character_select(selected_character_id)
                st.session_state.previous_character_id = selected_character_id
            
            # 選択されたキャラクターの編集ボタン
            if selected_character_id:
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("✏️ 編集", key="edit_character_button"):
                        st.session_state.show_character_edit = True
                        st.session_state.edit_character_id = selected_character_id
        
        # キャラクター作成ボタン
        if st.button("➕ 新しいNPCを作成"):
            st.session_state.show_character_creation = True
        
        # キャラクター編集フォーム
        if st.session_state.get("show_character_edit", False) and st.session_state.get("edit_character_id"):
            char_id = st.session_state.edit_character_id
            char_file_path = CHARACTERS_DIR / f"{char_id}.json"
            
            if char_file_path.exists():
                # キャラクターファイルを読み込む
                with open(char_file_path, "r", encoding="utf-8") as f:
                    char_data = json.load(f)
                
                with st.form("character_edit_form"):
                    st.subheader(f"NPCを編集: {char_data.get('name', '')}")
                    
                    # 基本情報の編集
                    edit_char_name = st.text_input("キャラクター名", value=char_data.get("name", ""))
                    edit_char_desc = st.text_area("説明", value=char_data.get("description", ""))
                    edit_char_personality = st.text_area("性格", value=char_data.get("personality", ""))
                    edit_char_background = st.text_area("背景", value=char_data.get("background", ""))
                    
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        cancel_button = st.form_submit_button("キャンセル")
                    with col2:
                        submit_button = st.form_submit_button("保存")
                    
                    if cancel_button:
                        st.session_state.show_character_edit = False
                        st.rerun()
                        
                    if submit_button:
                        if not edit_char_name:
                            st.error("キャラクター名を入力してください。")
                        elif edit_char_name:
                            # 更新されたキャラクターデータ
                            updated_character = {
                                "id": char_id,
                                "name": edit_char_name,
                                "description": edit_char_desc,
                                "personality": edit_char_personality,
                                "background": edit_char_background,
                                "emotions": char_data.get("emotions", {
                                    "JOY": 0.5,
                                    "TRUST": 0.5,
                                    "ANTICIPATION": 0.5
                                })
                            }
                            
                            # ファイルに保存
                            with open(char_file_path, "w", encoding="utf-8") as f:
                                json.dump(updated_character, f, ensure_ascii=False, indent=2)
                            
                            # 利用可能なキャラクターリストの更新（名前が変更された場合）
                            if edit_char_name != char_data.get("name", ""):
                                result["refresh_characters"] = True
                            
                            # 編集完了メッセージ
                            st.success(f"キャラクター '{edit_char_name}' を更新しました。")
                            
                            # フォームを閉じる
                            st.session_state.show_character_edit = False
                            st.rerun()
            else:
                st.error(f"キャラクターファイルが見つかりません: {char_id}")
                st.session_state.show_character_edit = False
        
        # キャラクター作成フォーム
        if st.session_state.get("show_character_creation", False):
            with st.form("character_creation_form"):
                st.subheader("新しいNPCを作成")
                
                new_char_name = st.text_input("キャラクター名", key="new_char_name")
                new_char_desc = st.text_area("説明", key="new_char_desc")
                new_char_personality = st.text_area("性格", key="new_char_personality")
                new_char_background = st.text_area("背景", key="new_char_background")
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    cancel_button = st.form_submit_button("キャンセル")
                with col2:
                    submit_button = st.form_submit_button("作成")
                
                if cancel_button:
                    st.session_state.show_character_creation = False
                    st.rerun()
                
                if submit_button:
                    if not new_char_name:
                        st.error("キャラクター名を入力してください。")
                    elif new_char_name:
                        # 新しいキャラクターの作成ロジックはアプリケーション側で実装
                        new_character_data = {
                            "name": new_char_name,
                            "description": new_char_desc,
                            "personality": new_char_personality,
                            "background": new_char_background
                        }
                    
                        result["new_character"] = new_character_data
                        st.session_state.new_character_data = new_character_data
                        st.session_state.show_character_creation = False
                        st.rerun()
        
        # 設定
        st.markdown("---")
        st.header("⚙️ 設定")
        
        # モデル選択
        model_options = ["gpt-4-turbo", "gpt-3.5-turbo"]
        selected_model = st.selectbox("AIモデル", model_options)
        result["model"]["name"] = selected_model
        
        # 温度設定
        temperature = st.slider("温度", min_value=0.0, max_value=1.0, value=0.7, step=0.1)
        result["model"]["temperature"] = temperature
        
        # 高度な設定
        with st.expander("高度な設定"):
            max_tokens = st.number_input("最大トークン数", min_value=100, max_value=8000, value=4000, step=100)
            memory_retention = st.number_input("記憶保持数", min_value=10, max_value=200, value=100, step=10)
            result["model"]["max_tokens"] = max_tokens
            result["model"]["memory_retention"] = memory_retention
        
        return result 