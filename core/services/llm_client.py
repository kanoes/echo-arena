"""
LLMクライアント

OpenAI APIと通信するためのクライアントクラス
"""

import openai
from typing import Dict, List, Optional, Any, Union
import json
import time
import random
from config.settings import OPENAI_API_KEY
from config.logging import LoggingConfig


# ログ設定
logging_config = LoggingConfig()
logger = logging_config.get_logger()

# Global API Keyを設定
openai.api_key = OPENAI_API_KEY

class LLMClient:
    """LLMクライアントクラス"""
    
    def __init__(self):
        """初期化"""
        self.last_call_time = 0
        self.min_delay = 0.5  # API呼び出し間の最小時間（秒）
    
    def _enforce_rate_limit(self):
        """API呼び出しの頻度制限を適用"""
        elapsed = time.time() - self.last_call_time
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
        self.last_call_time = time.time()
    
    def analyze_input(self, user_input: str, context: str, model: str = "gpt-3.5-turbo", temperature: float = 0.3) -> Dict[str, Any]:
        """ユーザー入力を分析する
        
        Args:
            user_input: ユーザー入力テキスト
            context: 現在のコンテキスト
            model: 使用するGPTモデル
            temperature: 温度パラメータ
            
        Returns:
            分析結果の辞書
        """
        self._enforce_rate_limit()
        
        try:
            prompt = f"""
            以下のユーザー入力を分析し、意図とアクションタイプを特定してください。

            コンテキスト:
            {context}

            ユーザー入力:
            {user_input}

            次の形式でJSON出力を返してください:
            {{
                "intent": "ユーザーの主な意図（会話、情報収集、移動、アクション実行など）",
                "action_type": "TALK/MOVE/EXAMINE/ITEM_USE/ATTACK/DEFEND/MAGIC/SKILL/REST/CRAFT",
                "target": "アクションの対象（人物、場所、アイテムなど）",
                "importance": "このインタラクションの重要度（1-10の整数）",
                "keywords": ["関連するキーワード"]
            }}
            """
            
            response = openai.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": prompt}],
                temperature=temperature,
                max_tokens=200,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content
            
            try:
                result = json.loads(result_text)
                return result
            except json.JSONDecodeError:
                logger.error(f"JSONデコードエラー: {result_text}")
                return {
                    "intent": "unknown",
                    "action_type": "TALK",
                    "target": "none",
                    "importance": 3,
                    "keywords": []
                }
                
        except Exception as e:
            logger.error(f"入力分析エラー: {str(e)}")
            return {
                "intent": "error",
                "action_type": "TALK",
                "target": "none",
                "importance": 3,
                "keywords": []
            }
    
    def generate_character_response(self, character_prompt: str, user_input: str, 
                                   memory_context: str, world_context: str,
                                   model: str = "gpt-4-turbo", 
                                   temperature: float = 0.7,
                                   with_emotion: bool = False) -> Union[str, Dict[str, Any]]:
        """キャラクターの応答を生成
        
        Args:
            character_prompt: キャラクター設定プロンプト
            user_input: ユーザー入力
            memory_context: キャラクターの記憶コンテキスト
            world_context: 世界の状態コンテキスト
            model: 使用するGPTモデル
            temperature: 温度パラメータ
            with_emotion: 感情データを取得するかどうか
            
        Returns:
            キャラクター応答テキスト、またはテキストとメタデータの辞書
        """
        self._enforce_rate_limit()
        
        try:
            # 感情データを返すかどうかによってシステムプロンプトを変更
            if with_emotion:
                system_prompt = f"""
                あなたは以下のキャラクター設定に基づいて一人称で会話するロールプレイエージェントです。
                常にキャラクターとして応答し、決してAIアシスタントとしては話さないでください。

                {character_prompt}

                ## 世界のコンテキスト
                {world_context}

                ## 記憶
                {memory_context}

                ## 制約事項
                - 一人称で話し、キャラクターの個性を保ってください。
                - 過去の会話や記憶と一貫性を保ってください。
                - 応答は3〜5文程度を目安にしてください。
                - 常にキャラクターのロールプレイを続けてください。
                
                ## 出力形式
                以下のJSON形式で出力してください:
                {{
                  "text": "キャラクターの応答テキスト",
                  "emotions": {{
                    "JOY": -0.1〜0.1, // 喜びの変化量
                    "SADNESS": -0.1〜0.1, // 悲しみの変化量
                    "ANGER": -0.1〜0.1, // 怒りの変化量
                    ... // 必要に応じて他の感情を変更
                  }},
                  "relationship_change": -0.1〜0.1 // プレイヤーとの関係性の変化量
                }}
                
                各感情値は-0.1から0.1の範囲で、この対話の結果として変化する値を示します。
                全ての感情を含める必要はなく、変化する感情のみ含めてください。
                relationship_changeは会話の内容に基づいたプレイヤーとの関係性の変化量です。
                """
            else:
                system_prompt = f"""
                あなたは以下のキャラクター設定に基づいて一人称で会話するロールプレイエージェントです。
                常にキャラクターとして応答し、決してAIアシスタントとしては話さないでください。

                {character_prompt}

                ## 世界のコンテキスト
                {world_context}

                ## 記憶
                {memory_context}

                ## 制約事項
                - 一人称で話し、キャラクターの個性を保ってください。
                - 過去の会話や記憶と一貫性を保ってください。
                - 応答は3〜5文程度を目安にしてください。
                - 常にキャラクターのロールプレイを続けてください。
                """
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
            
            # 感情データを返す場合はJSON形式を指定
            response_format = {"type": "json_object"} if with_emotion else None
            
            response = openai.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=500,
                response_format=response_format
            )
            
            result_text = response.choices[0].message.content
            
            # 感情データが要求された場合はJSONをパース
            if with_emotion:
                try:
                    result = json.loads(result_text)
                    # 念のため必須フィールドを確認
                    if "text" not in result:
                        result["text"] = "すみません、うまく応答できませんでした。"
                    if "emotions" not in result:
                        result["emotions"] = {}
                    if "relationship_change" not in result:
                        result["relationship_change"] = 0.0
                    return result
                except json.JSONDecodeError:
                    logger.error(f"キャラクター応答のJSONデコードエラー: {result_text}")
                    # エラー時はテキストのみを返す
                    return {"text": result_text, "emotions": {}, "relationship_change": 0.0}
            
            return result_text
                
        except Exception as e:
            logger.error(f"キャラクター応答生成エラー: {str(e)}")
            return "すみません、うまく応答できませんでした。" if not with_emotion else {
                "text": "すみません、うまく応答できませんでした。",
                "emotions": {},
                "relationship_change": 0.0
            }
    
    def generate_world_description(self, world_context: str, scene_context: str, 
                                  model: str = "gpt-3.5-turbo", 
                                  temperature: float = 0.5) -> str:
        """世界/シーン説明を生成
        
        Args:
            world_context: 世界の状態コンテキスト
            scene_context: 現在のシーンコンテキスト
            model: 使用するGPTモデル
            temperature: 温度パラメータ
            
        Returns:
            シーン説明テキスト
        """
        self._enforce_rate_limit()
        
        try:
            prompt = f"""
            以下の世界設定とシーン情報に基づいて、現在の状況を描写する説明文を生成してください。
            プレイヤーが現在の状況をイメージできる、簡潔で臨場感のある説明を作成してください。

            ## 世界の情報
            {world_context}

            ## 現在のシーン
            {scene_context}

            説明文は以下の要素を含めてください：
            - 現在の場所の外観と雰囲気
            - 時間帯と天候の様子
            - その場にいるキャラクター
            - 注目すべきアイテムや特徴
            
            200字程度で簡潔に説明してください。教科書的な説明ではなく、プレイヤーがその場にいるかのような臨場感ある描写を心がけてください。
            """
            
            response = openai.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": prompt}],
                temperature=temperature,
                max_tokens=300
            )
            
            return response.choices[0].message.content
                
        except Exception as e:
            logger.error(f"世界説明生成エラー: {str(e)}")
            return "現在の状況を把握できませんでした。" 