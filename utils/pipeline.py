from utils.snapshots import save_snapshot
from utils.events import detect_events
from utils.db import insert_event


def run_pipeline(df):

    # 1. detectar eventos ANTES de snapshot
    events = detect_events(df)

    # 2. guardar snapshot
    save_snapshot(df)

    # 3. guardar eventos
    for e in events:
        insert_event(e)

    return events