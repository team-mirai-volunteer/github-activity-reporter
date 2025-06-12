"""
ファイル操作ユーティリティ
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Union

def ensure_dir(path: Union[str, Path]) -> None:
    """
    ディレクトリが存在しない場合は作成する
    
    Args:
        path: ディレクトリパス
    """
    Path(path).mkdir(parents=True, exist_ok=True)

def read_json_file(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """
    JSONファイルを読み込む
    
    Args:
        file_path: JSONファイルのパス
        
    Returns:
        JSONデータ
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return [data]
            else:
                return []
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"JSONファイルの読み込みに失敗しました: {file_path}, エラー: {e}")
        return []

def write_json_file(data: List[Dict[str, Any]], file_path: Union[str, Path]) -> None:
    """
    データをJSONファイルに書き込む
    
    Args:
        data: 書き込むデータ
        file_path: 出力ファイルパス
    """
    ensure_dir(Path(file_path).parent)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def read_text_file(file_path: Union[str, Path]) -> str:
    """
    テキストファイルを読み込む
    
    Args:
        file_path: テキストファイルのパス
        
    Returns:
        ファイル内容
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError as e:
        print(f"ファイルが見つかりません: {file_path}")
        raise e

def write_text_file(content: str, file_path: Union[str, Path]) -> None:
    """
    テキストをファイルに書き込む
    
    Args:
        content: 書き込む内容
        file_path: 出力ファイルパス
    """
    ensure_dir(Path(file_path).parent)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
