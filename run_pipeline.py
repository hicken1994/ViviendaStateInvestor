from utils.fetch import fetch_data
from utils.pipeline import run_pipeline

if __name__ == "__main__":
    df = fetch_data()
    events = run_pipeline(df)

    print(f"{len(events)} eventos generados")