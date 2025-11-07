import os
import json
import time
from typing import Dict, Any, List


def ensure_reports_dir(path: str = "logs/reports") -> str:
    os.makedirs(path, exist_ok=True)
    return path


def write_report(report: Dict[str, Any], filename: str = None, dir_path: str = "logs/reports") -> str:
    """Write consolidated report to a JSON file and return the path."""
    ensure_reports_dir(dir_path)
    if filename is None:
        timestamp = int(time.time())
        filename = f"report_{timestamp}.json"

    report_path = os.path.join(dir_path, filename)
    with open(report_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)

    return report_path


def consolidate_matches(matches: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Simple consolidation: group by file and summarize scores."""
    summary = {}
    for m in matches:
        fp = m.get("file_path")
        if fp not in summary:
            summary[fp] = {
                "file_path": fp,
                "scores": [],
                "queries": [],
                "content_snippet": (m.get("content") or "")[:500],
            }
        summary[fp]["scores"].append(m.get("score", 0.0))
        q = m.get("query")
        if q and q not in summary[fp]["queries"]:
            summary[fp]["queries"].append(q)

    # compute aggregated score
    consolidated = []
    for fp, data in summary.items():
        avg_score = sum(data["scores"]) / max(1, len(data["scores"]))
        consolidated.append(
            {
                "file_path": fp,
                "avg_score": avg_score,
                "queries": data["queries"],
                "content_snippet": data["content_snippet"],
            }
        )

    # sort by avg_score desc
    consolidated.sort(key=lambda x: x["avg_score"], reverse=True)

    return {"total_files": len(consolidated), "files": consolidated}
