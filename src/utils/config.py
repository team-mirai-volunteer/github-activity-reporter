"""
設定管理モジュール
"""
import os
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv

class Config:
    """設定管理クラス"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        設定を初期化
        
        Args:
            config_file: 設定ファイルのパス（指定しない場合は.envを使用）
        """
        if config_file:
            load_dotenv(config_file)
        else:
            load_dotenv()
        
        self._config = {
            "github": {
                "token": os.getenv("GITHUB_TOKEN"),
            },
            "openai": {
                "api_key": os.getenv("OPENAI_API_KEY"),
            },
            "output": {
                "default_dir": os.getenv("OUTPUT_DIR", "./data"),
                "timezone": os.getenv("TIMEZONE", "UTC"),
            },
            "repositories": {
                "action_board": "team-mirai-volunteer/action-board",
                "fact_checker": "team-mirai-volunteer/fact-checker",
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        設定値を取得
        
        Args:
            key: 設定キー（ドット記法で階層指定可能）
            default: デフォルト値
            
        Returns:
            設定値
        """
        keys = key.split(".")
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_repositories(self) -> Dict[str, str]:
        """
        対象リポジトリの一覧を取得
        
        Returns:
            リポジトリ名とURLのマッピング
        """
        return self._config["repositories"]
