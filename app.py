"""
EchoArena メインアプリケーション

Streamlit UIとバックエンドロジックの接続を担当
"""

import streamlit as st
import os
import json
import uuid
from datetime import datetime
from pathlib import Path
import logging

from config.settings import (
    OPENAI_API_KEY, DEFAULT_MODEL, DEFAULT_TEMPERATURE, MAX_TOKENS,
    DATA_DIR, CHARACTERS_DIR, WORLD_TEMPLATES_DIR, LOGS_DIR
)
from core.models.character import Character
from core.models.player import Player
from core.models.world import World, WorldTime, Location, WeatherType, TimeOfDay
from core.models.enums import EmotionType, ActionType, RelationshipType
from core.logic.state_tracker import StateTracker
from core.logic.memory_manager import MemoryManager
from core.logic.action_router import ActionRouter
from core.services.llm_client import LLMClient
from core.ui.sidebar import render_sidebar
from core.ui.interaction_panel import render_interaction_panel
from core.ui.output_display import (
    render_scene_description, render_character_info, 
    render_player_status, render_world_status, render_event_log
)


# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / "app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def init_session_state():
    """セッション状態を初期化"""
    if "initialized" not in st.session_state:
        st.session_state.initialized = False
        st.session_state.player = None
        st.session_state.world = None
        st.session_state.state_tracker = None
        st.session_state.action_router = None
        st.session_state.memory_manager = None
        st.session_state.llm_client = None
        st.session_state.available_characters = {}
        st.session_state.available_worlds = {}
        st.session_state.events = []
        st.session_state.messages = []
        st.session_state.show_character_creation = False
        st.session_state.show_character_edit = False
        st.session_state.new_character_data = None
        st.session_state.edit_character_id = None


def load_available_characters():
    """利用可能なキャラクターを読み込む"""
    characters = {}
    
    # キャラクターディレクトリが存在しない場合は作成
    CHARACTERS_DIR.mkdir(parents=True, exist_ok=True)
    
    for file_path in CHARACTERS_DIR.glob("*.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                character_id = file_path.stem
                characters[character_id] = data["name"]
        except Exception as e:
            logger.error(f"キャラクターファイル '{file_path}' の読み込みに失敗しました: {str(e)}")
    
    # サンプルキャラクターがない場合は作成
    if not characters:
        create_sample_character()
        return load_available_characters()
        
    return characters


def load_available_worlds():
    """利用可能な世界テンプレートを読み込む"""
    worlds = {}
    
    # 世界テンプレートディレクトリが存在しない場合は作成
    WORLD_TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    
    for file_path in WORLD_TEMPLATES_DIR.glob("*.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                world_id = file_path.stem
                worlds[world_id] = data["name"]
        except Exception as e:
            logger.error(f"世界テンプレートファイル '{file_path}' の読み込みに失敗しました: {str(e)}")
    
    # サンプル世界がない場合は作成
    if not worlds:
        create_sample_world()
        return load_available_worlds()
        
    return worlds


def create_sample_character():
    """サンプルキャラクターを作成"""
    sample_character = {
        "id": "sample_npc",
        "name": "アリス",
        "description": "魔法学校の優等生。幼い頃から魔法の才能に恵まれ、特に風の魔法が得意。",
        "personality": "好奇心旺盛で明るい性格。新しいことを学ぶのが大好きだが、時々夢見がちになることも。人付き合いは得意で、誰とでもすぐに打ち解ける。",
        "background": "裕福な魔法使いの家庭に生まれ、5歳の時に魔法の才能が開花。現在は魔法学校の上級生として、様々な魔法を学んでいる。将来は魔法研究者になることを夢見ている。",
        "emotions": {
            "JOY": 0.7,
            "TRUST": 0.6,
            "ANTICIPATION": 0.8
        }
    }
    
    file_path = CHARACTERS_DIR / "sample_npc.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(sample_character, f, ensure_ascii=False, indent=2)
        
    logger.info("サンプルキャラクターを作成しました")


def create_sample_world():
    """サンプル世界を作成"""
    sample_world = {
        "id": "fantasy_world",
        "name": "ファンタジー世界",
        "description": "魔法と冒険に満ちた世界。ドラゴンや精霊など様々な幻想的な生き物が存在する。",
        "locations": [
            {
                "id": "magic_academy",
                "name": "魔法学園",
                "description": "若い魔法使いたちが学ぶ巨大な学園。古い石造りの建物には数千年の歴史がある。",
                "connected_locations": ["city_square", "library"],
                "items": ["魔法の杖", "古い魔道書", "クリスタルボール"]
            },
            {
                "id": "city_square",
                "name": "中央広場",
                "description": "王国の中心に位置する広い広場。噴水や露店が立ち並び、常に人で賑わっている。",
                "connected_locations": ["magic_academy", "inn", "shop"],
                "items": ["水筒", "パン", "リンゴ"]
            },
            {
                "id": "inn",
                "name": "冒険者の宿",
                "description": "冒険者たちが集まる古い宿屋。暖炉の火が温かく、様々な噂話が飛び交う。",
                "connected_locations": ["city_square"],
                "items": ["ビール", "ベッド", "ろうそく"]
            }
        ],
        "starting_location": "magic_academy",
        "time": {
            "hour": 12,
            "minute": 0
        },
        "weather": "SUNNY"
    }
    
    file_path = WORLD_TEMPLATES_DIR / "fantasy_world.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(sample_world, f, ensure_ascii=False, indent=2)
        
    logger.info("サンプル世界を作成しました")


def load_character(character_id):
    """キャラクターを読み込む"""
    file_path = CHARACTERS_DIR / f"{character_id}.json"
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # 感情状態のマッピング
        emotions = {}
        for emotion_name, value in data.get("emotions", {}).items():
            try:
                emotion_type = EmotionType[emotion_name]
                emotions[emotion_type] = value
            except KeyError:
                logger.warning(f"未知の感情タイプ: {emotion_name}")
        
        # キャラクターオブジェクトの作成
        character = Character(
            id=data.get("id", character_id),
            name=data.get("name", "名無し"),
            description=data.get("description", ""),
            personality=data.get("personality", ""),
            background=data.get("background", "")
        )
        
        # 感情状態の設定
        for emotion_type, value in emotions.items():
            character.emotions[emotion_type] = value
        
        return character
        
    except Exception as e:
        logger.error(f"キャラクター '{character_id}' の読み込みに失敗しました: {str(e)}")
        return None


def load_world(world_id):
    """世界を読み込む"""
    file_path = WORLD_TEMPLATES_DIR / f"{world_id}.json"
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 時間の設定
        time_data = data.get("time", {"hour": 12, "minute": 0})
        world_time = WorldTime(
            current_time=datetime.now().replace(
                hour=time_data.get("hour", 12),
                minute=time_data.get("minute", 0),
                second=0,
                microsecond=0
            )
        )
        
        # 天候の設定
        try:
            weather = WeatherType[data.get("weather", "SUNNY")]
        except KeyError:
            weather = WeatherType.SUNNY
            logger.warning(f"未知の天候タイプ: {data.get('weather')}")
        
        # 世界オブジェクトの作成
        world = World(
            id=data.get("id", world_id),
            name=data.get("name", "無名の世界"),
            description=data.get("description", ""),
            time=world_time,
            current_weather=weather
        )
        
        # 場所の追加
        for loc_data in data.get("locations", []):
            location = Location(
                id=loc_data.get("id", str(uuid.uuid4())),
                name=loc_data.get("name", "名前なし"),
                description=loc_data.get("description", ""),
                connected_locations=loc_data.get("connected_locations", []),
                items=loc_data.get("items", [])
            )
            world.add_location(location)
        
        # 開始場所の設定
        starting_location = data.get("starting_location")
        if starting_location and starting_location in world.locations:
            world.current_main_location_id = starting_location
        
        return world
        
    except Exception as e:
        logger.error(f"世界 '{world_id}' の読み込みに失敗しました: {str(e)}")
        return None


def create_player(name, character_name):
    """プレイヤーを作成"""
    player = Player(
        id=str(uuid.uuid4()),
        name=name,
        character_name=character_name
    )
    return player


def handle_character_select(character_id):
    """キャラクター選択時の処理"""
    if not character_id:
        return
        
    character = load_character(character_id)
    if not character:
        return
        
    if st.session_state.state_tracker:
        # 既存のキャラクターを削除して新しいキャラクターを追加
        if character.id in st.session_state.state_tracker.characters:
            del st.session_state.state_tracker.characters[character.id]
            
        # キャラクターが編集されたばかりなら常に再読み込み
        character = load_character(character_id)  # 強制的に再読み込み
        
        st.session_state.state_tracker.add_character(character)
        
        # 選択されたキャラクターを現在の対話対象として設定
        st.session_state.state_tracker.current_interaction_target = character.id
        
        st.session_state.events.append(f"{character.name} が会話に参加しました。")
        logger.info(f"キャラクター '{character.name}' を選択しました")


def handle_world_select(world_id):
    """世界選択時の処理"""
    if not world_id:
        return
        
    # 世界を読み込む
    world = load_world(world_id)
    if not world:
        return
        
    # 既存の状態をクリア
    st.session_state.messages = []
    st.session_state.events = []
    
    # プレイヤーを作成または更新
    if st.session_state.player:
        player = st.session_state.player
    else:
        player = create_player(
            st.session_state.player_name or "プレイヤー",
            st.session_state.character_name or "冒険者"
        )
    
    # 状態追跡とメモリ管理を初期化
    state_tracker = StateTracker(world, player)
    memory_manager = MemoryManager()
    
    # LLMクライアントを初期化
    llm_client = LLMClient()
    
    # アクションルーターを初期化
    action_router = ActionRouter(state_tracker, memory_manager, llm_client)
    
    # セッション状態を更新
    st.session_state.world = world
    st.session_state.player = player
    st.session_state.state_tracker = state_tracker
    st.session_state.memory_manager = memory_manager
    st.session_state.llm_client = llm_client
    st.session_state.action_router = action_router
    
    # 既存のキャラクターがあれば追加
    for character_id, _ in st.session_state.available_characters.items():
        handle_character_select(character_id)
    
    # 初期イベントを追加
    st.session_state.events.append(f"{world.name} の世界に入りました。")
    logger.info(f"世界 '{world.name}' を選択しました")


def handle_user_input(user_input):
    """ユーザー入力の処理"""
    if not st.session_state.initialized or not st.session_state.action_router:
        return "システムが初期化されていません。設定を確認してください。", {}
        
    # アクションルーターを通じて入力を処理
    response, state_changes = st.session_state.action_router.route_action(user_input)
    
    # 状態変化に基づいてイベントを追加
    if state_changes.get("scene_updated", False):
        st.session_state.events.append("場所が変わりました。")
    
    if state_changes.get("interaction", False) and "character_id" in state_changes:
        character_id = state_changes["character_id"]
        if character_id in st.session_state.state_tracker.characters:
            character = st.session_state.state_tracker.characters[character_id]
            st.session_state.events.append(f"{character.name} と会話しました。")
    
    return response, state_changes


def main():
    """メイン関数"""
    # ページの設定
    st.set_page_config(
        page_title="EchoArena",
        page_icon="🎮",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # セッション状態の初期化
    init_session_state()
    
    # 利用可能なキャラクターと世界を読み込む
    if not st.session_state.available_characters:
        st.session_state.available_characters = load_available_characters()
        
    if not st.session_state.available_worlds:
        st.session_state.available_worlds = load_available_worlds()
    
    # サイドバーを表示
    user_settings = render_sidebar(
        on_character_select=handle_character_select,
        on_world_select=handle_world_select,
        available_characters=st.session_state.available_characters,
        available_worlds=st.session_state.available_worlds,
        selected_character_id=st.session_state.get("selected_character_id"),
        selected_world_id=st.session_state.get("selected_world_id")
    )
    
    # キャラクターリストを更新する必要がある場合
    if user_settings.get("refresh_characters", False):
        st.session_state.available_characters = load_available_characters()
    
    # 新しいキャラクターが作成された場合
    if "new_character" in user_settings:
        new_char = user_settings.get("new_character")
        
        # new_charが有効な辞書であり、必要なキーが含まれていることを確認
        if new_char and isinstance(new_char, dict) and "name" in new_char and new_char["name"]:
            character_id = str(uuid.uuid4())
            
            # APIConfig設定を取得
            api_config = {
                "model": "gpt-4o",
                "temperature": 0.7
            }
            
            # APIConfig設定がある場合は上書き
            if "api_config" in new_char:
                api_config = new_char["api_config"]
            
            # キャラクターファイルを保存
            file_path = CHARACTERS_DIR / f"{character_id}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump({
                    "id": character_id,
                    "name": new_char["name"],
                    "description": new_char.get("description", ""),
                    "personality": new_char.get("personality", ""),
                    "background": new_char.get("background", ""),
                    "emotions": {
                        "JOY": 0.5,
                        "TRUST": 0.5,
                        "ANTICIPATION": 0.5
                    },
                    "api_config": api_config
                }, f, ensure_ascii=False, indent=2)
                
            # 利用可能なキャラクターリストを更新
            st.session_state.available_characters[character_id] = new_char["name"]
            
            # 新規キャラクター作成時にsession_stateの項目をクリーンアップ
            if "new_character_data" in st.session_state:
                del st.session_state.new_character_data
            
            # 新しいキャラクターを選択
            handle_character_select(character_id)
            st.rerun()
    
    # ユーザー設定を更新
    st.session_state.player_name = user_settings["player"]["name"]
    st.session_state.character_name = user_settings["player"]["character_name"]
    st.session_state.selected_world_id = user_settings["session"]["world_id"]
    st.session_state.selected_character_id = user_settings["session"]["selected_character_id"]
    
    # 世界が選択されているか確認
    if not st.session_state.world and st.session_state.selected_world_id:
        handle_world_select(st.session_state.selected_world_id)
    
    # メインコンテンツ
    if st.session_state.world and st.session_state.player and st.session_state.state_tracker:
        st.session_state.initialized = True
        
        # シーン説明を表示
        scene_description = st.session_state.state_tracker.get_scene_description()
        render_scene_description(scene_description)
        
        # 世界状態を表示
        render_world_status(st.session_state.world)
        
        # キャラクター情報の表示
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 対話パネルを表示
            render_interaction_panel(on_submit=handle_user_input)
        
        with col2:
            # プレイヤーステータスを表示
            render_player_status(st.session_state.player)
            
            # イベントログを表示
            render_event_log(st.session_state.events)
            
            # キャラクター情報を表示
            for character_id, character in st.session_state.state_tracker.characters.items():
                render_character_info(character, show_details=True)
    else:
        # 初期セットアップガイド
        st.markdown("""
        ## 🎮 EchoArenaへようこそ！
        
        テキスト型TRPG（テーブルトークRPG）シミュレーターです。
        
        ### 始めるには:
        1. サイドバーであなたの名前とキャラクター名を入力してください
        2. プレイする世界を選択してください
        3. 会話したいNPCキャラクターを選んでください
        
        準備ができたら、会話を始めましょう！自然言語でキャラクターと会話したり、
        行動を起こしたりできます。
        
        ### APIキーの設定方法:
        1. `.env`ファイルに`OPENAI_API_KEY=your_key_here`を設定する方法
        2. 環境変数に`NPC_名前_OPENAI_KEY=your_key_here`を設定する方法
           - この形式で設定するとNPCごとに別々のAPIキーを使い分けられます
           - キャラクター作成/編集時に環境変数からキーを選択できます
        """)


if __name__ == "__main__":
    main()
