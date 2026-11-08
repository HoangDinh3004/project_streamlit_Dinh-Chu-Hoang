from pathlib import Path
import argparse
import shutil
import pandas as pd

FILES_REQUIRED = [
    "order_level_labeled.csv",
    "model_cohort.csv",
    "data_coverage_by_status.csv",
    "model_validation_comparison.csv",
    "model_test_metrics.csv",
    "model_feature_importance.csv",
    "split_period_summary.csv",
]

def require_columns(df, columns, filename):
    missing = [col for col in columns if col not in df.columns]
    if missing:
        raise ValueError(f"{filename} thiếu cột bắt buộc: {missing}")

def main():
    parser = argparse.ArgumentParser(
        description="Tạo các tệp CSV tổng hợp an toàn hơn để đưa lên dashboard công khai."
    )
    parser.add_argument(
        "source_output",
        help="Đường dẫn thư mục output được xuất từ notebook đã chạy."
    )
    args = parser.parse_args()

    source = Path(args.source_output).expanduser().resolve()
    target = Path(__file__).resolve().parent / "output"
    target.mkdir(parents=True, exist_ok=True)

    missing = [name for name in FILES_REQUIRED if not (source / name).exists()]
    if missing:
        raise FileNotFoundError(
            f"Thiếu các tệp trong {source}: {missing}\n"
            "Hãy trỏ đến đúng thư mục output của notebook."
        )

    orders = pd.read_csv(source / "order_level_labeled.csv", low_memory=False)
    cohort = pd.read_csv(source / "model_cohort.csv", low_memory=False)

    require_columns(orders, ["order_id", "order_status", "Order_Risk", "order_purchase_timestamp"], "order_level_labeled.csv")
    require_columns(cohort, [
        "order_id", "Order_Risk", "main_category", "total_price",
        "total_freight", "total_weight_g", "Estimated_Delivery_Days",
        "Purchase_Hour", "Purchase_Weekday", "Is_Weekend"
    ], "model_cohort.csv")

    # 1. Trạng thái đơn ở mức tổng hợp, không chứa mã đơn.
    status = (
        orders.groupby("order_status")
        .agg(orders=("order_id", "nunique"))
        .reset_index()
    )
    status["share_pct"] = status["orders"] / status["orders"].sum() * 100
    status.to_csv(target / "status_counts.csv", index=False)

    # 2. Xu hướng tháng: luôn kèm số đơn và số đơn không hoàn tất.
    orders["order_purchase_timestamp"] = pd.to_datetime(
        orders["order_purchase_timestamp"], errors="coerce"
    )
    monthly = (
        orders.dropna(subset=["order_purchase_timestamp"])
        .set_index("order_purchase_timestamp")
        .resample("MS")
        .agg(
            order_count=("Order_Risk", "size"),
            risk_count=("Order_Risk", "sum"),
            risk_rate=("Order_Risk", "mean"),
        )
        .reset_index()
    )
    monthly["month"] = monthly["order_purchase_timestamp"].dt.strftime("%Y-%m")
    monthly["risk_rate_pct"] = monthly["risk_rate"] * 100
    monthly[["month", "order_count", "risk_count", "risk_rate_pct"]].to_csv(
        target / "monthly_summary.csv", index=False
    )

    # 3. Ngành hàng, chỉ giữ nhóm có ít nhất 100 đơn.
    category = (
        cohort.assign(main_category=cohort["main_category"].fillna("unknown").astype(str))
        .groupby("main_category")
        .agg(
            order_count=("order_id", "nunique"),
            risk_count=("Order_Risk", "sum"),
            risk_rate=("Order_Risk", "mean"),
        )
        .reset_index()
    )
    category = category[category["order_count"] >= 100].copy()
    category["risk_rate_pct"] = category["risk_rate"] * 100
    category.sort_values("risk_rate_pct", ascending=False).to_csv(
        target / "category_summary.csv", index=False
    )

    # 4. Phương thức thanh toán ở mức tổng hợp.
    if "payment_method_group" in orders.columns:
        payment = (
            orders.groupby("payment_method_group")
            .agg(
                order_count=("order_id", "nunique"),
                risk_count=("Order_Risk", "sum"),
                risk_rate=("Order_Risk", "mean"),
            )
            .reset_index()
        )
        payment["risk_rate_pct"] = payment["risk_rate"] * 100
        payment.sort_values("order_count", ascending=False).to_csv(
            target / "payment_summary.csv", index=False
        )
    else:
        pd.DataFrame(columns=["payment_method_group", "order_count", "risk_count", "risk_rate_pct"]).to_csv(
            target / "payment_summary.csv", index=False
        )

    # 5. Hồ sơ trung vị theo nhãn.
    profile_rows = []
    for label, group in cohort.groupby("Order_Risk"):
        profile_rows.append({
            "Order_Risk": int(label),
            "label": "Đã giao (0)" if int(label) == 0 else "Không hoàn tất (1)",
            "order_count": int(group["order_id"].nunique()),
            "median_total_price": group["total_price"].median(),
            "median_total_freight": group["total_freight"].median(),
            "median_total_weight_g": group["total_weight_g"].median(),
            "median_estimated_delivery_days": group["Estimated_Delivery_Days"].median(),
        })
    pd.DataFrame(profile_rows).to_csv(target / "risk_profile.csv", index=False)

    # 6. Tỷ lệ theo giờ.
    hourly = (
        cohort.groupby("Purchase_Hour")
        .agg(
            order_count=("order_id", "nunique"),
            risk_count=("Order_Risk", "sum"),
            risk_rate=("Order_Risk", "mean"),
        )
        .reindex(range(24))
        .rename_axis("Purchase_Hour")
        .reset_index()
    )
    hourly["risk_rate_pct"] = hourly["risk_rate"] * 100
    hourly.to_csv(target / "hourly_summary.csv", index=False)

    # 7. Tỷ lệ theo thứ trong tuần.
    weekday = (
        cohort.groupby("Purchase_Weekday")
        .agg(
            order_count=("order_id", "nunique"),
            risk_count=("Order_Risk", "sum"),
            risk_rate=("Order_Risk", "mean"),
        )
        .reindex(range(7))
        .rename_axis("Purchase_Weekday")
        .reset_index()
    )
    weekday["risk_rate_pct"] = weekday["risk_rate"] * 100
    weekday.to_csv(target / "weekday_summary.csv", index=False)

    # 8. So sánh ngày thường/cuối tuần.
    weekend = (
        cohort.groupby("Is_Weekend")
        .agg(
            order_count=("order_id", "nunique"),
            risk_count=("Order_Risk", "sum"),
            risk_rate=("Order_Risk", "mean"),
        )
        .reset_index()
    )
    weekend["day_type"] = weekend["Is_Weekend"].map({0: "Ngày thường", 1: "Cuối tuần"})
    weekend["risk_rate_pct"] = weekend["risk_rate"] * 100
    weekend.to_csv(target / "weekend_summary.csv", index=False)

    # 9. Chỉ sao chép các tệp thống kê đã tổng hợp, không copy tệp chứa bản ghi đơn hàng.
    copy_map = {
        "data_coverage_by_status.csv": "coverage.csv",
        "model_validation_comparison.csv": "validation_comparison.csv",
        "model_test_metrics.csv": "test_metrics.csv",
        "model_feature_importance.csv": "feature_importance.csv",
        "split_period_summary.csv": "split_period_summary.csv",
    }
    for src_name, dest_name in copy_map.items():
        shutil.copy2(source / src_name, target / dest_name)

    print(f"Đã tạo {len(list(target.glob('*.csv')))} tệp CSV tổng hợp tại: {target}")
    print("Đây là các bảng tổng hợp, không bao gồm order_id/customer_id hay các bản ghi giao dịch.")
    print("Các tệp không được đưa lên GitHub công khai: order_level_labeled.csv, model_cohort.csv, test_order_risk_predictions.csv và các dữ liệu thô.")

if __name__ == "__main__":
    main()
