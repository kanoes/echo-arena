"""
EchoArena Streamlit Application

Streamlit UIとバックエンドロジックの接続を担当
"""

import streamlit as st
import json
import uuid
from datetime import datetime   

from config.settings import (
    OPENAI_API_KEY, DEFAULT_MODEL, DEFAULT_TEMPERATURE, MAX_TOKENS,
    DATA_DIR, CHARACTERS_DIR, WORLD_TEMPLATES_DIR, LOGS_DIR
)
from core.models.character import Character
from core.models.player import Player
from core.models.world import World, WorldTime, Location, WeatherType
from core.models.enums import EmotionType
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
from utils.create_sample import create_sample_character, create_sample_world
from config.logging import LoggingConfig


# ログ設定
logging_config = LoggingConfig()
logger = logging_config.get_logger()


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
        # ゲーム開始状態フラグを追加
        st.session_state.game_started = False
        # キャラクター設定が完了したかどうかのフラグ
        st.session_state.setup_complete = False


def load_available_characters():
    """利用可能なキャラクターを読み込む"""
    characters = {}
    
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
        
        # 親密度の初期設定
        if character.id not in st.session_state.player.relationships:
            st.session_state.player.relationships[character.id] = 0.0
        
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
            
            # 親密度の更新
            if character_id in st.session_state.player.relationships:
                relationship_change = state_changes.get("relationship_change", 0.0)
                st.session_state.player.update_relationship(character_id, relationship_change)
                if relationship_change != 0.0:
                    st.session_state.events.append(f"{character.name} との親密度が変化しました。")
            
            # キャラクターとの対話履歴を追加
            st.session_state.events.append(f"{character.name} と会話しました。")
    
    return response, state_changes

def render_setup_screen():
    """ゲーム開始前の設定画面をレンダリング"""
    st.title("🎮 Echo Arena - ゲーム設定")
    
    # 利用可能なキャラクターと世界を読み込む
    if not st.session_state.available_characters:
        st.session_state.available_characters = load_available_characters()
        
    if not st.session_state.available_worlds:
        st.session_state.available_worlds = load_available_worlds()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("👤 プレイヤー設定")
        player_name = st.text_input("あなたの名前", value=st.session_state.get("player_name", ""))
        character_name = st.text_input("キャラクター名", value=st.session_state.get("character_name", ""))
        
        if not player_name or not character_name:
            st.warning("プレイヤー名とキャラクター名を入力してください")

    with col2:
        st.header("🌍 世界選択")
        world_options = list(st.session_state.available_worlds.items())
        world_names = [name for _, name in world_options]
        world_ids = [id for id, _ in world_options]
        
        if world_ids:
            selected_world_index = 0
            if "selected_world_id" in st.session_state and st.session_state.selected_world_id in world_ids:
                selected_world_index = world_ids.index(st.session_state.selected_world_id)
                
            selected_world_name = st.selectbox("プレイする世界を選択", world_names, index=selected_world_index)
            selected_world_id = world_ids[world_names.index(selected_world_name)]
            st.session_state.selected_world_id = selected_world_id
            
            # 選択された世界の情報を表示
            world = load_world(selected_world_id)
            if world:
                st.markdown(f"**説明**: {world.description}")
        else:
            st.error("利用可能な世界が見つかりません")
            selected_world_id = None
    
    # NPCキャラクター選択セクション
    st.header("🧙 参加させるNPCを選択")
    
    character_options = list(st.session_state.available_characters.items())
    if character_options:
        # 選択されたNPCのリスト
        if "selected_npcs" not in st.session_state:
            st.session_state.selected_npcs = []
            
        # 列を3つ作成
        cols = st.columns(3)
        for i, (char_id, char_name) in enumerate(character_options):
            with cols[i % 3]:
                if st.checkbox(char_name, key=f"npc_{char_id}"):
                    if char_id not in st.session_state.selected_npcs:
                        st.session_state.selected_npcs.append(char_id)
                else:
                    if char_id in st.session_state.selected_npcs:
                        st.session_state.selected_npcs.remove(char_id)
                
                # キャラクター情報を簡単に表示
                character = load_character(char_id)
                if character:
                    st.caption(character.description[:100] + "..." if len(character.description) > 100 else character.description)
    else:
        st.warning("利用可能なNPCがありません")
    
    # 新キャラクター作成ボタン
    if st.button("➕ 新しいNPCを作成"):
        st.session_state.show_character_creation = True
        st.rerun()
    
    # ゲーム開始ボタン
    start_col1, start_col2, start_col3 = st.columns([1, 2, 1])
    with start_col2:
        if st.button("🎮 ゲームを開始", type="primary", use_container_width=True):
            if not player_name or not character_name:
                st.error("プレイヤー名とキャラクター名を入力してください")
            elif not selected_world_id:
                st.error("プレイする世界を選択してください")
            elif not st.session_state.selected_npcs:
                st.error("少なくとも1人のNPCを選択してください")
            else:
                # プレイヤー情報を保存
                st.session_state.player_name = player_name
                st.session_state.character_name = character_name
                
                # ゲーム開始フラグをセット
                st.session_state.game_started = True
                st.session_state.setup_complete = True
                
                # 世界を読み込む
                handle_world_select(selected_world_id)
                
                # 選択したNPCを追加
                for char_id in st.session_state.selected_npcs:
                    if char_id:
                        handle_character_select(char_id)
                
                st.rerun()


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
    
    # ゲームがまだ開始されていない場合は設定画面を表示
    if not st.session_state.game_started:
        render_setup_screen()
        return
    
    # ここからはゲームが開始された後の処理
    
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
            
            # ゲームが開始されていない場合
            if not st.session_state.game_started:
                st.rerun()
            else:
                # ゲーム開始済みの場合は新しいキャラクターを選択
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
        
        # 設定を変更して最初からやり直すボタン
        if st.sidebar.button("⚙️ 設定をリセットして最初から始める"):
            st.session_state.game_started = False
            st.session_state.setup_complete = False
            st.session_state.initialized = False
            st.session_state.world = None
            st.session_state.player = None
            st.session_state.state_tracker = None
            st.session_state.action_router = None
            st.session_state.memory_manager = None
            st.session_state.messages = []
            st.session_state.events = []
            st.rerun()
        
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
                render_character_info(character, show_details=True, player_relationships=st.session_state.player.relationships)
    else:
        # 初期セットアップガイド
        st.markdown("""
        ## 🎮 EchoArenaへようこそ！
        
        テキスト型TRPG（テーブルトークRPG）シミュレーターです。
        
        ### 始めるには:
        1. 「⚙️ 設定をリセットして最初から始める」ボタンをクリックして初期設定画面に戻ってください。
        2. あなたの名前とキャラクター名、世界を選択してください。
        3. 会話したいNPCキャラクターを選んでください。
        4. 「ゲームを開始」ボタンをクリックしてください。
        
        自然言語でキャラクターと会話したり、行動を起こしたりできます。
        
        """)


if __name__ == "__main__":
    main()
