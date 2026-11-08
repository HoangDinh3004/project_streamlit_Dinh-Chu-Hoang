from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "output"

st.set_page_config(
    page_title="Dashboard quản trị đơn hàng",
    page_icon="📦",
    layout="wide",
)

st.title("📦 Dashboard phân tích đơn hàng thương mại điện tử")
st.caption("Phân tích đơn hàng không hoàn tất • Đánh giá mô hình học máy • Định hướng quản trị logistics ngược")

st.info(
    "Ứng dụng trình bày dữ liệu tổng hợp và kết quả đánh giá mô hình. "
    "Nhãn được phân tích là đơn hàng không hoàn tất (canceled/unavailable), "
    "không đồng nghĩa với sản phẩm đã được khách hàng trả lại. "
    "Không sử dụng dashboard này để tự động ra quyết định vận hành."
)

FILES = {
    "status": "status_counts.csv",
    "monthly": "monthly_summary.csv",
    "category": "category_summary.csv",
    "payment": "payment_summary.csv",
    "profile": "risk_profile.csv",
    "hourly": "hourly_summary.csv",
    "weekday": "weekday_summary.csv",
    "weekend": "weekend_summary.csv",
    "coverage": "coverage.csv",
    "validation": "validation_comparison.csv",
    "test": "test_metrics.csv",
    "importance": "feature_importance.csv",
    "split": "split_period_summary.csv",
}

@st.cache_data(show_spinner=False)
def read_csv(filename):
    path = DATA_DIR / filename
    if not path.exists():
        return None
    return pd.read_csv(path)

data = {key: read_csv(filename) for key, filename in FILES.items()}

missing = [filename for key, filename in FILES.items()
           if data.get(key) is None and key not in {"weekday", "weekend", "split"}]

if missing:
    st.warning(
        "Chưa tìm thấy một số tệp tổng hợp trong thư mục output. "
        "Hãy chạy prepare_public_data.py theo hướng dẫn README rồi tải các CSV đã tổng hợp lên GitHub."
    )
    st.code("\n".join(missing))
    st.stop()

status = data["status"]
monthly = data["monthly"]
test = data["test"]
validation = data["validation"]
importance = data["importance"]

def first_row(df):
    return df.iloc[0] if df is not None and not df.empty else pd.Series(dtype=object)

def num(row, key, default=0.0):
    try:
        val = float(row.get(key, default))
        return val if pd.notna(val) else default
    except (TypeError, ValueError):
        return default

status_row = status.set_index("order_status")["orders"].to_dict() if {"order_status", "orders"}.issubset(status.columns) else {}
total_orders = int(status["orders"].sum()) if "orders" in status.columns else 0
delivered = int(status_row.get("delivered", 0))
canceled = int(status_row.get("canceled", 0))
unavailable = int(status_row.get("unavailable", 0))
non_completed = canceled + unavailable
non_completed_rate = (non_completed / total_orders * 100) if total_orders else 0.0

metric_row = first_row(test)

tab_overview, tab_eda, tab_model, tab_feature, tab_data, tab_business = st.tabs([
    "Tổng quan", "Khám phá dữ liệu", "Đánh giá mô hình",
    "Đặc trưng mô hình", "Chất lượng dữ liệu", "Hàm ý quản trị"
])

with tab_overview:
    st.subheader("Tổng quan trạng thái đơn hàng")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng đơn có nhãn", f"{total_orders:,}")
    c2.metric("Đã giao", f"{delivered:,}")
    c3.metric("Không hoàn tất", f"{non_completed:,}")
    c4.metric("Tỷ lệ không hoàn tất", f"{non_completed_rate:.3f}%")

    fig = px.bar(
        status, x="order_status", y="orders", color="order_status",
        text="orders", title="Số lượng đơn theo trạng thái"
    )
    fig.update_layout(showlegend=False, xaxis_title="Trạng thái", yaxis_title="Số đơn")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Xu hướng theo tháng")
    if monthly is not None and not monthly.empty:
        m = monthly.copy()
        if "month" in m.columns:
            xcol = "month"
        else:
            xcol = m.columns[0]
        ycol = "risk_rate_pct" if "risk_rate_pct" in m.columns else None
        if ycol:
            fig = px.line(
                m, x=xcol, y=ycol, markers=True,
                hover_data=[c for c in ["order_count", "risk_count"] if c in m.columns],
                title="Tỷ lệ đơn không hoàn tất theo tháng"
            )
            fig.update_layout(xaxis_title="Tháng", yaxis_title="Tỷ lệ không hoàn tất (%)")
            st.plotly_chart(fig, use_container_width=True)
            if {"order_count", "risk_count"}.issubset(m.columns):
                st.caption("Luôn xem tỷ lệ cùng số đơn và số đơn không hoàn tất; tháng có ít đơn có thể tạo tỷ lệ dao động lớn.")
    else:
        st.info("Chưa có dữ liệu xu hướng theo tháng.")

with tab_eda:
    st.subheader("So sánh theo ngành hàng")
    cat = data["category"]
    if cat is not None and not cat.empty:
        required = {"main_category", "risk_rate_pct", "order_count"}
        if required.issubset(cat.columns):
            cat = cat.sort_values("risk_rate_pct", ascending=False).head(15)
            fig = px.bar(
                cat.sort_values("risk_rate_pct"),
                x="risk_rate_pct", y="main_category", orientation="h",
                hover_data=["order_count", "risk_count"] if "risk_count" in cat.columns else ["order_count"],
                title="Nhóm ngành hàng có tỷ lệ không hoàn tất cao"
            )
            fig.update_layout(xaxis_title="Tỷ lệ không hoàn tất (%)", yaxis_title="Ngành hàng")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.dataframe(cat, use_container_width=True)
    else:
        st.info("Chưa có dữ liệu ngành hàng.")

    st.subheader("So sánh theo phương thức thanh toán")
    pay = data["payment"]
    if pay is not None and not pay.empty:
        if {"payment_method_group", "risk_rate_pct", "order_count"}.issubset(pay.columns):
            pay = pay.sort_values("order_count", ascending=False)
            fig = px.bar(
                pay, x="payment_method_group", y="risk_rate_pct",
                hover_data=["order_count"], title="Tỷ lệ không hoàn tất theo nhóm thanh toán"
            )
            fig.update_layout(xaxis_title="Nhóm thanh toán", yaxis_title="Tỷ lệ không hoàn tất (%)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.dataframe(pay, use_container_width=True)

    st.subheader("Đặc điểm giỏ hàng theo nhãn")
    profile = data["profile"]
    if profile is not None and not profile.empty:
        st.dataframe(profile, use_container_width=True)
        for col, label in [
            ("median_total_price", "Trung vị giá trị sản phẩm"),
            ("median_total_freight", "Trung vị phí vận chuyển"),
            ("median_total_weight_g", "Trung vị trọng lượng"),
            ("median_estimated_delivery_days", "Trung vị số ngày giao dự kiến"),
        ]:
            if col in profile.columns:
                fig = px.bar(profile, x="label", y=col, title=label)
                fig.update_layout(xaxis_title="Nhãn (0 = đã giao, 1 = không hoàn tất)", yaxis_title=label)
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Chưa có bảng tổng hợp đặc điểm giỏ hàng.")

    st.subheader("Thời điểm đặt hàng")
    hourly = data["hourly"]
    if hourly is not None and not hourly.empty:
        fig = px.line(
            hourly, x="Purchase_Hour", y="risk_rate_pct", markers=True,
            hover_data=[c for c in ["order_count", "risk_count"] if c in hourly.columns],
            title="Tỷ lệ đơn không hoàn tất theo giờ đặt hàng"
        )
        fig.update_layout(xaxis_title="Giờ đặt hàng", yaxis_title="Tỷ lệ không hoàn tất (%)")
        st.plotly_chart(fig, use_container_width=True)
    weekend = data["weekend"]
    if weekend is not None and not weekend.empty:
        fig = px.bar(
            weekend, x="day_type", y="risk_rate_pct",
            hover_data=[c for c in ["order_count", "risk_count"] if c in weekend.columns],
            title="So sánh ngày thường và cuối tuần"
        )
        fig.update_layout(xaxis_title="Nhóm ngày", yaxis_title="Tỷ lệ không hoàn tất (%)")
        st.plotly_chart(fig, use_container_width=True)

with tab_model:
    st.subheader("So sánh mô hình trên tập Validation")
    if validation is not None and not validation.empty:
        st.dataframe(validation, use_container_width=True)
        metric_options = [c for c in ["Average_Precision", "ROC_AUC", "precision_at_0.5", "recall_at_0.5", "f1_at_0.5"] if c in validation.columns]
        if metric_options and "model" in validation.columns:
            chosen_metric = st.selectbox("Chỉ số so sánh", metric_options, index=0)
            fig = px.bar(
                validation, x="model", y=chosen_metric, text_auto=".4f",
                title=f"So sánh mô hình theo {chosen_metric}"
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Chưa có bảng so sánh Validation.")

    st.subheader("Kết quả cuối cùng trên tập Test")
    if test is not None and not test.empty:
        row = first_row(test)
        a, b, c, d = st.columns(4)
        a.metric("Precision", f"{num(row, 'precision')*100:.2f}%")
        b.metric("Recall", f"{num(row, 'recall')*100:.2f}%")
        c.metric("F2-score", f"{num(row, 'F2'):.3f}")
        d.metric("Average Precision", f"{num(row, 'PR_AUC_average_precision'):.3f}")
        st.caption(
            f"Mô hình: {row.get('model', 'N/A')} | "
            f"Accuracy: {num(row, 'accuracy')*100:.2f}% | "
            f"ROC-AUC: {num(row, 'ROC_AUC'):.3f} | "
            f"Ngưỡng: {num(row, 'threshold'):.3f}"
        )
        if all(k in row.index for k in ["TN", "FP", "FN", "TP"]):
            cm = [[int(row["TN"]), int(row["FP"])], [int(row["FN"]), int(row["TP"])]]
            fig = go.Figure(data=go.Heatmap(
                z=cm, x=["Dự đoán: đã giao", "Dự đoán: không hoàn tất"],
                y=["Thực tế: đã giao", "Thực tế: không hoàn tất"],
                text=[[f"{v:,}" for v in line] for line in cm],
                texttemplate="%{text}", colorscale="Blues", showscale=False
            ))
            fig.update_layout(title="Ma trận nhầm lẫn trên tập Test", xaxis_title="", yaxis_title="")
            st.plotly_chart(fig, use_container_width=True)
        st.warning(
            "Kết quả hiện tại cho thấy khả năng phát hiện lớp không hoàn tất còn thấp. "
            "Dashboard chỉ phục vụ trình bày và phân tích; chưa đủ căn cứ triển khai cảnh báo tự động."
        )
    else:
        st.info("Chưa có chỉ số Test.")

with tab_feature:
    st.subheader("Các đặc trưng có mức độ quan trọng cao")
    if importance is not None and not importance.empty:
        st.dataframe(importance.head(20), use_container_width=True)
        if {"feature", "importance"}.issubset(importance.columns):
            top = importance.sort_values("importance", ascending=False).head(15).sort_values("importance")
            fig = px.bar(top, x="importance", y="feature", orientation="h",
                         title="Top đặc trưng theo mức độ quan trọng")
            fig.update_layout(xaxis_title="Importance", yaxis_title="Đặc trưng")
            st.plotly_chart(fig, use_container_width=True)
        st.caption("Feature Importance phản ánh mức đóng góp trong mô hình, không chứng minh quan hệ nhân quả.")
    else:
        st.info("Chưa có bảng Feature Importance.")

with tab_data:
    st.subheader("Độ bao phủ dữ liệu theo trạng thái")
    coverage = data["coverage"]
    if coverage is not None:
        st.dataframe(coverage, use_container_width=True)
    st.subheader("Phân chia dữ liệu theo thời gian")
    split = data["split"]
    if split is not None:
        st.dataframe(split, use_container_width=True)
    st.caption("Ứng dụng công khai chỉ sử dụng các bảng tổng hợp. Không tải lên dữ liệu cấp đơn hàng, mã đơn hoặc thông tin nhận diện cá nhân.")

with tab_business:
    st.subheader("Hàm ý quản trị")
    st.markdown("""
    - Theo dõi đồng thời **số lượng đơn** và **tỷ lệ đơn không hoàn tất** theo tháng, ngành hàng và phương thức thanh toán.
    - Rà soát chất lượng dữ liệu và quy tắc ghi nhận trạng thái trước khi diễn giải biến động.
    - Không dùng riêng Feature Importance để kết luận nguyên nhân; cần kiểm chứng với quy trình nghiệp vụ.
    - Chưa sử dụng mô hình làm căn cứ tự động hủy đơn hoặc xử lý khách hàng do Recall lớp rủi ro còn thấp.
    """)
    st.subheader("Dữ liệu cần bổ sung để nghiên cứu logistics ngược")
    st.markdown("""
    - Yêu cầu trả hàng: mã đơn/sản phẩm, số lượng trả, thời điểm yêu cầu và lý do trả.
    - Vận chuyển: đơn vị vận chuyển, nhật ký sự kiện, số lần giao thất bại và mã ngoại lệ.
    - Kho và hàng hoàn: thời điểm nhận hàng hoàn, kết quả kiểm định, tình trạng sản phẩm và phương án xử lý.
    - Chi phí: tiền hoàn cho khách, phí vận chuyển ngược, chi phí kiểm định và xử lý.
    """)
    st.warning(
        "Nhãn hiện tại là đơn không hoàn tất (canceled/unavailable), không phải nhãn hàng đã trả về. "
        "Muốn xây dựng mô hình dự đoán trả hàng thực tế, cần dữ liệu trả hàng có nhãn và dấu thời gian."
    )

st.divider()
st.caption(
    "Sản phẩm học tập theo tình huống thực tập tại doanh nghiệp thương mại điện tử. "
    "Ứng dụng chỉ công khai dữ liệu tổng hợp và kết quả đánh giá; không hiển thị bản ghi giao dịch cá nhân."
)
