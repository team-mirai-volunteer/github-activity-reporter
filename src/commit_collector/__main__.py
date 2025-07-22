"""
コミット統計収集メインモジュール
"""
import argparse
import sys
from typing import List, Optional

from ..utils.config import Config
from .commit_stats import collect_all_commit_data, upload_to_sheets


def main() -> int:
    """
    メイン関数
    
    Returns:
        終了コード（0: 成功, 1: 失敗）
    """
    config = Config()
    
    parser = argparse.ArgumentParser(
        description='team-mirai-volunteer組織のコミット統計を収集してGoogle Sheetsに書き込む'
    )
    
    parser.add_argument(
        '--repos',
        help='リポジトリ名（カンマ区切り、指定しない場合は全パブリックリポジトリ）'
    )
    parser.add_argument(
        '--since-date',
        help='開始日（YYYY-MM-DD形式、指定しない場合は2025-05-01）',
        default='2025-05-01'
    )
    parser.add_argument(
        '--output-dir',
        help='出力ディレクトリ',
        default=config.get("output.default_dir", "./data")
    )
    parser.add_argument(
        '--timezone',
        help='タイムゾーン',
        default=config.get("output.timezone", "UTC")
    )
    parser.add_argument(
        '--no-upload',
        action='store_true',
        help='Google Sheetsにアップロードしない（データ収集のみ）'
    )
    parser.add_argument(
        '--clear-sheet',
        action='store_true',
        help='Google Sheetsの既存データをクリアしてから書き込み'
    )
    parser.add_argument(
        '--config',
        help='設定ファイルのパス'
    )
    
    args = parser.parse_args()
    
    if args.config:
        config = Config(config_file=args.config)
    
    repos: Optional[List[str]] = None
    if args.repos:
        repos = [repo.strip() for repo in args.repos.split(',')]
        full_repos = []
        for repo in repos:
            if '/' not in repo:
                full_repos.append(f"team-mirai-volunteer/{repo}")
            else:
                full_repos.append(repo)
        repos = full_repos
    
    print(f"コミットデータ収集を開始します...")
    print(f"対象期間: {args.since_date}以降")
    print(f"タイムゾーン: {args.timezone}")
    
    if repos:
        print(f"対象リポジトリ: {repos}")
    else:
        print("対象: team-mirai-volunteer組織の全パブリックリポジトリ")
    
    commit_data, json_file = collect_all_commit_data(
        repos=repos,
        since_date=args.since_date,
        timezone_str=args.timezone,
        output_dir=args.output_dir
    )
    
    if not commit_data:
        print("コミットデータが取得できませんでした")
        return 1
    
    print(f"収集完了: {len(commit_data)}件のコミット")
    
    if not args.no_upload:
        print("Google Sheetsにアップロード中...")
        
        success = upload_to_sheets(
            commit_data=commit_data,
            config=config,
            clear_existing=args.clear_sheet
        )
        
        if not success:
            print("Google Sheetsへのアップロードに失敗しました")
            return 1
        
        print("処理が完了しました")
    else:
        print("データ収集のみ完了しました（アップロードはスキップ）")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
