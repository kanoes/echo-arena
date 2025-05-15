"""
対話パネルUI

プレイヤーの入力フォームと実行ボタンを含む対話UIコンポーネント
"""

import streamlit as st
from typing import Callable, Dict, Any


def render_interaction_panel(on_submit: Callable[[str], Dict[str, Any]]) -> None:
    """対話パネルをレンダリング
    
    Args:
        on_submit: 送信時に呼び出される関数。ユーザー入力を引数に取り、
                 レスポンステキストと状態変化の辞書を返す
    """
    with st.container():
        st.markdown("### 👤 あなたのアクション")
        
        # セッション状態を初期化
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        # メッセージ履歴を表示
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
        # ユーザー入力フォーム
        user_input = st.chat_input("ここにメッセージを入力...")
        
        if user_input:
            # ユーザーメッセージをチャット履歴に追加
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # ユーザーメッセージを表示
            with st.chat_message("user"):
                st.markdown(user_input)
            
            # 処理中表示
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                message_placeholder.markdown("🤔 考え中...")
                
                # アクション処理
                response, state_changes = on_submit(user_input)
                
                # レスポンスメッセージを表示
                message_placeholder.markdown(response)
            
            # アシスタントメッセージをチャット履歴に追加
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # 状態変化に基づいてUIを更新（必要に応じて）
            if state_changes.get("scene_updated", False):
                st.rerun()  # シーンが更新された場合は画面を更新 