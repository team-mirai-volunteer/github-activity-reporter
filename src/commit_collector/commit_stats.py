"""
GitHubコミット統計収集モジュール
"""
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..utils.config import Config
from ..utils.file_utils import ensure_dir, write_json_file
from ..utils.sheets_client import SheetsClient


def get_github_token() -> Optional[str]:
    """
    GitHub CLIからトークンを取得
    
    Returns:
        GitHubトークン
    """
    try:
        result = subprocess.run(['gh', 'auth', 'token'], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        print("GitHub CLIでの認証が必要です。'gh auth login' を実行してください。")
        return None


def get_team_mirai_repos() -> List[str]:
    """
    team-mirai-volunteer組織の全パブリックリポジトリを取得
    
    Returns:
        リポジトリ名のリスト
    """
    try:
        cmd = [
            'gh', 'repo', 'list', 'team-mirai-volunteer',
            '--visibility=public', '--limit', '100',
            '--json', 'name'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        repos_data = json.loads(result.stdout)
        
        repos = [f"team-mirai-volunteer/{repo['name']}" for repo in repos_data]
        print(f"取得したリポジトリ数: {len(repos)}")
        
        return repos
        
    except subprocess.CalledProcessError as e:
        print(f"リポジトリ一覧の取得に失敗しました: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"JSONの解析に失敗しました: {e}")
        return []


def extract_commit_data(
    repo: str,
    days: int = 30,
    timezone_str: str = "UTC"
) -> List[Dict[str, Any]]:
    """
    指定されたリポジトリからコミットデータを抽出
    
    Args:
        repo: リポジトリ名（owner/repo形式）
        days: 過去何日分を取得するか
        timezone_str: タイムゾーン
        
    Returns:
        コミットデータのリスト
    """
    token = get_github_token()
    if not token:
        return []
    
    tz = timezone.utc if timezone_str == "UTC" else timezone(timedelta(hours=9))
    since_date = datetime.now(tz) - timedelta(days=days)
    since_iso = since_date.isoformat()
    
    print(f"リポジトリ {repo} からコミットデータを取得中... (過去{days}日間)")
    
    try:
        cmd = [
            'gh', 'api', f'repos/{repo}/commits',
            '--paginate',
            '--jq', f'''
            .[] | select(.commit.author.date >= "{since_iso}") | {{
                sha: .sha,
                author: .commit.author.name,
                email: .commit.author.email,
                date: .commit.author.date,
                message: .commit.message,
                url: .html_url
            }}
            '''
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        commits = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                try:
                    commit_data = json.loads(line)
                    
                    commit_date = commit_data.get('date', '')
                    if commit_date:
                        try:
                            dt = datetime.fromisoformat(commit_date.replace('Z', '+00:00'))
                            formatted_date = dt.strftime('%Y-%m-%d')
                        except ValueError:
                            formatted_date = commit_date[:10] if len(commit_date) >= 10 else commit_date
                    else:
                        formatted_date = ''
                    
                    repo_name = repo.replace('team-mirai-volunteer/', '') if repo.startswith('team-mirai-volunteer/') else repo
                    processed_commit = {
                        'repository': repo_name,
                        'author': commit_data.get('author', 'unknown'),
                        'date': formatted_date,
                        'count': 1
                    }
                    
                    commits.append(processed_commit)
                    
                except json.JSONDecodeError:
                    continue
        
        print(f"リポジトリ {repo}: {len(commits)}件のコミットを取得")
        return commits
        
    except subprocess.CalledProcessError as e:
        print(f"リポジトリ {repo} のコミットデータ取得に失敗しました: {e}")
        return []


def aggregate_commit_data(commits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    コミットデータを集約（Repository, Author, Date別にカウント）
    
    Args:
        commits: 個別コミットデータのリスト
        
    Returns:
        集約されたコミットデータ
    """
    aggregated = {}
    
    for commit in commits:
        key = (commit['repository'], commit['author'], commit['date'])
        if key in aggregated:
            aggregated[key]['count'] += 1
        else:
            aggregated[key] = {
                'repository': commit['repository'],
                'author': commit['author'],
                'date': commit['date'],
                'count': 1
            }
    
    return list(aggregated.values())


def collect_all_commit_data(
    repos: Optional[List[str]] = None,
    days: int = 30,
    timezone_str: str = "UTC",
    output_dir: str = "./data"
) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """
    全リポジトリからコミットデータを収集
    
    Args:
        repos: リポジトリのリスト（Noneの場合は全パブリックリポジトリ）
        days: 過去何日分を取得するか
        timezone_str: タイムゾーン
        output_dir: 出力ディレクトリ
        
    Returns:
        集約されたコミットデータとJSONファイルパス
    """
    if repos is None:
        repos = get_team_mirai_repos()
    
    if not repos:
        print("処理対象のリポジトリがありません")
        return [], None
    
    tz = timezone.utc if timezone_str == "UTC" else timezone(timedelta(hours=9))
    end_date = datetime.now(tz)
    start_date = end_date - timedelta(days=days)
    
    date_range_dir = f"{start_date.date().isoformat()}_to_{end_date.date().isoformat()}"
    
    output_path = Path(output_dir) / date_range_dir
    commit_raw_dir = output_path / "raw" / "commits"
    ensure_dir(commit_raw_dir)
    
    all_commits = []
    
    for repo in repos:
        repo_commits = extract_commit_data(repo, days, timezone_str)
        all_commits.extend(repo_commits)
    
    if all_commits:
        aggregated_commits = aggregate_commit_data(all_commits)
        
        commit_file = commit_raw_dir / "aggregated_commits.json"
        write_json_file(aggregated_commits, commit_file)
        
        print(f"全{len(all_commits)}件のコミットを{len(aggregated_commits)}件に集約して {commit_file} に保存しました")
        
        summary = {
            "total_commits": len(all_commits),
            "aggregated_commits": len(aggregated_commits),
            "repositories_count": len(repos),
            "period": {
                "start": start_date.date().isoformat(),
                "end": end_date.date().isoformat(),
                "days": days
            },
            "repositories": repos
        }
        
        summary_file = commit_raw_dir / "summary.json"
        write_json_file([summary], summary_file)
        
        return aggregated_commits, str(commit_file)
    
    return [], None


def upload_to_sheets(
    commit_data: List[Dict[str, Any]],
    config: Optional[Config] = None,
    clear_existing: bool = False
) -> bool:
    """
    コミットデータをGoogle Sheetsにアップロード
    
    Args:
        commit_data: コミットデータ
        config: 設定オブジェクト
        clear_existing: 既存データをクリアするか
        
    Returns:
        成功したかどうか
    """
    try:
        sheets_client = SheetsClient(config)
        
        if clear_existing:
            sheets_client.clear_sheet()
        
        sheets_client.write_commit_data(commit_data)
        
        print("Google Sheetsへのアップロードが完了しました")
        return True
        
    except Exception as e:
        print(f"Google Sheetsへのアップロードに失敗しました: {e}")
        return False
