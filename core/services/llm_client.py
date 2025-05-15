"""
LLM クライアント

OpenAI API を呼び出すためのラッパーモジュール
"""

import os
import json
from typing import Dict, List, Any, Optional, Union
import logging

from openai import OpenAI

from config.settings import OPENAI_API_KEY, DEFAULT_MODEL, DEFAULT_TEMPERATURE, MAX_TOKENS


# ロガーの設定
logger = logging.getLogger(__name__)


class LLMClient:
    """LLM (OpenAI) APIクライアント"""
    
    def __init__(self):
        """初期化"""
        self.api_key = OPENAI_API_KEY
        if not self.api_key:
            logger.warning("OpenAI API キーが設定されていません。.envファイルでOPENAI_API_KEYを設定してください。")
            
        # クライアントインスタンスを作成
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
    
    def generate_character_response(
        self,
        character_prompt: str,
        user_input: str,
        memory_context: str,
        world_context: str,
        model: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = MAX_TOKENS
    ) -> str:
        """キャラクターの応答を生成する
        
        Args:
            character_prompt: キャラクター設定のプロンプト
            user_input: ユーザー入力
            memory_context: 記憶の文脈情報
            world_context: 世界の文脈情報
            model: 使用するモデル名
            temperature: 温度パラメータ
            max_tokens: 最大トークン数
            
        Returns:
            生成されたキャラクターの応答テキスト
        """
        try:
            if not self.client:
                raise ValueError("OpenAI API キーが設定されていません。.envファイルでOPENAI_API_KEYを設定してください。")
            
            # プロンプトの構築
            messages = [
                {"role": "system", "content": character_prompt},
                {"role": "system", "content": f"## 記憶と過去の出来事\n{memory_context}"},
                {"role": "system", "content": f"## 現在の世界の状況\n{world_context}"},
                {"role": "user", "content": user_input}
            ]
            
            # APIリクエスト
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # 応答の取得
            generated_text = response.choices[0].message.content
            
            # トークン使用量のログ
            logger.info(f"Token usage - Prompt: {response.usage.prompt_tokens}, "
                       f"Completion: {response.usage.completion_tokens}, "
                       f"Total: {response.usage.total_tokens}")
            
            return generated_text
            
        except ValueError as e:
            error_message = str(e)
            logger.error(f"APIキーエラー: {error_message}")
            return f"[エラー: {error_message}]"
        except Exception as e:
            logger.error(f"LLM API呼び出し中にエラーが発生しました: {str(e)}")
            return f"[エラー: APIリクエスト失敗 - {str(e)}]"
    
    def analyze_user_input(
        self,
        user_input: str,
        context: str,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.2,  # 低温度で決定的な応答を得る
    ) -> Dict[str, Any]:
        """ユーザー入力を分析し、意図や感情などの情報を抽出する
        
        Args:
            user_input: ユーザー入力
            context: 現在の会話コンテキスト
            model: 使用するモデル名
            temperature: 温度パラメータ
            
        Returns:
            分析結果を含む辞書
        """
        try:
            if not self.client:
                raise ValueError("OpenAI API キーが設定されていません。.envファイルでOPENAI_API_KEYを設定してください。")
            
            prompt = """
            ユーザーの入力を分析し、以下の情報をJSON形式で抽出してください:
            
            1. 主な意図（TALK, ASK, MOVE, USE_ITEM, ATTACK, など）
            2. 対象（キャラクター名、アイテム名、場所名など）
            3. 感情（ある場合）
            4. 重要度（1-10のスケール）
            
            JSON形式で回答してください。例:
            {
                "intent": "TALK",
                "target": "アリス",
                "emotion": "友好的",
                "importance": 5
            }
            """
            
            messages = [
                {"role": "system", "content": prompt},
                {"role": "system", "content": f"現在のコンテキスト: {context}"},
                {"role": "user", "content": user_input}
            ]
            
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content
            return json.loads(result_text)
            
        except ValueError as e:
            error_message = str(e)
            logger.error(f"APIキーエラー: {error_message}")
            # エラーの場合はデフォルト値を返す
            return {
                "intent": "UNKNOWN",
                "target": "NONE",
                "emotion": "NEUTRAL",
                "importance": 1
            }
        except Exception as e:
            logger.error(f"ユーザー入力分析中にエラーが発生しました: {str(e)}")
            # エラーの場合はデフォルト値を返す
            return {
                "intent": "UNKNOWN",
                "target": "NONE",
                "emotion": "NEUTRAL",
                "importance": 1
            } 