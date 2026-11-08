# Dashboard quản trị đơn hàng thương mại điện tử

Ứng dụng Streamlit công khai để trình bày các kết quả tổng hợp của dự án:
- Tổng quan trạng thái đơn hàng.
- Phân tích EDA theo tháng, ngành hàng, phương thức thanh toán, giá trị giỏ hàng và thời điểm đặt hàng.
- So sánh mô hình trên Validation và đánh giá trên Test.
- Confusion Matrix và Feature Importance.
- Độ phủ dữ liệu, hàm ý quản trị và dữ liệu cần bổ sung cho logistics ngược.

**Phạm vi kết quả:** mô hình phân loại đơn hàng không hoàn tất (`canceled`/`unavailable`) so với đơn đã giao (`delivered`). Đây không phải mô hình dự đoán sản phẩm được khách hàng trả lại. Dashboard không cung cấp dự đoán đơn hàng mới và không khuyến nghị tự động can thiệp đơn hàng.

## 1. Vì sao dashboard dùng dữ liệu tổng hợp?

Repository có thể được đặt ở chế độ công khai để mọi người xem được ứng dụng. Vì vậy, chỉ đưa các bảng thống kê tổng hợp vào thư mục `output/`. Không đưa mã đơn hàng, mã khách hàng, dữ liệu giao dịch từng dòng hoặc dữ liệu thô lên GitHub.

## 2. Chuẩn bị dữ liệu tổng hợp trên máy của bạn

Trước hết, chạy notebook đến cuối để tạo thư mục `output` gồm các file:
- `order_level_labeled.csv`
- `model_cohort.csv`
- `data_coverage_by_status.csv`
- `model_validation_comparison.csv`
- `model_test_metrics.csv`
- `model_feature_importance.csv`
- `split_period_summary.csv`

Giải nén bộ triển khai này. Mở CMD/Terminal trong thư mục vừa giải nén và chạy:

```bash
pip install pandas
python prepare_public_data.py "C:\duong_dan_den_thu_muc_output_cua_notebook"
```

Ví dụ, thay đường dẫn bằng đúng thư mục output trên máy của bạn. Script sẽ tạo các CSV tổng hợp trong `output/` của dự án triển khai.

**Không chép các file `order_level_labeled.csv`, `model_cohort.csv`, `test_order_risk_predictions.csv` hoặc dữ liệu thô vào repository công khai.** Script chỉ đọc các file đầy đủ ở máy cá nhân rồi xuất những thống kê tổng hợp cần thiết.

## 3. Kiểm tra chạy ở máy cá nhân

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

Mở địa chỉ Local URL mà Streamlit hiển thị. Kiểm tra tất cả các tab trước khi công khai.

## 4. Đưa mã nguồn lên GitHub

1. Đăng nhập https://github.com/.
2. Chọn **New repository**.
3. Đặt tên, ví dụ `dashboard-quan-tri-don-hang`.
4. Chọn **Public** nếu muốn giảng viên/người xem mở ứng dụng không cần xin quyền truy cập. (Vì public, mã nguồn và các CSV tổng hợp trong repo cũng công khai.)
5. Tạo repository.
6. Upload các thành phần trong thư mục này: `app.py`, `requirements.txt`, `prepare_public_data.py`, `README.md`, thư mục `.streamlit/` và các CSV trong `output/`.
7. Không upload dữ liệu gốc, notebook có đường dẫn máy cá nhân, file chứa đơn hàng từng dòng, secrets hoặc mật khẩu.

## 5. Deploy trên Streamlit Community Cloud

1. Mở https://share.streamlit.io/.
2. Đăng nhập bằng GitHub.
3. Chọn **Create app** → **Yup, I have an app**.
4. Chọn repository `dashboard-quan-tri-don-hang`.
5. Branch: `main`.
6. Main file path: `app.py`.
7. Có thể đặt custom subdomain, ví dụ `quan-tri-don-hang` (nếu còn trống).
8. Chọn Python 3.11 trong **Advanced settings** nếu giao diện cho chọn.
9. Nhấn **Deploy**.

Khi triển khai thành công, nền tảng cấp địa chỉ HTTPS có dạng:

`https://ten-ung-dung.streamlit.app`

Đây là địa chỉ truy cập qua Internet, khác với địa chỉ mạng nội bộ kiểu `http://192.168.x.x:8501`.

## 6. Cập nhật ứng dụng

Khi sửa `app.py` hoặc `requirements.txt`, commit và push thay đổi lên GitHub; Community Cloud sẽ tự cập nhật ứng dụng từ repository. Không cần chạy máy tính cá nhân liên tục.

## 7. Giới hạn của gói Community Cloud miễn phí

Community Cloud hỗ trợ triển khai ứng dụng miễn phí từ GitHub và cấp URL công khai. Ứng dụng không có lượt truy cập trong 12 giờ sẽ chuyển sang trạng thái ngủ; lượt truy cập tiếp theo có thể đánh thức lại ứng dụng. Vì vậy, nó phù hợp để trình diễn báo cáo/thực tập, nhưng không phải cam kết máy chủ luôn hoạt động 24/7.

## 8. Nếu gặp lỗi deploy

- **Không tìm thấy file CSV:** kiểm tra các file tổng hợp đã nằm trong `output/` và đã được upload lên GitHub.
- **ModuleNotFoundError:** kiểm tra `requirements.txt` nằm cạnh `app.py` hoặc ở root repository.
- **App không khởi động:** mở App → Manage app → Logs, sao chép dòng lỗi màu đỏ để kiểm tra.
- **Bộ nhớ vượt giới hạn:** không upload bảng cấp đơn hàng/dữ liệu lớn; dùng lại script tạo CSV tổng hợp.
- **URL local không truy cập ngoài mạng:** `192.168...` là IP nội bộ; dùng URL `*.streamlit.app` sau deploy.

Tài liệu chính thức:
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies
- https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app
