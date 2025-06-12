"""
OpenAI API呼び出しモジュール
"""
import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import openai
except ImportError:
    print("OpenAI パッケージがインストールされていません。pip install openai を実行してください。")
    sys.exit(1)

from .utils.config import Config
from .utils.file_utils import ensure_dir, read_json_file, read_text_file, write_text_file


def call_openai_api(
    prompt: str,
    model: str = "gpt-4",
    max_tokens: Optional[int] = None,
    temperature: float = 0.7
) -> Tuple[str, Dict[str, Any]]:
    """
    OpenAI APIを呼び出す
    
    Args:
        prompt: プロンプト
        model: 使用するモデル
        max_tokens: 最大トークン数
        temperature: 温度パラメータ
        
    Returns:
        レスポンステキストとコスト情報
    """
    try:
        client = openai.OpenAI()
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        content = response.choices[0].message.content
        
        usage = response.usage
        cost_info = {
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
            "model": model
        }
        
        return content, cost_info
        
    except Exception as e:
        print(f"OpenAI API呼び出しエラー: {e}")
        return "", {}


def process_github_data(
    repo: str,
    data_dir: str,
    prompt_file: str,
    output_dir: Optional[str] = None,
    model: str = "gpt-4",
    max_tokens: Optional[int] = None
) -> Optional[str]:
    """
    GitHubデータを処理してAIレポートを生成
    
    Args:
        repo: リポジトリ名
        data_dir: データディレクトリ
        prompt_file: プロンプトファイルのパス
        output_dir: 出力ディレクトリ
        model: 使用するモデル
        max_tokens: 最大トークン数
        
    Returns:
        生成されたレポートファイルのパス
    """
    try:
        prompt_template = read_text_file(prompt_file)
    except FileNotFoundError:
        print(f"プロンプトファイルが見つかりません: {prompt_file}")
        return None
    
    data_path = Path(data_dir)
    repo_name = repo.split("/")[1] if "/" in repo else repo
    
    github_data_files = list(data_path.glob(f"*/raw/github/{repo_name}.json"))
    
    if not github_data_files:
        print(f"GitHubデータファイルが見つかりません: {repo_name}.json")
        return None
    
    latest_file = max(github_data_files, key=lambda x: x.stat().st_mtime)
    print(f"処理対象ファイル: {latest_file}")
    
    github_data = read_json_file(latest_file)
    
    if not github_data:
        print(f"GitHubデータが空です: {latest_file}")
        return None
    
    github_data_json = json.dumps(github_data, ensure_ascii=False, indent=2)
    
    full_prompt = prompt_template + "\n\n" + github_data_json
    
    print(f"OpenAI APIを呼び出し中... (モデル: {model})")
    
    response, cost_info = call_openai_api(
        prompt=full_prompt,
        model=model,
        max_tokens=max_tokens
    )
    
    if not response:
        print("OpenAI APIからのレスポンスが空です")
        return None
    
    if not output_dir:
        date_range_dir = latest_file.parent.parent.parent.name
        output_dir = str(latest_file.parent.parent.parent / "ai_reports")
    
    ensure_dir(output_dir)
    
    output_file = Path(output_dir) / f"ai_report-{repo_name}.md"
    
    write_text_file(response, output_file)
    
    print(f"AIレポートを保存しました: {output_file}")
    
    if cost_info:
        print(f"使用トークン数: {cost_info.get('total_tokens', 'N/A')}")
        print(f"プロンプトトークン: {cost_info.get('prompt_tokens', 'N/A')}")
        print(f"完了トークン: {cost_info.get('completion_tokens', 'N/A')}")
    
    return str(output_file)


def main() -> int:
    """
    メイン関数
    
    Returns:
        終了コード
    """
    config = Config()
    
    parser = argparse.ArgumentParser(description='OpenAI APIを使用してGitHubデータからAIレポートを生成')
    
    subparsers = parser.add_subparsers(dest='command', help='コマンド')
    
    github_parser = subparsers.add_parser('github', help='GitHubデータを処理')
    github_parser.add_argument('--repo', required=True, help='リポジトリ名（owner/repo形式）')
    github_parser.add_argument('--data-dir', help='データディレクトリ', 
                              default=config.get("output.default_dir", "./data"))
    github_parser.add_argument('--prompt-file', required=True, help='プロンプトファイルのパス')
    github_parser.add_argument('--output-dir', help='出力ディレクトリ')
    github_parser.add_argument('--model', help='使用するOpenAIモデル', default="gpt-4")
    github_parser.add_argument('--max-tokens', type=int, help='最大トークン数')
    github_parser.add_argument('--config', help='設定ファイルのパス')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    if args.config:
        config = Config(config_file=args.config)
    
    api_key = config.get("openai.api_key")
    if not api_key:
        print("エラー: OPENAI_API_KEY が設定されていません")
        print("環境変数またはconfigファイルでAPIキーを設定してください")
        return 1
    
    os.environ["OPENAI_API_KEY"] = api_key
    
    if args.command == 'github':
        result = process_github_data(
            repo=args.repo,
            data_dir=args.data_dir,
            prompt_file=args.prompt_file,
            output_dir=args.output_dir,
            model=args.model,
            max_tokens=args.max_tokens
        )
        
        if result:
            print(f"処理完了: {result}")
            return 0
        else:
            print("処理に失敗しました")
            return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
