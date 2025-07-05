"""
ユーザー名マッピングユーティリティ
"""
from typing import Dict, Optional

class UserNameMapper:
    """ユーザー名マッピングクラス"""
    
    def __init__(self):
        """
        ユーザー名マッピングを初期化
        """
        self._mapping = {
            "kentamurai": "Kenta Murai",
            "muraikenta": "Kenta Murai"
        }
    
    def map_username(self, username: Optional[str]) -> str:
        """
        ユーザー名をマッピング
        
        Args:
            username: 元のユーザー名
            
        Returns:
            マッピング後のユーザー名
        """
        if not username or username == "unknown":
            return "unknown"
        
        return self._mapping.get(username, username)
    
    def add_mapping(self, from_name: str, to_name: str) -> None:
        """
        新しいマッピングを追加
        
        Args:
            from_name: 変換元の名前
            to_name: 変換先の名前
        """
        self._mapping[from_name] = to_name
    
    def get_mappings(self) -> Dict[str, str]:
        """
        現在のマッピング一覧を取得
        
        Returns:
            マッピング辞書
        """
        return self._mapping.copy()

_mapper = UserNameMapper()

def map_username(username: Optional[str]) -> str:
    """
    ユーザー名をマッピング（便利関数）
    
    Args:
        username: 元のユーザー名
        
    Returns:
        マッピング後のユーザー名
    """
    return _mapper.map_username(username)
