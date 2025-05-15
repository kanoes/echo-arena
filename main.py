"""
EchoArena メイン起動スクリプト

Streamlitアプリケーションを起動するエントリポイント
"""

import os
import sys
import subprocess
from pathlib import Path


def main():
    """
    メイン関数
    Streamlitアプリケーションを起動
    """
    # 現在のスクリプトのディレクトリを取得
    current_dir = Path(__file__).parent.absolute()
    
    # アプリケーションのパス
    app_path = current_dir / "app.py"
    
    # アプリケーションが存在するか確認
    if not app_path.exists():
        print(f"エラー: アプリケーションファイル '{app_path}' が見つかりません。")
        return 1
    
    try:
        # Streamlitアプリケーションを起動
        print("EchoArena アプリケーションを起動しています...")
        subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path)], check=True)
        return 0
    except subprocess.CalledProcessError as e:
        print(f"アプリケーションの起動中にエラーが発生しました: {e}")
        return 1
    except KeyboardInterrupt:
        print("\nアプリケーションが中断されました。")
        return 0


if __name__ == "__main__":
    sys.exit(main())
