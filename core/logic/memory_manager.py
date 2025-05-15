"""
記憶管理

キャラクターの短期・長期記憶の管理と検索ロジックを提供するモジュール
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import heapq

from core.models.character import Character, Memory
from config.settings import MEMORY_RETENTION
from config.logging import LoggingConfig


# ログ設定
logging_config = LoggingConfig()
logger = logging_config.get_logger()

class MemoryManager:
    """キャラクターの記憶を管理するクラス"""
    
    def __init__(self, retention_limit: int = MEMORY_RETENTION):
        """初期化
        
        Args:
            retention_limit: 保持する短期記憶の最大数
        """
        self.retention_limit = retention_limit
    
    def consolidate_memories(self, character: Character) -> None:
        """短期記憶を整理し、重要な記憶を長期記憶に移動
        
        Args:
            character: 対象キャラクター
        """
        # 短期記憶が最大数を超えた場合、古いものを削除
        if len(character.short_term_memory) > self.retention_limit:
            # 重要度でソートし、重要なものと新しいものを優先して残す
            # 重要度 * 0.7 + 新しさ * 0.3 のスコアで評価
            now = datetime.now()
            
            def memory_score(memory: Memory) -> float:
                # 新しさスコア（1.0が最新、0.0が30日以上前）
                days_old = (now - memory.timestamp).total_seconds() / (60 * 60 * 24)
                recency_score = max(0.0, 1.0 - (days_old / 30.0))
                # 重要度スコア（0.1-1.0）
                importance_score = memory.importance / 10.0
                # 最終スコア
                return importance_score * 0.7 + recency_score * 0.3
            
            # スコアの高い順に保持する記憶を選択
            scored_memories = [(memory_score(mem), i, mem) 
                              for i, mem in enumerate(character.short_term_memory)]
            keep_memories = heapq.nlargest(self.retention_limit, scored_memories)
            
            # 削除される記憶から重要なものを長期記憶に移動
            for score, i, memory in scored_memories:
                if (score, i, memory) not in keep_memories and memory.importance >= 5:
                    if memory not in character.long_term_memory:
                        character.long_term_memory.append(memory)
                        logger.debug(f"重要な記憶を長期記憶に移行: {memory.content[:30]}...")
            
            # 短期記憶を更新
            character.short_term_memory = [mem for _, _, mem in keep_memories]
            logger.info(f"キャラクター '{character.name}' の記憶を整理しました。"
                      f"短期記憶: {len(character.short_term_memory)}件、"
                      f"長期記憶: {len(character.long_term_memory)}件")
    
    def filter_relevant_memories(self, character: Character, 
                               context: str, limit: int = 5) -> List[Memory]:
        """現在のコンテキストに関連する記憶をフィルタリング
        
        Args:
            character: 対象キャラクター
            context: 現在のコンテキスト（会話内容など）
            limit: 返す記憶の最大数
            
        Returns:
            関連する記憶のリスト
        """
        # TODO: ベクトル埋め込みによる意味的検索の実装
        # 現在は単純なキーワードマッチと重要度でフィルタリング
        
        all_memories = character.long_term_memory + character.short_term_memory
        
        # 単語の一致度でフィルタリング（単純な実装）
        context_words = set(context.lower().split())
        
        def relevance_score(memory: Memory) -> float:
            # 内容の単語を抽出
            memory_words = set(memory.content.lower().split())
            # 一致する単語数
            matching_words = context_words.intersection(memory_words)
            # 一致度スコア（0.0-1.0）
            match_score = len(matching_words) / max(1, len(context_words))
            # 重要度スコア（0.1-1.0）
            importance_score = memory.importance / 10.0
            # 最終スコア = 一致度 * 0.6 + 重要度 * 0.4
            return match_score * 0.6 + importance_score * 0.4
        
        # スコアの高い順に記憶を選択
        scored_memories = [(relevance_score(mem), i, mem) 
                          for i, mem in enumerate(all_memories)]
        relevant_memories = heapq.nlargest(limit, scored_memories)
        
        result = [mem for _, _, mem in relevant_memories]
        return result
    
    def format_memories_context(self, memories: List[Memory]) -> str:
        """記憶リストをプロンプト用のコンテキスト文字列にフォーマット
        
        Args:
            memories: 記憶のリスト
            
        Returns:
            フォーマットされたコンテキスト文字列
        """
        if not memories:
            return "特に関連する記憶はありません。"
            
        # 時系列順にソート
        sorted_memories = sorted(memories, key=lambda m: m.timestamp)
        
        # 記憶をフォーマット
        memory_texts = []
        for memory in sorted_memories:
            timestamp = memory.timestamp.strftime("%Y-%m-%d %H:%M")
            emotion_text = f"感情: {memory.emotion}" if memory.emotion else ""
            related_chars = f"関連人物: {', '.join(memory.related_characters)}" if memory.related_characters else ""
            
            memory_text = f"[{timestamp}] {memory.content}"
            if emotion_text or related_chars:
                memory_text += f" ({emotion_text} {related_chars})"
                
            memory_texts.append(memory_text)
            
        return "\n".join(memory_texts)
    
    def summarize_character_history(self, character: Character) -> str:
        """キャラクターの記憶から歴史的な要約を生成
        
        Args:
            character: 対象キャラクター
            
        Returns:
            キャラクターの歴史の要約
        """
        # 長期記憶から重要な出来事を抽出
        important_memories = sorted(
            [m for m in character.long_term_memory if m.importance >= 7],
            key=lambda m: m.timestamp
        )
        
        if not important_memories:
            return f"{character.name}の歴史に特に重要な出来事はありません。"
            
        # 要約を生成
        summary = f"{character.name}の重要な記憶:\n\n"
        
        for memory in important_memories:
            timestamp = memory.timestamp.strftime("%Y-%m-%d")
            summary += f"・{timestamp}: {memory.content}\n"
            
        return summary 