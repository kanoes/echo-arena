"""
アクションルーター

ユーザー入力を解析し、適切なアクションへルーティングするモジュール
"""

from typing import Dict, Optional, Any, Tuple

from core.services.llm_client import LLMClient
from core.logic.state_tracker import StateTracker
from core.logic.memory_manager import MemoryManager
from config.settings import DEFAULT_MODEL, DEFAULT_TEMPERATURE
from config.logging import LoggingConfig


# ログ設定
logging_config = LoggingConfig()
logger = logging_config.get_logger()

class ActionRouter:
    """ユーザー入力を分析し、適切なアクションへルーティングするクラス"""
    
    def __init__(self, state_tracker: StateTracker, memory_manager: MemoryManager, llm_client: LLMClient):
        """初期化
        
        Args:
            state_tracker: 状態追跡オブジェクト
            memory_manager: 記憶管理オブジェクト
            llm_client: LLMクライアント
        """
        self.state_tracker = state_tracker
        self.memory_manager = memory_manager
        self.llm_client = llm_client
    
    def analyze_user_input(self, user_input: str, context: str) -> Dict[str, Any]:
        """ユーザー入力を分析
        
        Args:
            user_input: ユーザーの入力テキスト
            context: 現在のコンテキスト
            
        Returns:
            分析結果の辞書
        """
        try:
            analysis = self.llm_client.analyze_user_input(user_input, context)
            logger.debug(f"ユーザー入力分析結果: {analysis}")
            return analysis
        except Exception as e:
            logger.error(f"ユーザー入力分析中にエラーが発生しました: {str(e)}")
            # エラーの場合はデフォルト値を返す
            return {
                "intent": "UNKNOWN",
                "target": "",
                "emotion": "NEUTRAL",
                "importance": 1
            }
    
    def route_action(self, user_input: str) -> Tuple[str, Dict[str, Any]]:
        """ユーザー入力を分析し、適切なアクションをルーティング
        
        Args:
            user_input: ユーザーの入力テキスト
            
        Returns:
            (レスポンステキスト, 状態変化データ)のタプル
        """
        # 現在のシーン説明を取得
        current_scene = self.state_tracker.get_scene_description()
        
        # ユーザー入力を分析
        analysis = self.analyze_user_input(user_input, current_scene)
        
        # 意図に基づいてアクションをルーティング
        intent = analysis.get("intent", "UNKNOWN")
        target = analysis.get("target", "")
        importance = analysis.get("importance", 1)
        
        response = ""
        state_changes = {}
        
        # UIで選択されたキャラクターの取得
        selected_character_id = self.state_tracker.current_interaction_target
        
        # 意図別の処理
        if intent == "TALK" or intent == "ASK":
            # UIで選択したキャラクターを使用
            if selected_character_id:
                # 選択されたキャラクターと会話
                logger.info(f"UIで選択された '{self.state_tracker.characters[selected_character_id].name}' と会話します")
                response, state_changes = self._handle_character_interaction(
                    user_input, selected_character_id, analysis
                )
            else:
                # 選択されたキャラクターがない場合
                response = "会話するキャラクターを選択してください。"
                
        elif intent == "MOVE":
            # 移動処理
            result = self.state_tracker.process_user_action(analysis)
            response = result
            # 移動後のシーン説明を更新
            state_changes = {"scene_updated": True}
            
        elif intent == "EXAMINE":
            # 調査・観察処理
            if target:
                response = self._handle_examination(target)
            else:
                # 対象が指定されていない場合は現在のシーンを詳細に説明
                response = self._generate_detailed_scene_description()
                
        elif intent == "USE_ITEM":
            # アイテム使用処理
            response = f"あなたは {target} を使おうとしましたが、まだその機能は実装されていません。"
            
        else:
            # その他の意図や不明な意図の場合
            response = f"あなたの意図「{intent}」は理解できましたが、まだその機能は実装されていません。"
        
        # プレイヤーの最終インタラクション時間を更新
        self.state_tracker.player.update_last_interaction()
        
        return response, state_changes
    
    def _find_character_by_name(self, name: str) -> Optional[str]:
        """名前からキャラクターIDを検索
        
        Args:
            name: 検索するキャラクター名
            
        Returns:
            キャラクターID、または見つからない場合はNone
        """
        # nameがNoneの場合は早期リターン
        if name is None:
            return None
            
        # 現在の場所にいるキャラクターのみ対象
        location = self.state_tracker.world.get_current_location()
        if not location:
            return None
            
        name_lower = name.lower()
        
        # 完全一致または部分一致で検索
        for char_id in location.characters:
            if char_id in self.state_tracker.characters:
                character = self.state_tracker.characters[char_id]
                if character.name.lower() == name_lower or name_lower in character.name.lower():
                    return char_id
                    
        return None
    
    def _handle_character_interaction(self, user_input: str, character_id: str, 
                                    analysis: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """キャラクターとの対話を処理
        
        Args:
            user_input: ユーザー入力
            character_id: 対象キャラクターID
            analysis: 入力分析結果
            
        Returns:
            (レスポンステキスト, 状態変化データ)のタプル
        """
        character = self.state_tracker.characters[character_id]
        
        # 関連する記憶を取得
        relevant_memories = self.memory_manager.filter_relevant_memories(
            character, user_input, limit=5
        )
        memory_context = self.memory_manager.format_memories_context(relevant_memories)
        
        # 世界の状態コンテキストを構築
        world_context = self._build_world_context(character_id)
        
        # キャラクタープロンプトを構築
        character_prompt = self._build_character_prompt(character)
        
        # LLMを使って応答を生成
        response_data = self.llm_client.generate_character_response(
            character_prompt, 
            user_input, 
            memory_context, 
            world_context,
            model=DEFAULT_MODEL,
            temperature=DEFAULT_TEMPERATURE,
            with_emotion=True  # 感情データも取得
        )
        
        # 応答テキストとメタデータを分離
        if isinstance(response_data, dict):
            response = response_data.get("text", "")
            emotion_data = response_data.get("emotions", {})
            relationship_change = response_data.get("relationship_change", 0.0)
        else:
            response = response_data
            emotion_data = {}
            relationship_change = 0.0
        
        # 感情データがあれば、キャラクターの感情状態を更新
        for emotion_type, value_change in emotion_data.items():
            try:
                if emotion_type in character.emotions:
                    character.update_emotion(emotion_type, value_change)
                    logger.debug(f"キャラクター '{character.name}' の感情 '{emotion_type}' を {value_change:+.2f} 変化させました")
            except Exception as e:
                logger.error(f"感情の更新に失敗しました: {str(e)}")
        
        # 親密度の変化を計算（応答内容から推測）
        if relationship_change == 0:
            # LLMから明示的な関係変化がない場合、文脈から推定
            sentiment_score = self._estimate_sentiment(response)
            relationship_change = sentiment_score * 0.05  # 小さな変化にする
        
        # この対話を記憶として追加
        interaction_memory = f"プレイヤー: {user_input}\n{character.name}: {response}"
        importance = analysis.get("importance", 3)
        emotion = None  # TODO: 応答から感情を抽出
        
        self.state_tracker.add_memory_to_character(
            character_id, interaction_memory, importance, emotion, [self.state_tracker.player.id]
        )
        
        # 最終交流時間を更新
        character.update_last_interaction()
        
        # 状態変化を記録
        state_changes = {
            "character_id": character_id,
            "interaction": True,
            "relationship_change": relationship_change
        }
        
        # 記憶を整理
        self.memory_manager.consolidate_memories(character)
        
        return response, state_changes
    
    def _build_character_prompt(self, character: Any) -> str:
        """キャラクターのプロンプトを構築
        
        Args:
            character: キャラクターオブジェクト
            
        Returns:
            プロンプト文字列
        """
        prompt = f"""
        あなたは「{character.name}」というキャラクターを演じてください。

        ## キャラクター設定
        {character.description}

        ## 性格
        {character.personality}

        ## 背景
        {character.background}

        ## 現在の感情状態
        {', '.join([f"{emotion}: {value:.1f}" for emotion, value in character.emotions.items() if value > 0.3])}

        ## 指示
        1. 常に「{character.name}」として一人称で話し、キャラクターの性格や背景に基づいた反応をしてください。
        2. 会話の文脈や記憶を参照し、一貫性のある応答を心がけてください。
        3. プレイヤーの言動に適切に反応し、感情を表現してください。
        4. 返答は会話文のみにしてください。ナレーションや動作説明は含めないでください。
        """
        
        return prompt
    
    def _build_world_context(self, character_id: str) -> str:
        """世界の状態コンテキストを構築
        
        Args:
            character_id: 対象キャラクターID
            
        Returns:
            世界コンテキスト文字列
        """
        world = self.state_tracker.world
        character = self.state_tracker.characters[character_id]
        current_location = world.get_current_location()
        
        context = f"""
        ## 現在の状況
        場所: {current_location.name}
        {current_location.description}
        
        ## 時間と天候
        時間: {world.time.get_time_of_day()}（{world.time.current_time.strftime('%H:%M')}）
        天候: {world.current_weather}
        
        ## その場にいる人物
        """
        
        # 同じ場所にいるキャラクター
        others = []
        for char_id in current_location.characters:
            if char_id != character_id and char_id in self.state_tracker.characters:
                others.append(self.state_tracker.characters[char_id].name)
                
        if others:
            context += f"登場人物: {', '.join(others)}\n"
        else:
            context += "あなたとプレイヤー以外に誰もいません。\n"
            
        context += f"プレイヤー名: {self.state_tracker.player.character_name}"
        
        return context
    
    def _handle_examination(self, target: str) -> str:
        """対象の調査・観察処理
        
        Args:
            target: 調査対象
            
        Returns:
            調査結果のテキスト
        """
        world = self.state_tracker.world
        current_location = world.get_current_location()
        
        # 場所自体の調査
        if target.lower() in current_location.name.lower() or target.lower() == "ここ" or target.lower() == "周囲":
            return f"""
            【{current_location.name}の詳細】
            {current_location.description}
            
            この場所には特に目立った特徴はありません。平和で静かな雰囲気が漂っています。
            """
            
        # アイテムの調査
        if target in current_location.items:
            return f"{target}を調べました。普通の{target}のようです。"
            
        # キャラクターの観察
        character_id = self._find_character_by_name(target)
        if character_id:
            character = self.state_tracker.characters[character_id]
            return f"""
            【{character.name}の観察】
            {character.description}
            
            現在の様子: {character.name}は落ち着いた様子で、あなたを見ています。
            """
            
        # 何も見つからない場合
        return f"{target}は見当たりませんでした。"
    
    def _generate_detailed_scene_description(self) -> str:
        """現在のシーンの詳細な説明を生成
        
        Returns:
            詳細なシーン説明
        """
        base_description = self.state_tracker.get_scene_description()
        
        # より詳細な説明を追加
        world = self.state_tracker.world
        current_location = world.get_current_location()
        
        additional = f"""
        さらに詳しく観察すると、{current_location.name}には独特の雰囲気があります。
        {world.time.get_time_of_day()}の光が場所全体を照らし、{world.current_weather}の影響で空気は少し{world.current_weather}っぽい感じがします。
        
        周囲は静かで、時折微かな音だけが聞こえます。
        """
        
        return base_description + additional 

    def _estimate_sentiment(self, text: str) -> float:
        """テキストから感情スコアを推定（簡易版）
        
        Args:
            text: 分析するテキスト
            
        Returns:
            感情スコア（-0.2〜0.2の範囲）
        """
        # ポジティブな表現
        positive_words = [
            "ありがとう", "嬉しい", "楽しい", "素晴らしい", "良い", "好き", "嬉し", 
            "幸せ", "感謝", "笑顔", "助かる", "信頼", "尊敬", "大好き", "賛成",
            "よかった", "うれしい", "すごい", "素敵"
        ]
        
        # ネガティブな表現
        negative_words = [
            "残念", "悲しい", "怒り", "不満", "嫌い", "困る", "怖い", "不安", 
            "恐れ", "嫌悪", "迷惑", "反対", "疑問", "悪い", "だめ", "ごめん",
            "申し訳", "失望", "がっかり", "嫌だ", "ひどい"
        ]
        
        text_lower = text.lower()
        
        # 単純な出現回数ベースのスコアリング
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        # 総単語数で正規化
        total_count = max(1, positive_count + negative_count)
        sentiment_score = (positive_count - negative_count) / total_count
        
        # -0.2〜0.2の範囲に制限
        return max(-0.2, min(0.2, sentiment_score)) 