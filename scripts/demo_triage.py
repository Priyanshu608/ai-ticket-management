"""Demo: triage N real tickets from the dataset and compare against
ground-truth labels (labels are stripped before the model sees anything).
"""

import sys
import time
from pathlib import Path

# KB docs and LLM output contain Unicode (em-dash, non-breaking hyphen) that the
# default Windows console (cp1252) can't encode. Force UTF-8 so printing works.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data_loader import load_tickets  # noqa: E402
from src.schemas import TicketInput  # noqa: E402
from src.triage.pipeline import triage_ticket  # noqa: E402

N = int(sys.argv[1]) if len(sys.argv) > 1 else 3

for t in load_tickets()[:N]:
    ticket = TicketInput(subject=t["subject"], body=t["body"])  # labels stripped
    res = triage_ticket(ticket)
    c = res.classification
    print("=" * 72)
    print(f"{t['ticket_id']} | {t['subject'][:60]}")
    print(f"  predicted : {c.product} / {c.product_area} / {c.category} / {c.urgency}")
    print(
        f"  actual    : {t['product']} / {t['product_area']} / "
        f"{t['category']} / {t['urgency']}"
    )
    print(f"  reasoning : {c.reasoning}")
    print(f"  kb match  : {res.kb_match.is_known_issue} -> {res.kb_match.doc_path}")
    print(f"  team      : {res.recommended_team}")
    print(f"  draft     : {res.draft_response[:200]}...")
    time.sleep(2)  # free tier: 30 RPM, 2 LLM calls per ticket
