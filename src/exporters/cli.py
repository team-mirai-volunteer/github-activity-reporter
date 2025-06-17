"""
Looker Studioエクスポート用CLI
"""
import argparse
from pathlib import Path
from .looker_studio_exporter import LookerStudioExporter

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="Looker Studio用データエクスポート")
    parser.add_argument(
        "--output-file",
        default="looker_studio_data.json",
        help="出力ファイル名"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="過去何日分のデータを含めるか"
    )
    parser.add_argument(
        "--format",
        choices=["unified", "flat"],
        default="flat",
        help="出力形式（unified: 構造化JSON, flat: Google Sheets用フラット形式）"
    )
    parser.add_argument(
        "--output-dir",
        default="./data",
        help="出力ディレクトリ"
    )
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    exporter = LookerStudioExporter()
    
    try:
        if args.format == "unified":
            output_file = args.output_file
            exporter.generate_unified_export(output_file, args.days)
            print(f"✅ エクスポート完了: {output_dir / output_file}")
        else:
            output_file = args.output_file.replace(".json", "_flat.json")
            result_path = exporter.export_for_google_sheets(output_file)
            print(f"✅ エクスポート完了: {result_path}")
        
    except Exception as e:
        print(f"❌ エクスポートエラー: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
