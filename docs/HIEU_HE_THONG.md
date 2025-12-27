# 📖 Hiểu Rõ Hệ Thống - Hướng Dẫn Cho Người Non-Tech

Tài liệu này giải thích chi tiết cách hệ thống **Predictive Maintenance (Bảo Trì Dự Đoán)** hoạt động, dành cho những người không có background kỹ thuật.

---

## 🎯 Mục Đích Của Hệ Thống

Hệ thống này giúp **dự đoán trước khi xe điện bị hỏng**, giống như bác sĩ dự đoán bệnh nhân có thể bị bệnh gì dựa trên các chỉ số sức khỏe.

**Ví dụ thực tế:**

- Thay vì đợi xe hỏng mới sửa (tốn kém, nguy hiểm)
- Hệ thống phân tích dữ liệu từ các cảm biến trên xe
- Dự đoán: "Xe này có 80% khả năng hỏng pin trong 30 ngày tới"
- → Chủ xe có thể sửa chữa phòng ngừa trước khi hỏng

---

## 🔤 Giải Thích Các Từ Khóa Chuyên Môn

### 1. **Predictive Maintenance (Bảo Trì Dự Đoán)**

- **Nghĩa đơn giản**: Bảo trì dựa trên dự đoán, không phải đợi hỏng mới sửa
- **Ví dụ**: Giống như bạn đi khám sức khỏe định kỳ để phát hiện bệnh sớm
- **Lợi ích**: Tiết kiệm chi phí, tránh hỏng hóc bất ngờ

### 2. **Machine Learning (Học Máy) / AI**

- **Nghĩa đơn giản**: Máy tính tự học từ dữ liệu để đưa ra dự đoán
- **Ví dụ**: Giống như bạn học lái xe, càng lái nhiều càng giỏi
- **Trong hệ thống**: Máy tính học từ hàng nghìn bản ghi dữ liệu xe để biết "xe nào sắp hỏng"

### 3. **Model (Mô Hình)**

- **Nghĩa đơn giản**: Công thức/bộ quy tắc mà máy tính đã học được
- **Ví dụ**: Giống như công thức nấu ăn - bạn cho nguyên liệu vào, ra món ăn
- **Trong hệ thống**: Cho dữ liệu cảm biến vào → Model → Dự đoán lỗi

### 4. **Training (Huấn Luyện)**

- **Nghĩa đơn giản**: Quá trình dạy máy tính học từ dữ liệu
- **Ví dụ**: Giống như học sinh học bài từ sách giáo khoa
- **Trong hệ thống**: Cho máy tính xem 100,000 bản ghi dữ liệu xe → Máy học pattern → Tạo ra model

### 5. **Inference (Suy Luận / Dự Đoán)**

- **Nghĩa đơn giản**: Sử dụng model đã học để dự đoán trên dữ liệu mới
- **Ví dụ**: Sau khi học xong, học sinh làm bài kiểm tra
- **Trong hệ thống**: Nhận dữ liệu cảm biến mới → Dùng model → Trả về dự đoán

### 6. **Anomaly (Bất Thường)**

- **Nghĩa đơn giản**: Điều gì đó khác thường, không bình thường
- **Ví dụ**: Nhiệt độ cơ thể 40°C là bất thường (bình thường là 37°C)
- **Trong hệ thống**: Phát hiện các giá trị cảm biến bất thường → Có thể là dấu hiệu hỏng hóc

### 7. **Feature (Đặc Trưng / Thuộc Tính)**

- **Nghĩa đơn giản**: Các thông tin đầu vào để dự đoán
- **Ví dụ**: Để dự đoán bệnh, bác sĩ cần: nhiệt độ, huyết áp, nhịp tim
- **Trong hệ thống**: Nhiệt độ pin, điện áp, số chu kỳ sạc, tốc độ, v.v.

### 8. **API (Application Programming Interface)**

- **Nghĩa đơn giản**: Cửa ngõ để các hệ thống khác giao tiếp với hệ thống của bạn
- **Ví dụ**: Giống như menu nhà hàng - bạn chọn món, nhà bếp nấu, mang ra
- **Trong hệ thống**: Gửi dữ liệu cảm biến → API → Nhận kết quả dự đoán

### 9. **Endpoint (Điểm Cuối)**

- **Nghĩa đơn giản**: Địa chỉ cụ thể trong API để thực hiện một chức năng
- **Ví dụ**: `/predict` = "Tôi muốn dự đoán", `/health` = "Kiểm tra hệ thống có hoạt động không"
- **Trong hệ thống**:
  - `POST /predict` → Gửi dữ liệu, nhận dự đoán
  - `GET /health` → Kiểm tra hệ thống

### 10. **Metrics (Chỉ Số / Số Liệu)**

- **Nghĩa đơn giản**: Các con số đo lường hiệu suất hệ thống
- **Ví dụ**: Số lượng khách hàng/ngày, thời gian phục vụ trung bình
- **Trong hệ thống**: Số request/giây, thời gian xử lý, số lần phát hiện anomaly

### 11. **Monitoring (Giám Sát)**

- **Nghĩa đơn giản**: Theo dõi, quan sát hệ thống hoạt động
- **Ví dụ**: Giống như dashboard xe hơi hiển thị tốc độ, nhiên liệu
- **Trong hệ thống**: Dashboard hiển thị: hệ thống có đang chạy không, có bao nhiêu request, có lỗi gì không

### 12. **Alert (Cảnh Báo)**

- **Nghĩa đơn giản**: Thông báo khi có điều gì bất thường
- **Ví dụ**: Điện thoại báo pin yếu, hoặc cảnh báo nhiệt độ cao
- **Trong hệ thống**: "Có quá nhiều anomaly trong 2 phút!" → Gửi cảnh báo

### 13. **Kafka (Message Queue)**

- **Nghĩa đơn giản**: Hệ thống chuyển tin nhắn giữa các phần của hệ thống
- **Ví dụ**: Giống như bưu điện - nhận thư từ người gửi, chuyển đến người nhận
- **Trong hệ thống**: Khi phát hiện anomaly → Gửi vào Kafka → Alert Service nhận → Xử lý cảnh báo

### 14. **Docker / Container**

- **Nghĩa đơn giản**: Công nghệ đóng gói ứng dụng và môi trường chạy vào một "hộp" riêng
- **Ví dụ**: Giống như container vận chuyển - mỗi container có môi trường riêng, không ảnh hưởng nhau
- **Lợi ích**: Chạy giống nhau trên mọi máy tính, dễ quản lý

### 15. **MLflow**

- **Nghĩa đơn giản**: Hệ thống quản lý và theo dõi các lần training model
- **Ví dụ**: Giống như sổ ghi chép thí nghiệm - ghi lại mỗi lần thử, kết quả, model nào tốt nhất
- **Trong hệ thống**: Lưu lại mỗi lần train, so sánh model cũ và mới, chọn model tốt nhất

---

## 🔄 Workflow Chi Tiết - Hệ Thống Hoạt Động Như Thế Nào?

### GIAI ĐOẠN 1: CHUẨN BỊ DỮ LIỆU VÀ TRAINING (Huấn Luyện)

#### Bước 1: Có Dữ Liệu

```
📊 Dữ liệu từ cảm biến xe điện
├── Nhiệt độ pin: 25°C, 30°C, 95°C...
├── Điện áp: 350V, 200V...
├── Số chu kỳ sạc: 50, 100, 2000...
├── Tốc độ: 60km/h, 120km/h...
└── ... (26 thông số khác)
```

**Giải thích**: Giống như bệnh án bệnh nhân - ghi lại tất cả thông tin quan trọng.

#### Bước 2: Training Model Anomaly (Phát Hiện Bất Thường)

**File**: `src/anomaly.py`

**Quá trình**:

1. Đọc dữ liệu từ file CSV
2. Chọn 9 thông số quan trọng nhất (nhiệt độ, điện áp, tốc độ...)
3. **Isolation Forest** (thuật toán) học pattern "bình thường"
4. Đánh dấu những điểm "khác thường" → Gọi là **Anomaly**
5. Lưu model vào `models/anomaly/`

**Ví dụ dễ hiểu**:

- Học sinh bình thường: điểm 5-10
- Isolation Forest học: "Điểm 5-10 là bình thường"
- Gặp điểm 0 hoặc 20 → "Bất thường!"

**Kết quả**: File `data/features_with_anomaly.parquet` chứa dữ liệu + cột "IF_Anomaly" (0 = bình thường, 1 = bất thường)

#### Bước 3: Training Model Classifier (Phân Loại Lỗi)

**File**: `src/classifier.py`

**Quá trình**:

1. Đọc file từ bước 2 (đã có nhãn Anomaly)
2. Chọn 26 thông số đầy đủ
3. **XGBoost** (thuật toán) học phân loại:
   - Input: 26 thông số cảm biến
   - Output: Loại lỗi (Battery Aging, Motor Overheat, Brake Failure...)
4. Xử lý **class imbalance** (có ít dữ liệu lỗi hơn dữ liệu bình thường)
5. Lưu model vào `models/classifier/`

**Ví dụ dễ hiểu**:

- Bác sĩ nhìn triệu chứng → Chẩn đoán bệnh
- Model nhìn 26 thông số → Dự đoán loại lỗi

**Kết quả**: Model biết phân loại: "Đây là lỗi pin" hay "Đây là lỗi motor"

#### Bước 4: Training Model RUL (Dự Đoán Tuổi Thọ Còn Lại)

**File**: `src/rul.py`

**Quá trình**:

1. Đọc dữ liệu từ bước 2
2. Sử dụng kết quả từ bước 3 (loại lỗi) như một thông số đầu vào
3. **LightGBM** (thuật toán) học dự đoán:
   - Input: 26 thông số + loại lỗi
   - Output: Số chu kỳ còn lại trước khi hỏng (RUL)
4. Lưu model vào `models/rul/`

**Ví dụ dễ hiểu**:

- Bác sĩ: "Bệnh nhân này còn sống được khoảng 6 tháng"
- Model: "Xe này còn chạy được khoảng 500 chu kỳ sạc"

**Kết quả**: Model biết dự đoán: "Còn bao lâu nữa thì hỏng?"

#### Bước 5: Lưu Vào MLflow

**File**: `src/train.py`

**Quá trình**:

1. Chạy lần lượt 3 bước trên
2. Upload tất cả models lên MLflow
3. Ghi lại metrics (độ chính xác, F1-score, RMSE...)
4. Lưu lại parameters (số lượng cây, learning rate...)

**Lợi ích**:

- So sánh model cũ vs mới
- Quay lại model cũ nếu model mới tệ hơn
- Theo dõi lịch sử training

---

### GIAI ĐOẠN 2: INFERENCE (Sử Dụng Model Để Dự Đoán)

#### Bước 1: Nhận Request Từ Người Dùng

**Endpoint**: `POST /predict`

**Input**: Dữ liệu cảm biến từ xe (JSON)

```json
{
  "data": {
    "SoC": 0.9,              // Mức pin: 90%
    "SoH": 0.95,             // Sức khỏe pin: 95%
    "Battery_Temperature": 25, // Nhiệt độ pin: 25°C
    "Charge_Cycles": 50,      // Đã sạc 50 lần
    ... (26 thông số)
  }
}
```

#### Bước 2: Anomaly Detection (Phát Hiện Bất Thường)

**Quá trình**:

1. Load model Isolation Forest từ `models/anomaly/`
2. Lấy 9 thông số quan trọng từ input
3. Model kiểm tra: "Dữ liệu này có bất thường không?"
4. **Rule Override**: Nếu SoH < 60% hoặc Charge_Cycles > 2000 → Coi như bất thường

**Kết quả**: `IF_Anomaly = 0` (bình thường) hoặc `1` (bất thường)

**Ví dụ**:

- Input: Nhiệt độ pin = 95°C (quá nóng!)
- Model: "Bất thường!" → `IF_Anomaly = 1`

#### Bước 3: Fault Classification (Phân Loại Lỗi) - Chỉ Khi Có Anomaly

**Quá trình** (chỉ chạy nếu `IF_Anomaly = 1`):

1. Load model XGBoost từ `models/classifier/`
2. Lấy 26 thông số từ input
3. Model phân loại: "Đây là loại lỗi gì?"
4. Decode kết quả: Số → Tên lỗi (ví dụ: 0 → "Battery Aging")
5. Kiểm tra: "Có phải lỗi không?" (so với normal_label)

**Kết quả**:

- `classifier_label`: "Battery Aging" hoặc "Motor Overheat"...
- `is_fault`: `true` (có lỗi) hoặc `false` (bình thường)

**Ví dụ**:

- Input: Nhiệt độ pin cao + Điện áp thấp
- Model: "Đây là lỗi Battery Aging" → `classifier_label = "Battery Aging"`, `is_fault = true`

#### Bước 4: RUL Prediction (Dự Đoán Tuổi Thọ) - Chỉ Khi Có Fault

**Quá trình** (chỉ chạy nếu `is_fault = true`):

1. Load model LightGBM từ `models/rul/`
2. Lấy 26 thông số + loại lỗi từ bước 3
3. Model dự đoán: "Còn bao nhiêu chu kỳ nữa thì hỏng?"

**Kết quả**: `RUL_estimated = 500` (ví dụ: còn 500 chu kỳ sạc)

**Ví dụ**:

- Input: Lỗi Battery Aging + Các thông số hiện tại
- Model: "Còn khoảng 500 chu kỳ sạc nữa thì pin sẽ hỏng hoàn toàn"

#### Bước 5: Trả Về Kết Quả

**Response**:

```json
{
  "IF_Anomaly": 1,
  "classifier_label": "Battery Aging",
  "is_fault": true,
  "RUL_estimated": 500
}
```

#### Bước 6: Gửi Cảnh Báo (Nếu Có Anomaly Hoặc Fault)

**Quá trình**:

1. Nếu `IF_Anomaly = 1` hoặc `is_fault = true`:
   - Tăng counter `anomaly_predictions_total` (để monitoring)
   - Gửi thông tin vào **Kafka** (topic: `ev_predictions`)
2. **Alert Service** nhận từ Kafka:
   - Tăng counter `anomaly_events_total`
   - Tăng counter `fault_events_total`
   - Cập nhật metric `rul_estimated`
3. **Prometheus** scrape metrics từ:
   - FastAPI (`/metrics`)
   - Alert Service (`:9101/metrics`)
4. **Prometheus Alerts** kiểm tra:
   - Nếu `anomaly_predictions_total` tăng quá nhanh → Gửi alert
   - Nếu latency quá cao → Gửi alert
5. **Alertmanager** nhận alerts và có thể:
   - Gửi email
   - Gửi Slack notification
   - Gửi SMS

---

## 🏗️ Kiến Trúc Hệ Thống - Các Thành Phần Làm Gì?

### 1. **FastAPI Inference Server** (Máy Chủ Dự Đoán)

**Vai trò**: Nhận request, chạy models, trả về kết quả

**Giống như**: Nhà hàng - nhận order, nấu ăn, phục vụ

**Các endpoint**:

- `/predict` - Nhận dữ liệu, trả về dự đoán
- `/health` - Kiểm tra hệ thống có hoạt động không
- `/metrics` - Trả về số liệu thống kê (cho Prometheus)
- `/api/train` - Trigger training mới

### 2. **Kafka** (Hệ Thống Tin Nhắn)

**Vai trò**: Chuyển tin nhắn giữa các phần của hệ thống

**Giống như**: Bưu điện - nhận thư, phân loại, chuyển đến đúng người

**Trong hệ thống**:

- FastAPI gửi: "Có anomaly!" → Kafka topic `ev_predictions`
- Alert Service đọc từ Kafka → Xử lý cảnh báo

**Lợi ích**:

- Tách biệt các phần (FastAPI không cần biết Alert Service)
- Đảm bảo không mất tin nhắn (lưu lại nếu Alert Service tạm thời down)

### 3. **Alert Service** (Dịch Vụ Cảnh Báo)

**Vai trò**: Nhận thông tin từ Kafka, tạo metrics, có thể gửi cảnh báo

**Giống như**: Trung tâm điều hành - nhận thông tin, xử lý, báo cáo

**Chức năng**:

- Đếm số anomaly events
- Đếm số fault events
- Lưu RUL estimate mới nhất
- Expose metrics cho Prometheus

### 4. **Prometheus** (Hệ Thống Thu Thập Số Liệu)

**Vai trò**: Thu thập và lưu trữ metrics từ các services

**Giống như**: Sổ ghi chép - ghi lại mọi số liệu quan trọng

**Chức năng**:

- Mỗi 10 giây: Hỏi FastAPI "Bạn có bao nhiêu requests?"
- Mỗi 10 giây: Hỏi Alert Service "Bạn có bao nhiêu anomalies?"
- Lưu lại tất cả số liệu theo thời gian
- Kiểm tra alert rules: "Nếu có quá nhiều anomalies → Gửi alert"

### 5. **Grafana** (Dashboard Hiển Thị)

**Vai trò**: Hiển thị metrics dưới dạng biểu đồ, bảng

**Giống như**: Dashboard xe hơi - hiển thị tốc độ, nhiên liệu bằng đồng hồ, biểu đồ

**Chức năng**:

- Kết nối với Prometheus (tự động)
- Hiển thị: Số requests/giây, Latency, Số anomalies
- Tạo dashboard tùy chỉnh
- Cảnh báo trực quan (màu đỏ khi có vấn đề)

### 6. **MLflow** (Quản Lý Models)

**Vai trò**: Lưu trữ và quản lý các lần training

**Giống như**: Thư viện - lưu trữ sách (models), có catalog để tìm

**Chức năng**:

- Lưu mỗi lần training như một "run"
- Ghi lại: Model nào, parameters gì, kết quả ra sao
- So sánh: Model cũ vs mới, model nào tốt hơn
- Lưu artifacts (files models, confusion matrix...)

### 7. **MinIO** (Kho Lưu Trữ)

**Vai trò**: Lưu trữ files (models, datasets...)

**Giống như**: Google Drive - lưu files trên cloud

**Chức năng**:

- MLflow lưu models vào MinIO
- Có thể tải về, backup, restore

### 8. **Alertmanager** (Quản Lý Cảnh Báo)

**Vai trò**: Nhận alerts từ Prometheus, xử lý và gửi thông báo

**Giống như**: Trung tâm cuộc gọi khẩn cấp - nhận báo, quyết định gửi đến ai

**Chức năng**:

- Nhận alerts từ Prometheus
- Quyết định: Gửi email? SMS? Slack?
- Tránh spam (không gửi quá nhiều alerts giống nhau)

---

## 📊 Ví Dụ Workflow Hoàn Chỉnh

### Tình Huống: Xe Điện Đang Chạy, Gửi Dữ Liệu Cảm Biến

#### Bước 1: Xe Gửi Dữ Liệu

```
Xe điện → Gửi dữ liệu cảm biến mỗi 15 phút
├── Nhiệt độ pin: 95°C (QUÁ NÓNG!)
├── Điện áp: 200V (thấp)
├── Số chu kỳ sạc: 2100 (nhiều)
└── ... (24 thông số khác)
```

#### Bước 2: FastAPI Nhận Request

```
POST /predict
{
  "data": {
    "Battery_Temperature": 95,
    "Battery_Voltage": 200,
    "Charge_Cycles": 2100,
    ...
  }
}
```

#### Bước 3: Anomaly Detection

```
Isolation Forest Model:
├── Kiểm tra: Nhiệt độ 95°C → Bất thường!
├── Rule Override: Charge_Cycles = 2100 > 2000 → Bất thường!
└── Kết quả: IF_Anomaly = 1 ✅
```

#### Bước 4: Fault Classification

```
XGBoost Model:
├── Phân tích 26 thông số
├── So sánh với patterns đã học
└── Kết quả: "Battery Aging" (Pin đã già)
    ├── classifier_label = "Battery Aging"
    └── is_fault = true ✅
```

#### Bước 5: RUL Prediction

```
LightGBM Model:
├── Input: 26 thông số + "Battery Aging"
├── Dự đoán dựa trên lịch sử
└── Kết quả: RUL_estimated = 300
    → "Còn khoảng 300 chu kỳ sạc nữa thì pin hỏng hoàn toàn"
```

#### Bước 6: Trả Về Kết Quả

```json
{
  "IF_Anomaly": 1,
  "classifier_label": "Battery Aging",
  "is_fault": true,
  "RUL_estimated": 300
}
```

#### Bước 7: Gửi Cảnh Báo

```
FastAPI → Kafka (topic: ev_predictions)
  → Alert Service nhận
    → Tăng counter: anomaly_events_total
    → Tăng counter: fault_events_total
    → Prometheus scrape metrics
      → Kiểm tra alert rules
        → "Có quá nhiều anomalies!" → Alertmanager
          → Gửi email/Slack cho kỹ sư
```

#### Bước 8: Monitoring

```
Grafana Dashboard hiển thị:
├── Biểu đồ: Số anomalies/giờ (tăng đột biến!)
├── Bảng: Các lỗi phổ biến (Battery Aging: 10 lần)
└── Cảnh báo: "High Anomaly Rate" (màu đỏ)
```

---

## 🔍 Giải Thích Các Thuật Toán

### 1. **Isolation Forest (Rừng Cô Lập)**

**Mục đích**: Phát hiện điểm bất thường

**Cách hoạt động** (đơn giản):

1. Tạo nhiều "cây" ngẫu nhiên
2. Mỗi cây cố gắng "cô lập" (tách biệt) một điểm
3. Điểm bất thường dễ cô lập hơn (ít điểm xung quanh)
4. Nếu nhiều cây cô lập được điểm đó → Điểm đó là bất thường

**Ví dụ**:

- Trong lớp 30 học sinh, 29 người cao 1.6m-1.8m
- Có 1 người cao 2.2m → Dễ "cô lập" → Bất thường!

### 2. **XGBoost (Extreme Gradient Boosting)**

**Mục đích**: Phân loại (classification) - "Đây là loại lỗi gì?"

**Cách hoạt động** (đơn giản):

1. Tạo nhiều "cây quyết định" (decision trees)
2. Mỗi cây học từ lỗi của cây trước
3. Kết hợp tất cả cây → Dự đoán chính xác hơn

**Ví dụ**:

- Cây 1: "Nếu nhiệt độ > 90°C → Có thể là lỗi pin"
- Cây 2: "Nếu điện áp < 250V → Xác nhận lỗi pin"
- Cây 3: "Nếu số chu kỳ > 2000 → Xác nhận lỗi pin"
- Kết hợp 3 cây → "Đây chắc chắn là lỗi Battery Aging"

### 3. **LightGBM (Light Gradient Boosting Machine)**

**Mục đích**: Hồi quy (regression) - "Còn bao nhiêu chu kỳ nữa?"

**Cách hoạt động**: Tương tự XGBoost nhưng:

- Nhanh hơn
- Dùng ít bộ nhớ hơn
- Phù hợp cho dữ liệu lớn

**Ví dụ**:

- Input: Nhiệt độ cao + Điện áp thấp + Đã sạc 2100 lần
- Model: "Dựa trên pattern đã học, pin này còn khoảng 300 chu kỳ nữa"

---

## 🎓 Tại Sao Cần 3 Models?

### Model 1: Anomaly Detection (Phát Hiện Bất Thường)

- **Mục đích**: Lọc nhanh - "Có gì bất thường không?"
- **Lợi ích**: Không cần chạy 2 model sau nếu không có bất thường → Tiết kiệm tài nguyên
- **Ví dụ**: Giống như bác sĩ khám sơ bộ trước khi làm xét nghiệm chi tiết

### Model 2: Fault Classification (Phân Loại Lỗi)

- **Mục đích**: Xác định loại lỗi cụ thể
- **Lợi ích**: Biết sửa cái gì, mua phụ tùng gì
- **Ví dụ**: Không chỉ biết "có lỗi", mà còn biết "lỗi pin" hay "lỗi motor"

### Model 3: RUL Prediction (Dự Đoán Tuổi Thọ)

- **Mục đích**: Biết còn bao lâu nữa thì hỏng
- **Lợi ích**: Lên kế hoạch sửa chữa, đặt phụ tùng trước
- **Ví dụ**: "Còn 300 chu kỳ nữa" → Sắp xếp lịch sửa trong 2 tháng tới

---

## 🔄 Vòng Đời Của Một Request

```
1. Client gửi request
   ↓
2. FastAPI nhận tại /predict
   ↓
3. Middleware bắt đầu đo thời gian
   ↓
4. Anomaly Detection
   ├── Nếu bình thường → Trả về ngay
   └── Nếu bất thường → Tiếp tục
   ↓
5. Fault Classification
   ├── Nếu không phải lỗi → Trả về
   └── Nếu là lỗi → Tiếp tục
   ↓
6. RUL Prediction
   ↓
7. Tăng metrics (anomaly_predictions_total nếu có anomaly)
   ↓
8. Gửi vào Kafka (nếu có anomaly/fault)
   ↓
9. Middleware kết thúc, ghi latency
   ↓
10. Trả về response cho client
```

---

## 📈 Monitoring & Alerts - Giám Sát Hệ Thống

### Metrics Quan Trọng

1. **inference_requests_total**

   - **Nghĩa**: Tổng số requests đã xử lý
   - **Dùng để**: Biết hệ thống có đang hoạt động không
   - **Alert**: Nếu = 0 trong 5 phút → "Không có traffic"

2. **inference_request_latency_seconds**

   - **Nghĩa**: Thời gian xử lý mỗi request
   - **Dùng để**: Đảm bảo hệ thống nhanh
   - **Alert**: Nếu p95 > 500ms → "Hệ thống chậm"

3. **anomaly_predictions_total**
   - **Nghĩa**: Tổng số lần phát hiện anomaly
   - **Dùng để**: Theo dõi số lượng xe có vấn đề
   - **Alert**: Nếu tăng quá nhanh (5+ trong 2 phút) → "Có vấn đề nghiêm trọng"

### Alerts Đã Cấu Hình

1. **FastAPIInferenceDown**

   - **Khi nào**: FastAPI không phản hồi trong 30 giây
   - **Ý nghĩa**: Hệ thống bị down
   - **Hành động**: Kiểm tra logs, restart service

2. **HighInferenceLatency**

   - **Khi nào**: p95 latency > 500ms trong 1 phút
   - **Ý nghĩa**: Hệ thống chậm, có thể quá tải
   - **Hành động**: Kiểm tra tài nguyên, scale up

3. **HighAnomalyRate**

   - **Khi nào**: 5+ anomalies trong 2 phút
   - **Ý nghĩa**: Có nhiều xe có vấn đề
   - **Hành động**: Kiểm tra dữ liệu, có thể có bug trong model

4. **NoInferenceTraffic**
   - **Khi nào**: Không có request nào trong 5 phút
   - **Ý nghĩa**: Client không gửi dữ liệu, hoặc có vấn đề kết nối
   - **Hành động**: Kiểm tra client, network

---

## 🛠️ Các File Quan Trọng Trong Hệ Thống

### Training Scripts

1. **`src/anomaly.py`**

   - Train Isolation Forest
   - Tạo file parquet với cột IF_Anomaly

2. **`src/classifier.py`**

   - Train XGBoost classifier
   - Xử lý class imbalance
   - Lưu confusion matrix

3. **`src/rul.py`**

   - Train LightGBM RUL model
   - Tính RMSE, MAE, R²

4. **`src/train.py`**
   - Orchestrator - chạy 3 scripts trên
   - Upload lên MLflow

### Inference

5. **`src/inference_server.py`**
   - FastAPI application
   - Load models, xử lý requests
   - Expose endpoints

### Monitoring

6. **`monitoring/prometheus.yml`**

   - Cấu hình Prometheus
   - Định nghĩa jobs để scrape

7. **`monitoring/alerts.yml`**

   - Định nghĩa alert rules
   - Khi nào gửi alert, gửi gì

8. **`monitoring/grafana/provisioning/`**
   - Tự động cấu hình Grafana
   - Datasource, dashboards

### Alert Service

9. **`alert_service/main.py`**
   - Đọc từ Kafka
   - Tạo metrics
   - Expose cho Prometheus

---

## ❓ Câu Hỏi Thường Gặp (FAQ)

### Q1: Tại sao cần 3 models riêng biệt?

**A**: Mỗi model giải quyết một vấn đề khác nhau:

- Anomaly: "Có bất thường không?" → Nhanh, rẻ
- Classifier: "Lỗi gì?" → Cần biết để sửa đúng
- RUL: "Còn bao lâu?" → Cần biết để lên kế hoạch

Nếu chỉ dùng 1 model → Phức tạp, chậm, khó maintain.

### Q2: Tại sao cần Kafka?

**A**:

- **Tách biệt**: FastAPI không cần biết Alert Service
- **Reliability**: Nếu Alert Service down, messages được lưu lại
- **Scalability**: Có thể thêm nhiều services đọc từ Kafka
- **Async**: FastAPI không phải đợi Alert Service xử lý xong

### Q3: Tại sao cần Prometheus + Grafana?

**A**:

- **Prometheus**: Thu thập và lưu trữ metrics (database)
- **Grafana**: Hiển thị metrics (dashboard)

Giống như: Excel lưu số liệu, PowerPoint hiển thị biểu đồ.

### Q4: Model có tự cập nhật không?

**A**: Không tự động. Cần:

1. Train model mới: `docker compose run --rm trainer`
2. Models được lưu vào `models/`
3. Restart FastAPI: `docker compose restart fastapi-inference`
4. FastAPI tự động load models mới

### Q5: Làm sao biết model mới tốt hơn model cũ?

**A**: Xem trong MLflow:

- So sánh metrics: Accuracy, F1-score, RMSE
- Model nào có metrics tốt hơn → Model đó tốt hơn
- Có thể quay lại model cũ nếu model mới tệ hơn

### Q6: Hệ thống có thể xử lý bao nhiêu requests/giây?

**A**: Phụ thuộc vào:

- Hardware (CPU, RAM)
- Model complexity
- Thường: 10-100 requests/giây trên máy thông thường

Có thể scale bằng cách:

- Thêm nhiều FastAPI instances
- Dùng load balancer

### Q7: Dữ liệu được lưu ở đâu?

**A**:

- **Training data**: File CSV trong `src/data/`
- **Models**: Thư mục `models/` (local) + MLflow (remote)
- **Metrics**: Prometheus database
- **Artifacts**: MinIO (S3-compatible storage)

### Q8: Làm sao backup hệ thống?

**A**:

- **Models**: Backup thư mục `models/` hoặc export từ MLflow
- **Configs**: Backup `monitoring/`, `docker-compose.yml`
- **Data**: Backup `src/data/` và MinIO buckets

---

## 📚 Tài Liệu Tham Khảo Thêm

- `README.md` - Hướng dẫn chạy nhanh
- `docs/WORKFLOW_GUIDE.md` - Workflow chi tiết 9 bước
- `docs/QUICK_WORKFLOW.md` - Tóm tắt lệnh nhanh
- `docs/DOCKER_WORKFLOW.md` - Hướng dẫn Docker
- `docs/PROMETHEUS_DEBUG.md` - Debug Prometheus và alerts

---

## 🎯 Tóm Tắt

Hệ thống này giúp:

1. **Dự đoán** xe điện sắp hỏng (trước khi hỏng)
2. **Phân loại** loại lỗi cụ thể (pin, motor, phanh...)
3. **Ước lượng** còn bao lâu nữa thì hỏng
4. **Cảnh báo** khi có vấn đề
5. **Giám sát** hiệu suất hệ thống

Tất cả tự động hóa, giúp tiết kiệm chi phí và tăng độ an toàn.

---

**Tác giả**: Hệ thống MLOps cho Predictive Maintenance  
**Phiên bản**: 1.0  
**Cập nhật**: 2024
