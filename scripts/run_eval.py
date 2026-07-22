"""Eval CLI for the triage pipeline.

Examples:
  python scripts/run_eval.py --n 40                 # classification eval, 40 tickets
  python scripts/run_eval.py --n 40 --judge 8       # + LLM-judge 8 draft responses
  python scripts/run_eval.py --adversarial          # only the edge-case suite
  python scripts/run_eval.py --n 40 --refresh       # ignore prediction cache

Predictions and the JSON report are written to eval_output/ (git-ignored).
Classification uses a cache, so re-runs are cheap; --judge and --adversarial
make fresh LLM calls each run.
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import config  # noqa: E402
from src.eval import adversarial, harness, judge  # noqa: E402


def _bar(x: float, width: int = 24) -> str:
    filled = int(round(x * width))
    return "#" * filled + "." * (width - filled)


def print_report(report: dict) -> None:
    print("=" * 76)
    print(f"CLASSIFICATION EVAL  |  model={report['model']}  "
          f"prompt={report['prompt_version']}  n={report['n_scored']}")
    print("=" * 76)
    cat, urg, prod = report["category"], report["urgency"], report["product"]
    print(f"Category  accuracy : {cat['accuracy']:.3f}  [{_bar(cat['accuracy'])}]  "
          f"macro-F1 {cat['macro_f1']:.3f}")
    print(f"Urgency   accuracy : {urg['accuracy']:.3f}  [{_bar(urg['accuracy'])}]  "
          f"within-1 {urg['within_1']:.3f}")
    print(f"Product   accuracy : {prod['accuracy']:.3f}  [{_bar(prod['accuracy'])}]")

    print("\nPer-category (precision / recall / f1 / support):")
    for label, m in cat["per_class"].items():
        if m["support"] == 0:
            continue
        print(f"  {label:<16} P {m['precision']:.2f}  R {m['recall']:.2f}  "
              f"F1 {m['f1']:.2f}  (n={m['support']})")

    print("\nUrgency confusion (rows=gold, cols=pred):")
    labels = list(urg["confusion"].keys())
    print("        " + "  ".join(f"{c:>4}" for c in labels))
    for g in labels:
        row = urg["confusion"][g]
        print(f"  {g:<5} " + "  ".join(f"{row[c]:>4}" for c in labels))

    dis = report["category_disagreements"]
    print(f"\nCategory disagreements vs ground truth: {len(dis)} "
          f"(many are known-ambiguous labels)")
    for d in dis[:8]:
        print(f"  {d['ticket_id']}  gold={d['gold']:<22} pred={d['pred']:<22} "
              f"| {d['subject']}")


def print_adversarial(results: list[dict]) -> None:
    passed = sum(r["passed"] for r in results)
    print("=" * 76)
    print(f"ADVERSARIAL SUITE  |  {passed}/{len(results)} passed")
    print("=" * 76)
    for r in results:
        mark = "PASS" if r["passed"] else "FAIL"
        print(f"  [{mark}] {r['name']:<26} -> {r['category']}/{r['urgency']}")
        for f in r["failures"]:
            print(f"           - {f}")


def print_judge(agg: dict, samples: list[dict]) -> None:
    print("=" * 76)
    print(f"LLM-JUDGE (draft response quality)  |  n={agg.get('n', 0)}")
    print("=" * 76)
    for dim in ["groundedness", "relevance", "actionability", "tone"]:
        print(f"  {dim:<14}: {agg.get(dim, 0):.2f} / 5")
    print(f"  hallucination_rate: {agg.get('hallucination_rate', 0):.1%}")
    for s in samples[:5]:
        flag = " HALLUCINATED" if s["hallucinated"] else ""
        print(f"    {s['ticket_id']}: grounded {s['groundedness']}/5{flag} — {s['rationale'][:80]}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=30, help="tickets to score (classification)")
    ap.add_argument("--judge", type=int, default=0, help="also LLM-judge this many drafts")
    ap.add_argument("--adversarial", action="store_true", help="run edge-case suite")
    ap.add_argument("--refresh", action="store_true", help="ignore prediction cache")
    args = ap.parse_args()

    output: dict = {"generated_at": datetime.now().isoformat()}

    if args.adversarial:
        from src.triage.pipeline import triage_ticket
        results = [adversarial.run_case(c, triage_ticket) for c in adversarial.CASES]
        print_adversarial(results)
        output["adversarial"] = results

    if not args.adversarial or args.n:
        print(f"Scoring {args.n} tickets (cached predictions reused)...")
        report = harness.run(args.n, refresh=args.refresh)
        print_report(report)
        output["classification"] = report

    if args.judge:
        from src.schemas import TicketInput
        from src.triage.pipeline import triage_ticket
        print(f"\nJudging {args.judge} draft responses...")
        tickets = harness.sample_tickets(args.judge)
        scores = []
        for t in tickets:
            res = triage_ticket(TicketInput(subject=t["subject"], body=t["body"]))
            s = judge.judge_response(t["subject"], t["body"], res)
            s["ticket_id"] = t["ticket_id"]
            scores.append(s)
            time.sleep(1.2)
        agg = judge.aggregate(scores)
        print_judge(agg, scores)
        output["judge"] = {"aggregate": agg, "samples": scores}

    out_dir = config.ROOT_DIR / "eval_output"
    out_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = out_dir / f"report_{stamp}.json"
    report_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nFull report written to {report_path.relative_to(config.ROOT_DIR)}")


if __name__ == "__main__":
    main()
