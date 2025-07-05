"""
GitHub活動データ収集モジュール
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from ..utils.config import Config
from ..utils.file_utils import ensure_dir, read_json_file, write_json_file, write_text_file
from ..utils.user_mapping import map_username


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


def extract_username_from_email(email: str) -> str:
    """
    メールアドレスからユーザー名を抽出
    
    Args:
        email: メールアドレス
        
    Returns:
        ユーザー名
    """
    if not email:
        return "unknown"
    
    if email.endswith("@users.noreply.github.com"):
        parts = email.split("@")[0].split("+")
        if len(parts) > 1:
            return parts[1]
        else:
            return parts[0]
    else:
        return email.split("@")[0]


def extract_github_data(
    repo: str,
    output_dir: str = "./data",
    last_days: int = 7,
    include_prs: bool = True,
    timezone_str: str = "UTC"
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    GitHubからissueとPRデータを抽出
    
    Args:
        repo: リポジトリ名（owner/repo形式）
        output_dir: 出力ディレクトリ
        last_days: 過去何日分を取得するか
        include_prs: PRを含めるかどうか
        timezone_str: タイムゾーン
        
    Returns:
        抽出結果の辞書とJSONファイルパス
    """
    token = get_github_token()
    if not token:
        return None, None
    
    tz = timezone.utc if timezone_str == "UTC" else timezone(timedelta(hours=9))
    end_date = datetime.now(tz)
    start_date = end_date - timedelta(days=last_days)
    
    date_range_dir = f"{start_date.date().isoformat()}_to_{end_date.date().isoformat()}"
    
    output_path = Path(output_dir) / date_range_dir
    github_raw_dir = output_path / "raw" / "github"
    ensure_dir(github_raw_dir)
    
    repo_name = repo.split("/")[1]
    
    print(f"リポジトリ {repo} からissueデータを取得中...")
    
    issue_cmd = [
        'gh', 'issue', 'list',
        '--repo', repo,
        '--state', 'all',
        '--limit', '1000',
        '--json', 'number,title,body,state,createdAt,updatedAt,closedAt,author,assignees,labels,comments,url'
    ]
    
    try:
        result = subprocess.run(issue_cmd, capture_output=True, text=True, check=True)
        all_issues = json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"issueデータの取得に失敗しました: {e}")
        all_issues = []
    
    all_prs = []
    if include_prs:
        print(f"リポジトリ {repo} からPRデータを取得中...")
        
        pr_cmd = [
            'gh', 'pr', 'list',
            '--repo', repo,
            '--state', 'all',
            '--limit', '1000',
            '--json', 'number,title,body,state,createdAt,updatedAt,closedAt,mergedAt,author,assignees,labels,comments,url,mergeable,additions,deletions,changedFiles'
        ]
        
        try:
            result = subprocess.run(pr_cmd, capture_output=True, text=True, check=True)
            all_prs = json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"PRデータの取得に失敗しました: {e}")
            all_prs = []
    
    all_data = all_issues + all_prs
    
    github_file = github_raw_dir / f"{repo_name}.json"
    write_json_file(all_data, github_file)
    
    print(f"{len(all_issues)}件のissueと{len(all_prs)}件のPRを {github_file} に保存しました")
    
    result = {
        "repo": repo,
        "period": {
            "start": start_date.date().isoformat(),
            "end": end_date.date().isoformat(),
            "days": last_days
        },
        "counts": {
            "issues": len(all_issues),
            "prs": len(all_prs),
            "total": len(all_data)
        },
        "file": str(github_file)
    }
    
    summary_file = github_raw_dir / f"{repo_name}_summary.json"
    write_json_file([result], summary_file)
    
    print(f"抽出結果の概要を {summary_file} に保存しました")
    
    return result, str(github_file)


def format_item(item: Dict[str, Any]) -> str:
    """
    アイテムをMarkdown形式でフォーマット
    
    Args:
        item: issue/PRデータ
        
    Returns:
        フォーマットされた文字列
    """
    item_type = "PR" if "mergeable" in item else "Issue"
    number = item.get("number", "N/A")
    title = item.get("title", "タイトルなし")
    state = item.get("state", "unknown")
    author = map_username(item.get("author", {}).get("login", "unknown") if item.get("author") else "unknown")
    created_at = item.get("createdAt", "")
    updated_at = item.get("updatedAt", "")
    url = item.get("url", "")
    
    created_date = ""
    if created_at:
        try:
            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            created_date = dt.strftime("%Y-%m-%d")
        except ValueError:
            created_date = created_at[:10] if len(created_at) >= 10 else created_at
    
    updated_date = ""
    if updated_at:
        try:
            dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            updated_date = dt.strftime("%Y-%m-%d")
        except ValueError:
            updated_date = updated_at[:10] if len(updated_at) >= 10 else updated_at
    
    labels = []
    if item.get("labels"):
        labels = [label.get("name", "") for label in item["labels"] if label.get("name")]
    
    comment_count = len(item.get("comments", []))
    
    formatted = f"## {item_type} #{number}: {title}\n\n"
    formatted += f"- **状態**: {state}\n"
    formatted += f"- **作成者**: {author}\n"
    formatted += f"- **作成日**: {created_date}\n"
    formatted += f"- **更新日**: {updated_date}\n"
    
    if labels:
        formatted += f"- **ラベル**: {', '.join(labels)}\n"
    
    if comment_count > 0:
        formatted += f"- **コメント数**: {comment_count}\n"
    
    formatted += f"- **URL**: {url}\n\n"
    
    body = item.get("body", "")
    if body:
        body_preview = body[:200] + "..." if len(body) > 200 else body
        formatted += f"**概要**:\n{body_preview}\n\n"
    
    if item_type == "PR":
        if item.get("mergedAt"):
            merged_date = ""
            try:
                dt = datetime.fromisoformat(item["mergedAt"].replace('Z', '+00:00'))
                merged_date = dt.strftime("%Y-%m-%d")
            except ValueError:
                merged_date = item["mergedAt"][:10] if len(item["mergedAt"]) >= 10 else item["mergedAt"]
            formatted += f"- **マージ日**: {merged_date}\n"
        
        additions = item.get("additions", 0)
        deletions = item.get("deletions", 0)
        changed_files = item.get("changedFiles", 0)
        
        if additions or deletions or changed_files:
            formatted += f"- **変更**: +{additions} -{deletions} ({changed_files}ファイル)\n"
    
    formatted += "\n---\n\n"
    
    return formatted


def generate_markdown(
    items: List[Dict[str, Any]],
    repo: str,
    start_date: str,
    end_date: str,
    output_file: Optional[Union[str, Path]] = None
) -> str:
    """
    Markdownレポートを生成
    
    Args:
        items: issue/PRデータのリスト
        repo: リポジトリ名
        start_date: 開始日
        end_date: 終了日
        output_file: 出力ファイルパス
        
    Returns:
        生成されたMarkdown
    """
    repo_name = repo.split("/")[-1] if "/" in repo else repo
    
    markdown_report = f"# {repo_name} GitHub活動レポート ({start_date} ~ {end_date})\n\n"
    
    if not items:
        markdown_report += "この期間中に活動はありませんでした。\n"
        if output_file:
            write_text_file(markdown_report, output_file)
            print(f"レポートは {output_file} に保存されました。")
        return markdown_report
    
    issues = [item for item in items if "mergeable" not in item]
    prs = [item for item in items if "mergeable" in item]
    
    markdown_report += f"## 概要\n\n"
    markdown_report += f"- **総アイテム数**: {len(items)}\n"
    markdown_report += f"- **Issue数**: {len(issues)}\n"
    markdown_report += f"- **PR数**: {len(prs)}\n\n"
    
    open_items = [item for item in items if item.get("state") == "open"]
    closed_items = [item for item in items if item.get("state") == "closed"]
    merged_prs = [item for item in prs if item.get("state") == "merged"]
    
    markdown_report += f"### 状態別統計\n\n"
    markdown_report += f"- **オープン**: {len(open_items)}\n"
    markdown_report += f"- **クローズ**: {len(closed_items)}\n"
    if merged_prs:
        markdown_report += f"- **マージ済みPR**: {len(merged_prs)}\n"
    markdown_report += "\n"
    
    sorted_items = sorted(items, key=lambda x: x.get("updatedAt", ""), reverse=True)
    
    markdown_report += f"## 詳細\n\n"
    
    for item in sorted_items:
        markdown_report += format_item(item)
    
    if output_file:
        write_text_file(markdown_report, output_file)
        print(f"レポートは {output_file} に保存されました。")
    
    return markdown_report


def generate_markdown_from_file(
    json_file: Union[str, Path], 
    output_file: Optional[Union[str, Path]] = None,
    timezone_str: str = "UTC"
) -> Optional[str]:
    """
    JSONファイルからMarkdownレポートを生成
    
    Args:
        json_file: JSONファイルのパス
        output_file: 出力ファイル名（指定しない場合はリポジトリ名から自動生成）
        timezone_str: タイムゾーン名
        
    Returns:
        生成されたMarkdown
    """
    items = read_json_file(json_file)
    
    if not items:
        print(f"{json_file} にデータが見つかりませんでした")
        return None
    
    repo = "unknown-repo"
    if items and isinstance(items[0], dict) and "url" in items[0]:
        url = items[0]["url"]
        if "github.com" in url:
            parts = url.split("/")
            if len(parts) >= 5:
                repo = "/".join(parts[3:5])
    
    tz = timezone.utc if timezone_str == "UTC" else timezone(timedelta(hours=9))
    end_date = datetime.now(tz)
    start_date = end_date - timedelta(days=7)
    
    if not output_file:
        repo_name = repo.split("/")[1] if "/" in repo else repo
        json_file_path = Path(json_file)
        
        try:
            date_range_dir = json_file_path.parent.parent.parent.name
            if not '_to_' in date_range_dir:
                date_range_dir = f"{start_date.date().isoformat()}_to_{end_date.date().isoformat()}"
                
            base_path = json_file_path.parent
            while base_path.name != date_range_dir and str(base_path) != '/':
                base_path = base_path.parent
            
            if str(base_path) == '/':
                base_path = json_file_path.parent.parent.parent
            else:
                base_path = base_path.parent
                
            markdown_dir = base_path / date_range_dir / "markdown" / "github"
            ensure_dir(markdown_dir)
            output_file = markdown_dir / f"github_report-{repo_name}.md"
        except (IndexError, ValueError):
            date_range_dir = f"{start_date.date().isoformat()}_to_{end_date.date().isoformat()}"
            markdown_dir = Path(json_file).parent.parent / "markdown" / "github"
            ensure_dir(markdown_dir)
            output_file = markdown_dir / f"github_report-{repo_name}.md"
    
    return generate_markdown(
        items=items,
        repo=repo,
        start_date=start_date.date().isoformat(),
        end_date=end_date.date().isoformat(),
        output_file=output_file
    )


def main() -> int:
    """
    メイン関数
    
    Returns:
        int: 終了コード（0: 成功, 1: 失敗）
    """
    config = Config()
    
    parser = argparse.ArgumentParser(description='GitHubのissueとPRデータを抽出してレポートを生成するツール')
    
    repo_group = parser.add_argument_group('リポジトリ指定')
    repo_group.add_argument('--repo', help='リポジトリ名（owner/repo形式、またはカンマ区切りで複数指定可能）', required=True)
    repo_group.add_argument('--org', help='組織名（--repo で指定したリポジトリ名の前に付与される）')
    
    parser.add_argument('--output-dir', help='出力ディレクトリ', default=config.get("output.default_dir", "./data"))
    parser.add_argument('--last-days', type=int, help='過去何日分を取得するか', default=7)
    parser.add_argument('--no-prs', action='store_true', help='PRを含めない')
    parser.add_argument('--markdown', action='store_true', help='Markdownレポートも生成する')
    parser.add_argument('--output', help='Markdownレポートの出力ファイル名（指定しない場合はリポジトリ名から自動生成）')
    parser.add_argument('--json-file', help='既存のJSONファイルからMarkdownレポートを生成する場合に指定')
    parser.add_argument('--timezone', help='タイムゾーン', default=config.get("output.timezone", "UTC"))
    parser.add_argument('--config', help='設定ファイルのパス')
    
    args = parser.parse_args()
    
    if args.config:
        config = Config(config_file=args.config)
    
    timezone_str = args.timezone or config.get("output.timezone", "UTC")
    
    if args.json_file:
        if not Path(args.json_file).exists():
            print(f"エラー: JSONファイルが見つかりません: {args.json_file}")
            return 1
        
        generate_markdown_from_file(
            json_file=args.json_file,
            output_file=args.output,
            timezone_str=timezone_str
        )
        return 0
    
    repos = []
    raw_repos = [repo.strip() for repo in args.repo.split(',')]
    
    for repo in raw_repos:
        if '/' in repo:
            repos.append(repo)  # すでに owner/repo 形式の場合はそのまま
        elif args.org:
            repos.append(f"{args.org}/{repo}")  # 組織名を付与
        else:
            print(f"エラー: リポジトリ '{repo}' に組織名が指定されていません。--org オプションを使用するか、owner/repo 形式で指定してください。")
            return 1
    
    print(f"処理対象リポジトリ: {repos}")
    
    output_dir = args.output_dir or config.get("output.default_dir", "./data")
    
    tz = timezone.utc if timezone_str == "UTC" else timezone(timedelta(hours=9))
    end_date = datetime.now(tz)
    start_date = end_date - timedelta(days=args.last_days)
    date_range_dir = f"{start_date.date().isoformat()}_to_{end_date.date().isoformat()}"
    
    all_results = []
    all_items = []
    
    for repo in repos:
        result, json_file = extract_github_data(
            repo=repo,
            output_dir=output_dir,
            last_days=args.last_days,
            include_prs=not args.no_prs,
            timezone_str=timezone_str
        )
        
        if result:
            all_results.append(result)
            
            if args.markdown:
                repo_name = repo.split("/")[1]
                
                if not args.output:
                    markdown_dir = Path(output_dir) / date_range_dir / "markdown" / "github"
                    ensure_dir(markdown_dir)
                    output_file = markdown_dir / f"github_report-{repo_name}.md"
                else:
                    if len(repos) > 1:
                        output_path = Path(args.output)
                        base, ext = output_path.stem, output_path.suffix
                        output_file = output_path.with_name(f"{base}-{repo_name}{ext}")
                    else:
                        output_file = args.output
                
                items = []
                if json_file and Path(json_file).exists():
                    items = read_json_file(json_file)
                    all_items.extend(items)
                
                generate_markdown(
                    items=items,
                    repo=repo,
                    start_date=result["period"]["start"],
                    end_date=result["period"]["end"],
                    output_file=output_file
                )
    
    if len(repos) > 1 and all_items and args.markdown:
        markdown_dir = Path(output_dir) / date_range_dir / "markdown" / "github"
        ensure_dir(markdown_dir)
        combined_output = markdown_dir / "github_report-combined.md"
        
        repo_names = [r.split("/")[1] for r in repos]
        combined_repo_name = ", ".join(repo_names)
        
        generate_markdown(
            items=all_items,
            repo=combined_repo_name,
            start_date=start_date.date().isoformat(),
            end_date=end_date.date().isoformat(),
            output_file=combined_output
        )
        
        print(f"まとめレポートは {combined_output} に保存されました。")
    
    return 0


if __name__ == "__main__":
    exit(main())
