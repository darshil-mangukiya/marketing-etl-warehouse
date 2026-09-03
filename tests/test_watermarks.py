from pathlib import Path

import pandas as pd

from ingestion.watermarks import WatermarkStore


def test_watermark_filters_incremental_rows(tmp_path: Path) -> None:
    store = WatermarkStore(tmp_path / "watermarks.json", tmp_path / "processed.json")
    first = pd.DataFrame({"updated_at": ["2025-01-01T00:00:00", "2025-01-02T00:00:00"]})
    store.update_from_frame("crm_leads", first)

    second = pd.DataFrame(
        {
            "updated_at": [
                "2025-01-01T12:00:00",
                "2025-01-03T00:00:00",
            ],
            "lead_id": ["old", "new"],
        }
    )
    filtered, load_type = store.filter_incremental("crm_leads", second)

    assert load_type == "incremental"
    assert filtered["lead_id"].tolist() == ["new"]
