"""GUIDE Phần 6e - Lặp để đo nhiễu: tổng hợp nhiều thư mục kết quả của cùng các điều kiện trên tác vụ đánh giá.

Chạy:  python -m lab.noise results results-rep2 results-rep3 > report/noise.md

Mỗi thư mục là một lần lặp độc lập (cùng mã, cùng skill đã đóng băng). Với mỗi điều kiện và tác vụ đánh giá,
in số check đạt ở từng lần lặp, trung bình và khoảng dao động; rồi tổng hợp theo điều kiện
(check kỹ thuật, check quy ước `rule_`, token).
"""
import json
import sys
from pathlib import Path

from .runner import CONDITIONS
from .tasks import list_tasks


def load(results_dirs, role="eval"):
    """{condition: {task: [run.json của từng lần lặp, None nếu thiếu]}}."""
    tasks = [t.id for t in list_tasks(role)]
    data = {}
    for condition in CONDITIONS:
        data[condition] = {}
        for task in tasks:
            runs = []
            for d in results_dirs:
                f = Path(d) / condition / task / "run.json"
                runs.append(json.loads(f.read_text(encoding="utf-8")) if f.exists() else None)
            data[condition][task] = runs
    return data


def _mean(values):
    return sum(values) / len(values) if values else float("nan")


def _split(run):
    """(kỹ thuật đạt, kỹ thuật tổng, quy ước đạt, quy ước tổng) của một lần chạy."""
    rule = [c for c in run["checks"] if c["name"].startswith("rule_")]
    tech = [c for c in run["checks"] if not c["name"].startswith("rule_")]
    return sum(c["passed"] for c in tech), len(tech), sum(c["passed"] for c in rule), len(rule)


def render(results_dirs) -> str:
    data = load(results_dirs)
    n = len(results_dirs)
    lines = [f"Lần lặp: {', '.join(f'`{d}`' for d in results_dirs)}", ""]

    lines += ["| Điều kiện | Tác vụ | " + " | ".join(f"Lần {i + 1}" for i in range(n)) + " | Trung bình | Thấp nhất - cao nhất | Check đổi kết quả giữa các lần |",
              "|---|---|" + "---|" * n + "---|---|---|"]
    for condition, tasks in data.items():
        for task, runs in tasks.items():
            done = [r for r in runs if r]
            passed = [r["passed"] for r in done]
            cells = [f"{r['passed']}/{r['total']}" + (" (lỗi)" if r["error"] else "") if r else "-" for r in runs]
            # check không cho cùng một kết quả ở mọi lần lặp
            outcomes = {}
            for r in done:
                for c in r["checks"]:
                    outcomes.setdefault(c["name"], set()).add(bool(c["passed"]))
            unstable = sorted(name for name, seen in outcomes.items() if len(seen) > 1)
            lines.append(f"| {condition} | {task} | " + " | ".join(cells)
                         + f" | {_mean(passed):.2f} | {min(passed)} - {max(passed)} | {', '.join(f'`{u}`' for u in unstable) or 'không'} |")

    lines += ["", "| Điều kiện | Tổng check đạt mỗi lần lặp | Trung bình | Dao động | Kỹ thuật mỗi lần | Quy ước mỗi lần | Token trung bình mỗi lần chạy (từng lần lặp) |",
              "|---|---|---|---|---|---|---|"]
    for condition, tasks in data.items():
        totals, tech, rule, tokens = [], [], [], []
        for i in range(n):
            runs = [tasks[t][i] for t in tasks if tasks[t][i]]
            if not runs:
                continue
            parts = [_split(r) for r in runs]
            totals.append(sum(r["passed"] for r in runs))
            tech.append(f"{sum(p[0] for p in parts)}/{sum(p[1] for p in parts)}")
            rule.append(f"{sum(p[2] for p in parts)}/{sum(p[3] for p in parts)}")
            tokens.append(round(_mean([r["tokens"]["total"] for r in runs])))
        lines.append(f"| {condition} | {', '.join(map(str, totals))} | {_mean(totals):.2f} | {min(totals)} - {max(totals)} | "
                     f"{', '.join(tech)} | {', '.join(rule)} | {', '.join(f'{t:,}' for t in tokens)} |")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(render(sys.argv[1:] or ["results"]), end="")
