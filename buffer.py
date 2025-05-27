import json
from pathlib import Path
from datetime import datetime

BUFFER_PATH = Path("triplet_buffer.jsonl")

def save_to_buffer(triplet, buffer_path=BUFFER_PATH):
    triplet_with_date = triplet.copy()
    triplet_with_date["date_added"] = datetime.utcnow().isoformat()
    
    with open(buffer_path, "a", encoding="utf-8") as f:
        json.dump(triplet_with_date, f, ensure_ascii=False)
        f.write("\n")

def load_buffered_triplets(buffer_path=BUFFER_PATH):
    if not buffer_path.exists():
        return []

    triplets = []
    with open(buffer_path, encoding="utf-8") as f:
        for line in f:
            try:
                triplet = json.loads(line)
                triplets.append(triplet)
            except json.JSONDecodeError:
                continue
    return triplets

def clear_buffer(buffer_path=BUFFER_PATH):
    buffer_path.unlink(missing_ok=True)
    buffer_path.touch()
