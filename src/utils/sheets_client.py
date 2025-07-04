"""
Google Sheets API クライアント
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import gspread
    from google.auth.exceptions import GoogleAuthError
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    print("Google Sheets パッケージがインストールされていません。pip install gspread google-auth を実行してください。")
    GSPREAD_AVAILABLE = False

from .config import Config


class SheetsClient:
    """Google Sheets API クライアント"""
    
    def __init__(self, config: Optional[Config] = None):
        """
        クライアントを初期化
        
        Args:
            config: 設定オブジェクト
        """
        if not GSPREAD_AVAILABLE:
            raise ImportError("gspread パッケージがインストールされていません")
        
        self.config = config or Config()
        self.client = None
        self._authenticate()
    
    def _authenticate(self) -> None:
        """
        Google Sheets API認証
        """
        credentials_file = self.config.get("google.credentials_file")
        if not credentials_file:
            raise ValueError("GOOGLE_SHEETS_CREDENTIALS_FILE が設定されていません")
        
        credentials_path = Path(credentials_file)
        if not credentials_path.exists():
            raise FileNotFoundError(f"認証ファイルが見つかりません: {credentials_file}")
        
        try:
            scope = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            credentials = Credentials.from_service_account_file(
                credentials_file, scopes=scope
            )
            
            self.client = gspread.authorize(credentials)
            print("Google Sheets API認証に成功しました")
            
        except GoogleAuthError as e:
            raise GoogleAuthError(f"Google Sheets API認証に失敗しました: {e}")
        except Exception as e:
            raise Exception(f"認証エラー: {e}")
    
    def get_spreadsheet(self, spreadsheet_id: Optional[str] = None):
        """
        スプレッドシートを取得
        
        Args:
            spreadsheet_id: スプレッドシートID
            
        Returns:
            スプレッドシートオブジェクト
        """
        if not self.client:
            raise RuntimeError("クライアントが初期化されていません")
        
        sheet_id = spreadsheet_id or self.config.get("google.spreadsheet_id")
        if not sheet_id:
            raise ValueError("GOOGLE_SHEETS_SPREADSHEET_ID が設定されていません")
        
        try:
            return self.client.open_by_key(sheet_id)
        except Exception as e:
            raise Exception(f"スプレッドシートの取得に失敗しました: {e}")
    
    def write_commit_data(self, commit_data: List[Dict[str, Any]], 
                         spreadsheet_id: Optional[str] = None,
                         worksheet_name: str = "Sheet1") -> None:
        """
        コミットデータをスプレッドシートに書き込み
        
        Args:
            commit_data: コミットデータのリスト
            spreadsheet_id: スプレッドシートID
            worksheet_name: ワークシート名
        """
        if not commit_data:
            print("書き込むデータがありません")
            return
        
        spreadsheet = self.get_spreadsheet(spreadsheet_id)
        
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
        except:
            worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=10)
        
        headers = ["プロジェクト(repository)", "貢献者", "日時", "貢献数(commits)"]
        
        existing_data = worksheet.get_all_values()
        if not existing_data or existing_data[0] != headers:
            worksheet.clear()
            worksheet.append_row(headers)
            print(f"ヘッダーを設定しました: {headers}")
        
        rows_to_add = []
        for commit in commit_data:
            row = [
                commit.get("repository", ""),
                commit.get("author", ""),
                commit.get("date", ""),
                str(commit.get("count", 1))
            ]
            rows_to_add.append(row)
        
        if rows_to_add:
            worksheet.append_rows(rows_to_add)
            print(f"{len(rows_to_add)}件のコミットデータを書き込みました")
    
    def clear_sheet(self, spreadsheet_id: Optional[str] = None,
                   worksheet_name: str = "Sheet1") -> None:
        """
        シートをクリア
        
        Args:
            spreadsheet_id: スプレッドシートID
            worksheet_name: ワークシート名
        """
        spreadsheet = self.get_spreadsheet(spreadsheet_id)
        
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
            worksheet.clear()
            print(f"シート '{worksheet_name}' をクリアしました")
        except Exception as e:
            print(f"シートのクリアに失敗しました: {e}")
