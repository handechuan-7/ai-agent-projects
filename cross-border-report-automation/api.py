from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app import build_report, find_anomalies, kpi_table, normalise_columns, sample_data
from platform_data import fitness_platform_data, platform_snapshot

app = FastAPI(title="Fitness E-commerce Report API", version="0.2.0")


class ReportRequest(BaseModel):
    period: Literal["日报", "周报"] = "日报"
    source: Literal["sample", "files", "platform"] = "platform"


@app.get("/health")
def health():
    return {"status": "ok", "service": "report-api", "domain": "fitness-equipment"}


@app.get("/platform/snapshot")
def get_platform_snapshot():
    return platform_snapshot()


@app.post("/generate-report")
def generate_report(request: ReportRequest):
    if request.source == "platform":
        sales, ads, inventory = fitness_platform_data()
    elif request.source == "sample":
        sales, ads, inventory = sample_data()
    else:
        data_dir = Path(os.getenv("REPORT_DATA_DIR", "/data"))
        paths = {key: data_dir / f"{key}.csv" for key in ("sales", "ads", "inventory")}
        missing = [str(path) for path in paths.values() if not path.exists()]
        if missing:
            raise HTTPException(status_code=400, detail=f"缺少数据文件: {', '.join(missing)}")
        sales, ads, inventory = [normalise_columns(pd.read_csv(paths[key])) for key in ("sales", "ads", "inventory")]

    kpi = kpi_table(sales, ads, inventory, request.period)
    anomalies = find_anomalies(sales, ads, inventory)
    return {
        "period": request.period,
        "data_date": str(kpi["date"].date()),
        "data_source": request.source,
        "kpi": {key: (float(value) if hasattr(value, "item") else value) for key, value in kpi.items() if key != "date"},
        "anomalies": anomalies,
        "report_markdown": build_report(sales, ads, inventory, request.period),
    }
