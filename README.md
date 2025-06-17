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

## Looker Studio連携

### 概要

このシステムは、GitHub活動データ、Devin統計、PR統計を統合してLooker Studio用にエクスポートする機能を提供します。

### データソース

- **GitHub Activity**: action-board、fact-checkerリポジトリのissue/PR活動
- **Devin Statistics**: Devin AIの使用統計とPR作成履歴
- **PR Statistics**: team-mirai/policyリポジトリのPR統計

### 使用方法

#### 手動エクスポート

```bash
# Google Sheets用フラット形式（推奨）
python -m src.exporters.cli --format flat --days 30

# 構造化JSON形式
python -m src.exporters.cli --format unified --days 30
```

#### 自動エクスポート

GitHub Actionsワークフローにより、週次で自動的にLooker Studio用データが生成されます。

### Looker Studioでの可視化設定

1. **データソースの設定**
   - Google Sheetsに生成されたJSONファイルをインポート
   - Looker StudioでGoogle Sheetsをデータソースとして接続

2. **推奨ダッシュボード構成**
   - プロジェクト活動概要（PR数、issue数、マージ率）
   - 貢献者活動（ユーザー別活動、Devin使用状況）
   - 時系列トレンド（週別/月別活動推移）
   - ラベル別分析（プロジェクト分野別活動）

3. **主要メトリクス**
   - **活動指標**: PR作成数、issue作成数、コメント数
   - **品質指標**: マージ率、レビュー時間、クローズ率
   - **参加指標**: アクティブ貢献者数、新規参加者数
   - **Devin活用**: セッション数、ACU使用量、PR成功率

### データ更新頻度

- **GitHub Actions**: 週次自動更新
- **手動実行**: 必要に応じて随時実行可能
- **データ保持**: 90日間のアーティファクト保持

### トラブルシューティング

データが正しく生成されない場合：

1. 依存リポジトリの確認
   ```bash
   # pr-dataリポジトリの存在確認
   ls -la ../pr-data/prs/
   
   # devin-statリポジトリの存在確認
   ls -la ../devin-stat/data/
   ```

2. 権限の確認
   - GITHUB_TOKENが正しく設定されているか
   - 各リポジトリへのアクセス権限があるか

3. ログの確認
   - GitHub Actionsのログを確認
   - エラーメッセージの詳細を確認

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
│   ├── exporters/
│   │   ├── __init__.py
│   │   ├── looker_studio_exporter.py
│   │   └── cli.py
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
