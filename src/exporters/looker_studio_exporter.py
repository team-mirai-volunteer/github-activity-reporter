"""
Looker Studio用データエクスポートモジュール
"""
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import subprocess

from ..utils.file_utils import read_json_file, write_json_file, ensure_dir

try:
    from ..utils.config import Config
except ImportError:
    Config = type(None)

class LookerStudioExporter:
    """Looker Studio用データエクスポートクラス"""
    
    def __init__(self, config: Optional[Any] = None):
        self.config = config
        self.pr_data_dir = Path("../pr-data/prs")
        self.devin_stat_dir = Path("../devin-stat")
        
    def collect_github_activity_data(self, days: int = 30) -> List[Dict[str, Any]]:
        """GitHub活動データを収集"""
        data_dir = Path("./data")
        activity_data = []
        
        for repo_file in data_dir.glob("*/raw/github/*.json"):
            repo_data = read_json_file(repo_file)
            for item in repo_data:
                activity_data.append({
                    "source": "github_activity",
                    "repository": repo_file.stem,
                    "type": item.get("type", "unknown"),
                    "title": item.get("title", ""),
                    "state": item.get("state", ""),
                    "created_at": item.get("created_at", ""),
                    "updated_at": item.get("updated_at", ""),
                    "user": item.get("user", {}).get("login", ""),
                    "labels": [label.get("name", "") for label in item.get("labels", [])],
                    "comments_count": len(item.get("comments", [])),
                })
        
        return activity_data
    
    def collect_devin_stats_data(self) -> List[Dict[str, Any]]:
        """Devin統計データを収集"""
        devin_data = []
        
        usage_file = self.devin_stat_dir / "data/usage_history.json"
        if usage_file.exists():
            usage_data = read_json_file(usage_file)
            if isinstance(usage_data, list) and len(usage_data) > 0:
                usage_dict = usage_data[0] if isinstance(usage_data[0], dict) else {}
                if "data" in usage_dict:
                    for session in usage_dict["data"]:
                        devin_data.append({
                            "source": "devin_usage",
                            "session_name": session.get("session", ""),
                            "created_at": session.get("created_at", ""),
                            "acus_used": session.get("acus_used", 0),
                            "type": "usage"
                        })
        
        if self.pr_data_dir.exists():
            devin_patterns = ["devin-ai-integration[bot]", "devin-ai-integration", "devin"]
            for pr_file in self.pr_data_dir.glob("*.json"):
                pr_data = read_json_file(pr_file)
                if isinstance(pr_data, list) and pr_data:
                    pr_data = pr_data[0]
                
                if isinstance(pr_data, dict):
                    user_login = pr_data.get("basic_info", {}).get("user", {}).get("login", "")
                    if any(pattern in user_login.lower() for pattern in devin_patterns):
                        devin_data.append({
                            "source": "devin_pr",
                            "pr_number": pr_data.get("basic_info", {}).get("number", 0),
                            "title": pr_data.get("basic_info", {}).get("title", ""),
                            "state": pr_data.get("basic_info", {}).get("state", ""),
                            "created_at": pr_data.get("basic_info", {}).get("created_at", ""),
                            "merged_at": pr_data.get("basic_info", {}).get("merged_at", ""),
                            "type": "devin_pr"
                        })
        
        return devin_data
    
    def collect_pr_data_stats(self, days: int = 30) -> List[Dict[str, Any]]:
        """PR統計データを収集"""
        pr_stats = []
        cutoff_date = datetime.now() - timedelta(days=days)
        
        if not self.pr_data_dir.exists():
            return pr_stats
        
        total_prs = 0
        merged_prs = 0
        open_prs = 0
        
        for pr_file in self.pr_data_dir.glob("*.json"):
            pr_data = read_json_file(pr_file)
            if isinstance(pr_data, list) and pr_data:
                pr_data = pr_data[0]
            
            if isinstance(pr_data, dict):
                created_at = pr_data.get("basic_info", {}).get("created_at", "")
                if created_at:
                    try:
                        pr_date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                        if pr_date >= cutoff_date:
                            total_prs += 1
                            state = pr_data.get("basic_info", {}).get("state", "")
                            if state == "closed" and pr_data.get("basic_info", {}).get("merged_at"):
                                merged_prs += 1
                            elif state == "open":
                                open_prs += 1
                    except:
                        continue
        
        pr_stats.append({
            "source": "pr_statistics",
            "type": "summary",
            "period_days": days,
            "total_prs": total_prs,
            "merged_prs": merged_prs,
            "open_prs": open_prs,
            "merge_rate": merged_prs / total_prs if total_prs > 0 else 0,
            "generated_at": datetime.now().isoformat()
        })
        
        return pr_stats
    
    def generate_unified_export(self, output_file: str = "looker_studio_data.json", days: int = 30) -> Dict[str, Any]:
        """統合データをエクスポート"""
        print("GitHub活動データを収集中...")
        github_data = self.collect_github_activity_data(days)
        
        print("Devin統計データを収集中...")
        devin_data = self.collect_devin_stats_data()
        
        print("PR統計データを収集中...")
        pr_stats = self.collect_pr_data_stats(days)
        
        unified_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "period_days": days,
                "data_sources": ["github_activity", "devin_stats", "pr_data"],
                "total_records": len(github_data) + len(devin_data) + len(pr_stats)
            },
            "github_activity": github_data,
            "devin_stats": devin_data,
            "pr_statistics": pr_stats,
            "summary": {
                "github_items": len(github_data),
                "devin_sessions": len([d for d in devin_data if d["source"] == "devin_usage"]),
                "devin_prs": len([d for d in devin_data if d["source"] == "devin_pr"]),
                "pr_stats_records": len(pr_stats)
            }
        }
        
        output_path = Path("./data") / output_file
        ensure_dir(output_path.parent)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(unified_data, f, ensure_ascii=False, indent=2)
        
        print(f"統合データを {output_path} に保存しました")
        print(f"総レコード数: {unified_data['metadata']['total_records']}")
        
        return unified_data
    
    def export_for_google_sheets(self, output_file: str = "looker_studio_flat.json") -> str:
        """Google Sheets用にフラット化されたデータをエクスポート"""
        unified_data = self.generate_unified_export()
        
        flat_records = []
        
        for item in unified_data["github_activity"]:
            flat_records.append({
                "source_type": "github_activity",
                "repository": item.get("repository", ""),
                "item_type": item.get("type", ""),
                "title": item.get("title", ""),
                "state": item.get("state", ""),
                "created_at": item.get("created_at", ""),
                "updated_at": item.get("updated_at", ""),
                "user": item.get("user", ""),
                "labels": "|".join(item.get("labels", [])),
                "comments_count": item.get("comments_count", 0),
                "numeric_value": item.get("comments_count", 0)
            })
        
        for item in unified_data["devin_stats"]:
            flat_records.append({
                "source_type": "devin_stats",
                "repository": "",
                "item_type": item.get("type", ""),
                "title": item.get("session_name", "") or f"PR #{item.get('pr_number', '')}",
                "state": item.get("state", ""),
                "created_at": item.get("created_at", ""),
                "updated_at": "",
                "user": "devin",
                "labels": "",
                "comments_count": 0,
                "numeric_value": item.get("acus_used", 0) or item.get("pr_number", 0)
            })
        
        for item in unified_data["pr_statistics"]:
            flat_records.append({
                "source_type": "pr_statistics",
                "repository": "team-mirai/policy",
                "item_type": "summary",
                "title": f"PR Statistics ({item.get('period_days', 0)} days)",
                "state": "summary",
                "created_at": item.get("generated_at", ""),
                "updated_at": "",
                "user": "system",
                "labels": "",
                "comments_count": item.get("total_prs", 0),
                "numeric_value": item.get("merge_rate", 0)
            })
        
        output_path = Path("./data") / output_file
        ensure_dir(output_path.parent)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(flat_records, f, ensure_ascii=False, indent=2)
        
        print(f"Google Sheets用フラットデータを {output_path} に保存しました")
        print(f"レコード数: {len(flat_records)}")
        
        return str(output_path)
