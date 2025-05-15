"""
プロンプト構築

キャラクターや世界の状態に基づいてLLM用のプロンプトを構築するモジュール
"""

import os
from typing import Dict, List, Optional, Any
from pathlib import Path

from core.models.character import Character
from core.models.world import World
from core.models.player import Player


class PromptBuilder:
    """LLM用のプロンプトを構築するクラス"""
    
    def __init__(self, templates_dir: Optional[Path] = None):
        """初期化
        
        Args:
            templates_dir: プロンプトテンプレートディレクトリのパス
                           指定しない場合はデフォルトのディレクトリを使用
        """
        if templates_dir is None:
            # デフォルトは現在のモジュールのある場所の隣にある templates ディレクトリ
            self.templates_dir = Path(__file__).parent / "templates"
        else:
            self.templates_dir = templates_dir
            
        # テンプレートディレクトリが存在しない場合は作成
        self.templates_dir.mkdir(parents=True, exist_ok=True)
    
    def load_template(self, template_name: str) -> str:
        """テンプレートファイルを読み込む
        
        Args:
            template_name: テンプレート名
            
        Returns:
            テンプレート文字列
        """
        template_path = self.templates_dir / f"{template_name}.txt"
        
        # テンプレートが存在しない場合はデフォルトテンプレートを作成
        if not template_path.exists():
            return self._create_default_template(template_name)
            
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    
    def _create_default_template(self, template_name: str) -> str:
        """デフォルトテンプレートを作成
        
        Args:
            template_name: テンプレート名
            
        Returns:
            デフォルトテンプレート文字列
        """
        template = ""
        
        if template_name == "character_base":
            template = """
            あなたは「{character_name}」というキャラクターを演じてください。

            ## キャラクター設定
            {character_description}

            ## 性格
            {character_personality}

            ## 背景
            {character_background}

            ## 現在の感情状態
            {emotions_text}

            ## 指示
            1. 常に「{character_name}」として一人称で話し、キャラクターの性格や背景に基づいた反応をしてください。
            2. 会話の文脈や記憶を参照し、一貫性のある応答を心がけてください。
            3. プレイヤーの言動に適切に反応し、感情を表現してください。
            4. 返答は会話文のみにしてください。ナレーションや動作説明は含めないでください。
            """
        elif template_name == "scene_description":
            template = """
            ## 現在の状況
            場所: {location_name}
            {location_description}
            
            時間: {time_of_day} ({current_time})
            天候: {weather}
            
            ## その場にいる人物
            {characters_present_text}
            
            ## プレイヤーとの関係性
            関係値: {player_relation} (-1.0〜1.0)
            """
        elif template_name == "memory_context":
            template = """
            ## 記憶と過去の出来事
            {memories_text}
            """
        
        # テンプレートファイルを保存
        template_path = self.templates_dir / f"{template_name}.txt"
        with open(template_path, "w", encoding="utf-8") as f:
            f.write(template)
            
        return template
    
    def build_character_prompt(self, character: Character) -> str:
        """キャラクタープロンプトを構築
        
        Args:
            character: キャラクターオブジェクト
            
        Returns:
            構築されたプロンプト
        """
        template = self.load_template("character_base")
        
        # 感情テキストを構築
        emotions_text = ", ".join([f"{emotion}: {value:.1f}" 
                                  for emotion, value in character.emotions.items() 
                                  if value > 0.3])
        
        if not emotions_text:
            emotions_text = "特に強い感情はありません。"
        
        # テンプレート変数を置換
        prompt = template.format(
            character_name=character.name,
            character_description=character.description,
            character_personality=character.personality,
            character_background=character.background,
            emotions_text=emotions_text
        )
        
        return prompt
    
    def build_scene_context(self, world: World, character: Character, 
                           player: Player, characters: Dict[str, Character]) -> str:
        """シーンコンテキストを構築
        
        Args:
            world: 世界オブジェクト
            character: 対象キャラクター
            player: プレイヤーオブジェクト
            characters: キャラクター辞書
            
        Returns:
            構築されたシーンコンテキスト
        """
        template = self.load_template("scene_description")
        
        current_location = world.get_current_location()
        
        # その場所にいるキャラクター
        characters_present = []
        for char_id in current_location.characters:
            if char_id in characters and char_id != character.id:
                char = characters[char_id]
                relation = character.relationships.get(char_id, 0.0)
                characters_present.append(f"{char.name} (関係性: {relation:.1f})")
        
        characters_present_text = ", ".join(characters_present) if characters_present else "あなたとプレイヤー以外には誰もいません。"
        
        # プレイヤーとの関係
        player_relation = character.relationships.get(player.id, 0.0)
        
        # テンプレート変数を置換
        context = template.format(
            location_name=current_location.name,
            location_description=current_location.description,
            time_of_day=world.time.get_time_of_day(),
            current_time=world.time.current_time.strftime("%H:%M"),
            weather=world.current_weather,
            characters_present_text=characters_present_text,
            player_relation=f"{player_relation:.1f}"
        )
        
        return context
    
    def build_memory_context(self, memories_text: str) -> str:
        """記憶コンテキストを構築
        
        Args:
            memories_text: フォーマット済みの記憶テキスト
            
        Returns:
            構築された記憶コンテキスト
        """
        template = self.load_template("memory_context")
        
        # テンプレート変数を置換
        context = template.format(
            memories_text=memories_text
        )
        
        return context 