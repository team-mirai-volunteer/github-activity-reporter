# GitHub Activity Reporter

GitHub活動をAIレポート用にまとめるシステム

## 概要

このツールは、team-mirai-volunteer組織の以下のリポジトリのGitHub活動データを収集し、AIが処理しやすいMarkdown形式でレポートを生成します：

- `team-mirai-volunteer/action-board` - アクションボード（ゲーミフィケーション政治参加プラットフォーム）
- `team-mirai-volunteer/fact-checker` - ファクトチェッカー（Twitter/X投稿のリアルタイムファクトチェックシステム）

## 機能

- GitHub APIを使用したissue/PRデータの自動収集
- JSON形式でのデータ保存
- AIが処理しやすいMarkdown形式でのレポート生成
- 週次自動実行（GitHub Actions）
- リポジトリ固有のプロンプトファイル対応

## セットアップ

### 必要な環境

- Python 3.8以上
- GitHub CLI (`gh`)
- OpenAI API キー（オプション）

### インストール

1. リポジトリをクローン
```bash
git clone https://github.com/team-mirai-volunteer/github-activity-reporter.git
cd github-activity-reporter
```

2. 依存関係をインストール
```bash
pip install -r requirements.txt
```

3. 環境変数を設定
```bash
cp .env.example .env
# .envファイルを編集してAPIキーを設定
```

## 使用方法

### 基本的な使用方法

```bash
# action-boardリポジトリの活動データを収集
python -m src.github_logger.github_report --repo team-mirai-volunteer/action-board --markdown

# fact-checkerリポジトリの活動データを収集
python -m src.github_logger.github_report --repo team-mirai-volunteer/fact-checker --markdown

# 両方のリポジトリを同時に処理
python -m src.github_logger.github_report --repo team-mirai-volunteer/action-board,team-mirai-volunteer/fact-checker --markdown
```

### OpenAI APIを使用したレポート生成

```bash
# action-board用のAIレポート生成
python -m src.call_openai_api github --repo "team-mirai-volunteer/action-board" --prompt-file "./prompts/action_board_prompt.txt"

# fact-checker用のAIレポート生成
python -m src.call_openai_api github --repo "team-mirai-volunteer/fact-checker" --prompt-file "./prompts/fact_checker_prompt.txt"
```

## プロジェクト構造

```
github-activity-reporter/
├── README.md
├── requirements.txt
├── .env.example
├── .github/workflows/
│   └── weekly-report.yml
├── src/
│   ├── __init__.py
│   ├── github_logger/
│   │   ├── __init__.py
│   │   ├── github_report.py
│   │   └── prompt.txt
│   ├── call_openai_api.py
│   └── utils/
│       ├── __init__.py
│       ├── config.py
│       └── file_utils.py
├── prompts/
│   ├── action_board_prompt.txt
│   └── fact_checker_prompt.txt
└── data/
    └── .gitkeep
```

## 設定

### 環境変数

- `GITHUB_TOKEN`: GitHub APIアクセス用トークン
- `OPENAI_API_KEY`: OpenAI APIキー（オプション）

### プロンプトファイル

各リポジトリ用のプロンプトファイルを `prompts/` ディレクトリに配置します。これらのファイルは、AIがGitHub活動データを解析する際の指示を含みます。

## 自動実行

GitHub Actionsを使用して週次でレポートを自動生成します。設定は `.github/workflows/weekly-report.yml` を参照してください。

## コントリビュート

プロジェクトへのコントリビュートを歓迎します。Issue の作成や Pull Request の提出をお気軽にどうぞ。

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。
