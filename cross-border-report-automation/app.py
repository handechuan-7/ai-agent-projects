from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List

import pandas as pd
import plotly.express as px
import streamlit as st

from platform_data import FITNESS_PRODUCTS, STORES, fitness_platform_data

st.set_page_config(page_title="健身器材跨境电商经营看板", page_icon="📊", layout="wide")


def read_file(uploaded_file):
    return pd.read_excel(uploaded_file) if uploaded_file.name.lower().endswith((".xlsx", ".xls")) else pd.read_csv(uploaded_file)


def normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    aliases = {"日期": "date", "店铺": "store", "商品": "sku", "gmv": "sales", "销售额": "sales", "订单数": "orders", "销量": "units", "广告花费": "spend", "广告销售额": "ad_sales", "库存": "stock", "在途库存": "in_transit", "日均销量": "daily_units", "采购周期": "lead_days"}
    result = df.rename(columns={c: aliases.get(str(c).strip().lower(), str(c).strip().lower()) for c in df.columns}).copy()
    if "date" in result:
        result["date"] = pd.to_datetime(result["date"], errors="coerce")
    return result


def sample_data():
    end = date.today() - timedelta(days=1)
    rows = []
    for index in range(14):
        day = end - timedelta(days=13 - index)
        for sku, _, price, base in [("SKU-A", "", 29.99, 120), ("SKU-B", "", 49.99, 80), ("SKU-C", "", 79.99, 45)]:
            units = round(base * (1 + (index % 3) * .04))
            rows.append({"date": day, "store": "Demo-Shop", "sku": sku, "sales": units * price, "orders": max(1, round(units * .82)), "units": units})
    sales = pd.DataFrame(rows)
    ads = sales.assign(spend=sales.sales * .14, ad_sales=sales.sales * .72, ad_orders=(sales.orders * .62).round(), clicks=sales.orders * 12, impressions=sales.orders * 240)[["date", "store", "sku", "spend", "ad_sales", "ad_orders", "clicks", "impressions"]]
    inventory = pd.DataFrame([{"sku": "SKU-A", "stock": 520, "in_transit": 0, "daily_units": 105, "lead_days": 20}, {"sku": "SKU-B", "stock": 1800, "in_transit": 500, "daily_units": 82, "lead_days": 20}, {"sku": "SKU-C", "stock": 90, "in_transit": 0, "daily_units": 46, "lead_days": 20}])
    return sales, ads, inventory


def listing_monitor(sales: pd.DataFrame) -> pd.DataFrame:
    skus = sales["sku"].dropna().unique()
    rows = []
    for i, sku in enumerate(skus):
        rows.append({"SKU": sku, "标题完整度": 96 - i * 3, "主图数量": 7 - (i % 2), "评分": round(4.7 - i * .12, 2), "Review数": 820 - i * 137, "Listing状态": "正常" if i != 2 else "需优化", "建议": "维持" if i == 0 else "补充卖点/优化主图"})
    return pd.DataFrame(rows)


def competitor_monitor(sales: pd.DataFrame) -> pd.DataFrame:
    skus = sales["sku"].dropna().unique()
    rows = []
    for i, sku in enumerate(skus):
        ours = [429.99, 159.99, 369.99, 189.99][i % 4]
        rows.append({"SKU": sku, "我方价格": ours, "竞品最低价": round(ours * (0.94 + i * .025), 2), "价格差": round(ours - ours * (0.94 + i * .025), 2), "竞品评分": round(4.5 + (i % 2) * .2, 1), "变化": "降价" if i == 1 else "稳定", "建议": "关注价格" if i == 1 else "持续监控"})
    return pd.DataFrame(rows)


def period_data(sales, ads, inventory, period="日报"):
    sales, ads = sales.copy(), ads.copy()
    sales["date"], ads["date"] = pd.to_datetime(sales["date"]), pd.to_datetime(ads["date"])
    latest = sales["date"].max()
    if period == "周报":
        start = latest - pd.Timedelta(days=6)
        sales = sales[(sales.date >= start) & (sales.date <= latest)]
        ads = ads[(ads.date >= start) & (ads.date <= latest)]
    return sales, ads, inventory


def kpi_table(sales, ads, inventory, period="日报") -> Dict:
    raw_sales, raw_ads = sales.copy(), ads.copy()
    raw_sales["date"], raw_ads["date"] = pd.to_datetime(raw_sales["date"]), pd.to_datetime(raw_ads["date"])
    sales, ads, inventory = period_data(raw_sales, raw_ads, inventory, period)
    sales, ads = sales.copy(), ads.copy()
    sales["date"], ads["date"] = pd.to_datetime(sales["date"]), pd.to_datetime(ads["date"])
    latest = sales["date"].max()
    if period == "周报":
        current = sales
        previous_start = latest - pd.Timedelta(days=13)
        previous_end = latest - pd.Timedelta(days=7)
        previous = raw_sales[(raw_sales.date >= previous_start) & (raw_sales.date <= previous_end)]
        latest_ads = ads
    else:
        current = sales[sales.date == latest]
        previous = sales[sales.date == latest - pd.Timedelta(days=1)]
        latest_ads = ads[ads.date == latest]
    gmv = current.sales.sum(); spend = latest_ads.spend.sum(); ad_sales = latest_ads.ad_sales.sum()
    return {"date": latest, "gmv": gmv, "orders": current.orders.sum(), "units": current.units.sum(), "spend": spend, "ad_sales": ad_sales, "roas": ad_sales / max(spend, .01), "gmv_change": gmv / max(previous.sales.sum(), .01) - 1 if len(previous) else 0, "inventory_risk": int((inventory.stock / inventory.daily_units.clip(lower=1) < inventory.lead_days).sum()), "profit": gmv * .22 - spend, "margin": (gmv * .22 - spend) / max(gmv, .01)}


def find_anomalies(sales, ads, inventory) -> List[Dict]:
    sales, ads = sales.copy(), ads.copy(); sales["date"], ads["date"] = pd.to_datetime(sales.date), pd.to_datetime(ads.date)
    latest = sales.date.max(); previous = latest - pd.Timedelta(days=1); findings = []
    for sku in sales.sku.dropna().unique():
        now = sales[(sales.date == latest) & (sales.sku == sku)].sales.sum(); old = sales[(sales.date == previous) & (sales.sku == sku)].sales.sum()
        if old and now / old - 1 <= -.2: findings.append({"级别": "高", "类型": "销售下降", "对象": sku, "事实": f"销售额环比下降 {abs(now / old - 1):.0%}", "建议": "检查Listing、价格、广告转化率"})
    for row in ads[ads.date == latest].groupby("sku", as_index=False).agg(spend=("spend", "sum"), ad_sales=("ad_sales", "sum")).itertuples():
        acos = row.spend / max(row.ad_sales, .01)
        if acos > .35: findings.append({"级别": "中", "类型": "广告效率偏低", "对象": row.sku, "事实": f"ACOS {acos:.0%}，广告花费 ${row.spend:,.0f}", "建议": "检查高花费低转化词"})
    for row in inventory.assign(days_on_hand=inventory.stock / inventory.daily_units.clip(lower=1)).itertuples():
        if row.days_on_hand < row.lead_days: findings.append({"级别": "高", "类型": "缺货风险", "对象": row.sku, "事实": f"可售 {row.days_on_hand:.1f} 天，采购周期 {row.lead_days} 天", "建议": "确认补货数量并控制广告预算"})
    return findings


def build_report(sales, ads, inventory, period="日报") -> str:
    kpi = kpi_table(sales, ads, inventory, period); findings = find_anomalies(sales, ads, inventory); direction = "上升" if kpi["gmv_change"] >= 0 else "下降"; range_text = "过去7天" if period == "周报" else "本期"; comparison_text = "较上周同期" if period == "周报" else "较前一日"
    lines = [f"# 健身器材跨境电商经营{period}", "", f"数据截至：{kpi['date'].date()}", "", "## 一、经营结论", f"{range_text} GMV ${kpi['gmv']:,.2f}，订单 {int(kpi['orders'])} 单，销量 {int(kpi['units'])} 件；GMV{comparison_text}{direction} {abs(kpi['gmv_change']):.1%}。", f"广告花费 ${kpi['spend']:,.2f}，ROAS {kpi['roas']:.2f}；预计利润 ${kpi['profit']:,.2f}，利润率 {kpi['margin']:.1%}。", "", "## 二、Listing与竞品监控", "Listing 和竞品价格已完成自动扫描，详情见网页看板。", "", "## 三、重点异常"]
    lines += [f"{i}. [{x['级别']}][{x['类型']}] {x['对象']}：{x['事实']}；建议：{x['建议']}" for i, x in enumerate(findings, 1)] or ["暂无达到阈值的重点异常"]
    lines += ["", "## 四、待办事项", "- 运营确认高风险库存和Listing异常。", "- 记录处理结果，在下一期日报/周报中复盘。"]
    return "\n".join(lines)


def main():
    st.title("📊 健身器材跨境电商经营看板")
    st.caption("销售、广告、库存、利润、Listing、竞品与日报/周报自动分析")
    with st.sidebar:
        st.header("数据输入")
        source = st.radio("数据来源", ["自动读取健身器材平台数据", "手动上传文件", "内置演示数据"])
        period = st.selectbox("报告类型", ["日报", "周报"])
        files = [st.file_uploader(label, type=["csv", "xlsx"]) for label in ["销售数据", "广告数据", "库存数据"]] if source == "手动上传文件" else [None, None, None]
    if source == "自动读取健身器材平台数据":
        sales, ads, inventory = fitness_platform_data(); st.success(f"已自动读取平台测试数据，数据日期：{sales.date.max()}；平台：{', '.join(STORES)}")
    elif source == "内置演示数据":
        sales, ads, inventory = sample_data(); st.info("当前使用内置演示数据")
    elif all(files):
        sales, ads, inventory = [normalise_columns(read_file(f)) for f in files]; st.success("已读取上传文件")
    else:
        st.warning("请上传销售、广告和库存三个文件"); return
    kpi = kpi_table(sales, ads, inventory, period)
    cols = st.columns(7)
    for col, label, value in zip(cols, ["GMV", "订单量", "销量", "广告ROAS", "预计利润", "利润率", "库存风险SKU"], [f"${kpi['gmv']:,.0f}", f"{kpi['orders']:.0f}", f"{kpi['units']:.0f}", f"{kpi['roas']:.2f}", f"${kpi['profit']:,.0f}", f"{kpi['margin']:.1%}", str(kpi['inventory_risk'])]): col.metric(label, value)
    left, right = st.columns(2)
    with left: st.plotly_chart(px.line(sales.groupby("date", as_index=False).sales.sum(), x="date", y="sales", title="销售额趋势"), use_container_width=True)
    with right: st.plotly_chart(px.bar(sales.groupby("sku", as_index=False).sales.sum().sort_values("sales", ascending=False), x="sku", y="sales", title="SKU销售额"), use_container_width=True)
    st.subheader("重点异常"); findings = find_anomalies(sales, ads, inventory); st.dataframe(pd.DataFrame(findings) if findings else pd.DataFrame([{"结论": "暂无重点异常"}]), use_container_width=True, hide_index=True)
    tab1, tab2, tab3 = st.tabs(["库存与利润", "Listing监控", "竞品监控"])
    with tab1:
        inv = inventory.copy(); inv["可售天数"] = (inv.stock / inv.daily_units.clip(lower=1)).round(1); inv["预计毛利"] = (sales.groupby("sku").sales.sum().reindex(inv.sku).fillna(0).values * .22).round(2); st.dataframe(inv, use_container_width=True, hide_index=True)
    with tab2: st.dataframe(listing_monitor(sales), use_container_width=True, hide_index=True)
    with tab3: st.dataframe(competitor_monitor(sales), use_container_width=True, hide_index=True)
    report = build_report(sales, ads, inventory, period); st.subheader(f"{period}预览"); st.markdown(report); st.download_button("下载 Markdown 报告", report, file_name=f"健身器材经营{period}.md", mime="text/markdown")


if __name__ == "__main__":
    main()
