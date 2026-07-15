"""
PHASE 1 — DATA INGESTION

Real job: receive real-time telemetry (device metrics, traffic, logs) and
tag each record with which device/session it belongs to.

This module's job in the skeleton: read NSL-KDD records (real file if present,
otherwise a synthetic fallback with the same schema) and yield them in small
batches, the way a real streaming source would. Everything downstream only
ever sees "a batch of records" — it never needs to know whether they came
from a file, MQTT, or Kafka. That's the point of keeping this phase isolated:
you can swap the source later without touching Phases 2-9.

STATUS: functional (reads real data or synthesizes it). Nothing to fill in
to get a first pipeline run — but see the TODOs for the real upgrade path.
"""

import numpy as np
import pandas as pd

from config import RAW_DATA_PATH, KDD_COLUMNS, CATEGORICAL_COLUMNS, SYNTHETIC_ROWS, STREAM_BATCH_SIZE


def _generate_synthetic_dataset(n_rows: int = SYNTHETIC_ROWS) -> pd.DataFrame:
    """Fallback data generator, same 41-column NSL-KDD schema as the real file.
    Lets you run the whole pipeline today even before you've downloaded the
    real dataset. Swap in the real file at data/raw/KDDTrain+.txt any time —
    nothing else in the pipeline changes.
    """
    rng = np.random.default_rng(seed=42)
    n_normal = int(n_rows * 0.9)
    n_anomaly = n_rows - n_normal

    def rows(count, scale, label):
        return pd.DataFrame({
            "duration": rng.exponential(scale, count),
            "protocol_type": rng.choice(["tcp", "udp", "icmp"], count),
            "service": rng.choice(["http", "ftp", "smtp", "private"], count),
            "flag": rng.choice(["SF", "S0", "REJ"], count),
            "src_bytes": rng.exponential(scale * 200, count),
            "dst_bytes": rng.exponential(scale * 200, count),
            "land": 0, "wrong_fragment": 0, "urgent": 0,
            "hot": rng.integers(0, 2, count),
            "num_failed_logins": 0, "logged_in": 1,
            "num_compromised": 0, "root_shell": 0, "su_attempted": 0, "num_root": 0,
            "num_file_creations": 0, "num_shells": 0, "num_access_files": 0,
            "num_outbound_cmds": 0, "is_host_login": 0, "is_guest_login": 0,
            "count": rng.integers(1, scale * 10, count),
            "srv_count": rng.integers(1, scale * 10, count),
            "serror_rate": rng.uniform(0, 0.1 * scale, count).clip(0, 1),
            "srv_serror_rate": rng.uniform(0, 0.1 * scale, count).clip(0, 1),
            "rerror_rate": 0.0, "srv_rerror_rate": 0.0,
            "same_srv_rate": rng.uniform(0.7, 1.0, count),
            "diff_srv_rate": rng.uniform(0, 0.1, count),
            "srv_diff_host_rate": rng.uniform(0, 0.1, count),
            "dst_host_count": rng.integers(1, 255, count),
            "dst_host_srv_count": rng.integers(1, 255, count),
            "dst_host_same_srv_rate": rng.uniform(0.7, 1.0, count),
            "dst_host_diff_srv_rate": rng.uniform(0, 0.1, count),
            "dst_host_same_src_port_rate": rng.uniform(0, 1, count),
            "dst_host_srv_diff_host_rate": rng.uniform(0, 0.1, count),
            "dst_host_serror_rate": rng.uniform(0, 0.1 * scale, count).clip(0, 1),
            "dst_host_srv_serror_rate": rng.uniform(0, 0.1 * scale, count).clip(0, 1),
            "dst_host_rerror_rate": 0.0, "dst_host_srv_rerror_rate": 0.0,
            "label": label, "difficulty": rng.integers(1, 21, count),
        })

    normal = rows(n_normal, 1.0, "normal")
    anomaly = rows(n_anomaly, 8.0, "attack")  # bigger/spikier values = anomaly-like
    df = pd.concat([normal, anomaly], ignore_index=True)
    return df.sample(frac=1, random_state=42).reset_index(drop=True)  # shuffle


def load_dataset() -> pd.DataFrame:
    """Load the real NSL-KDD file if present, else generate the synthetic fallback."""
    if RAW_DATA_PATH.exists():
        df = pd.read_csv(RAW_DATA_PATH, names=KDD_COLUMNS)
        print(f"[ingestion] loaded real dataset: {len(df)} rows from {RAW_DATA_PATH}")
    else:
        df = _generate_synthetic_dataset()
        print(f"[ingestion] {RAW_DATA_PATH} not found — generated {len(df)} synthetic rows instead")
    return df


def stream_batches(df: pd.DataFrame, batch_size: int = STREAM_BATCH_SIZE):
    """Yield the dataset in batches, simulating a real-time stream.

    TODO (real upgrade path, later): replace this generator with a Mosquitto
    MQTT subscriber or a Kafka consumer. Every function downstream already
    just takes 'a batch of records' as a DataFrame, so nothing else changes.
    """
    for start in range(0, len(df), batch_size):
        batch = df.iloc[start:start + batch_size].copy()
        batch["_record_id"] = range(start, start + len(batch))  # simple session/device tag
        yield batch


if __name__ == "__main__":
    data = load_dataset()
    for i, batch in enumerate(stream_batches(data)):
        print(f"batch {i}: {len(batch)} records")
        if i == 2:
            break
