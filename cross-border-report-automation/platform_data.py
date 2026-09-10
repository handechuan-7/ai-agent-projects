from __future__ import annotations

from datetime import date, timedelta
import hashlib

import pandas as pd


FITNESS_PRODUCTS = [
    ("TREADMILL-X1", "电动跑步机 X1", 429.99, 28),
    ("DUMBBELL-ADJ", "可调节哑铃套装", 159.99, 42),
    ("ROWER-R2", "家用划船机 R2", 369.99, 18),
    ("BENCH-F7", "多功能力量训练椅", 189.99, 24),
]
STORES = ["Amazon-US", "TikTok-US", "Walmart-US"]


def _factor(day: date, sku: str) -> float:
    value = int(hashlib.sha256(f"{day.isoformat()}:{sku}".encode()).hexdigest()[:8], 16)
    return 0.84 + (value % 34) / 100


def fitness_platform_data(as_of: date | None = None):
    """模拟健身器材多平台/ERP接口返回的数据。

    真实接入时只需要替换本函数，日报分析和 n8n 流程无需重做。
    """
    end = as_of or (date.today() - timedelta(days=1))
    sales_rows, ads_rows = [], []
    for offset in range(14):
        day = end - timedelta(days=13 - offset)
        for store_index, store in enumerate(STORES):
            for sku_index, (sku, _name, price, base_units) in enumerate(FITNESS_PRODUCTS):
                units = max(1, round(base_units * _factor(day, sku) * (1 - store_index * 0.08)))
                sales = round(units * price, 2)
                orders = max(1, round(units * 0.78))
                spend = round(sales * (0.11 + store_index * 0.025), 2)
                sales_rows.append({"date": day, "store": store, "sku": sku, "sales": sales, "orders": orders, "units": units})
                ads_rows.append({"date": day, "store": store, "sku": sku, "spend": spend,
                                 "ad_sales": round(sales * (0.68 + (sku_index % 2) * 0.08), 2),
                                 "ad_orders": max(1, round(orders * 0.58)), "clicks": orders * 13,
                                 "impressions": orders * 260})
    inventory = pd.DataFrame([
        {"sku": "TREADMILL-X1", "stock": 86, "in_transit": 120, "daily_units": 26, "lead_days": 18},
        {"sku": "DUMBBELL-ADJ", "stock": 680, "in_transit": 300, "daily_units": 39, "lead_days": 14},
        {"sku": "ROWER-R2", "stock": 74, "in_transit": 0, "daily_units": 17, "lead_days": 21},
        {"sku": "BENCH-F7", "stock": 410, "in_transit": 180, "daily_units": 23, "lead_days": 16},
    ])
    return pd.DataFrame(sales_rows), pd.DataFrame(ads_rows), inventory


def platform_snapshot(as_of: date | None = None) -> dict:
    sales, ads, inventory = fitness_platform_data(as_of)
    return {"source": "mock_fitness_platform_erp", "data_date": str(sales["date"].max()),
            "stores": STORES, "sales_rows": len(sales), "ads_rows": len(ads),
            "inventory_rows": len(inventory)}
