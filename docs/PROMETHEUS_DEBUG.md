# 🔍 Prometheus Debug Guide

Hướng dẫn debug và kiểm tra Prometheus hoạt động đúng.

## ❌ Vấn đề thường gặp

### 1. Alert không hoạt động

**Nguyên nhân**: Job name trong `prometheus.yml` không khớp với alert rule.

**Kiểm tra**:

```bash
# Xem job name trong prometheus.yml
cat monitoring/prometheus.yml | grep job_name

# Xem alert rule query
cat monitoring/alerts.yml | grep job=
```

**Sửa**: Đảm bảo job name nhất quán giữa 2 file.

### 2. Graph không hiển thị

**Nguyên nhân**:

- Chưa có metrics được scrape
- Query sai
- Service chưa expose `/metrics`

**Kiểm tra**:

#### Bước 1: Xem Prometheus có scrape được không

1. Mở Prometheus UI: http://localhost:9090
2. Vào **Status → Targets**
3. Kiểm tra:
   - `fastapi-inference` có **UP** không?
   - `alert-service` có **UP** không?

Nếu **DOWN**:

- Kiểm tra service có đang chạy: `docker compose ps`
- Kiểm tra network: `docker compose exec prometheus ping fastapi-inference`

#### Bước 2: Kiểm tra metrics có tồn tại không

1. Vào **Graph** tab
2. Thử query đơn giản:

```promql
up{job="fastapi-inference"}
```

Nếu trả về `1` → Service đang UP, Prometheus scrape được.

Nếu trả về `0` hoặc không có kết quả → Service DOWN hoặc chưa scrape được.

#### Bước 3: Xem tất cả metrics có sẵn

Query:

```promql
{job="fastapi-inference"}
```

Hoặc xem danh sách metrics:

- Vào **Graph** → gõ `{` → Prometheus sẽ suggest các label
- Hoặc vào **Status → Targets** → click vào `fastapi-inference` → xem **Last Scrape** và **Scrape Error**

### 3. Test Alert FastAPIInferenceDown

**Các bước**:

1. **Kiểm tra trước khi test**:

   ```promql
   up{job="fastapi-inference"}
   ```

   Phải trả về `1`

2. **Dừng FastAPI**:

   ```bash
   docker compose stop fastapi-inference
   ```

3. **Chờ 30-40 giây** (alert rule có `for: 30s`)

4. **Kiểm tra alert**:

   - Vào **Alerts** tab trong Prometheus UI
   - Tìm `FastAPIInferenceDown`
   - Trạng thái phải là **FIRING** (màu đỏ)

5. **Kiểm tra query**:

   ```promql
   up{job="fastapi-inference"}
   ```

   Phải trả về `0` hoặc không có kết quả

6. **Bật lại FastAPI**:

   ```bash
   docker compose start fastapi-inference
   ```

7. **Chờ vài giây** → Alert sẽ tự động **RESOLVED**

## 📊 Query mẫu để test Graph

### 1. Kiểm tra service UP/DOWN

```promql
up{job="fastapi-inference"}
```

### 2. Số lượng request

```promql
inference_requests_total{job="fastapi-inference"}
```

### 3. Rate của request (requests/giây)

```promql
rate(inference_requests_total{job="fastapi-inference"}[1m])
```

### 4. Số lượng anomaly predictions

```promql
anomaly_predictions_total{job="fastapi-inference"}
```

### 5. Latency (p95)

```promql
histogram_quantile(
  0.95,
  sum by (le) (
    rate(inference_request_latency_seconds_bucket{job="fastapi-inference"}[2m])
  )
)
```

### 6. Tất cả metrics từ FastAPI

```promql
{job="fastapi-inference"}
```

## 🔧 Troubleshooting

### Prometheus không scrape được

1. **Kiểm tra network**:

   ```bash
   docker compose exec prometheus ping fastapi-inference
   ```

2. **Kiểm tra metrics endpoint**:

   ```bash
   curl http://localhost:8000/metrics
   ```

   Phải trả về text metrics (Prometheus format)

3. **Xem log Prometheus**:

   ```bash
   docker compose logs prometheus | grep -i error
   ```

4. **Restart Prometheus**:
   ```bash
   docker compose restart prometheus
   ```

### Alert không fire

1. **Kiểm tra rule đã load chưa**:

   - Vào **Status → Rules**
   - Tìm group `ev-ml-inference-alerts`
   - Xem có lỗi không

2. **Test query trực tiếp**:

   - Vào **Graph**
   - Chạy query trong alert rule
   - Xem có kết quả không

3. **Kiểm tra `for` duration**:
   - Alert chỉ fire sau khi điều kiện đúng trong `for` giây
   - Ví dụ: `for: 30s` → phải đợi 30 giây

### Graph không hiển thị

1. **Chọn time range đúng**:

   - Click vào time picker (góc trên bên phải)
   - Chọn **Last 5 minutes** hoặc **Last 1 hour**

2. **Kiểm tra query có kết quả**:

   - Query phải trả về số liệu trong time range đã chọn
   - Nếu không có data trong quá khứ, chỉ query **Last 5 minutes**

3. **Thử query đơn giản trước**:
   ```promql
   up
   ```
   Nếu query này không có kết quả → Prometheus chưa scrape được gì cả

## ✅ Checklist Debug

- [ ] Prometheus container đang chạy: `docker compose ps prometheus`
- [ ] FastAPI container đang chạy: `docker compose ps fastapi-inference`
- [ ] Metrics endpoint accessible: `curl http://localhost:8000/metrics`
- [ ] Prometheus scrape được: `up{job="fastapi-inference"}` = 1
- [ ] Alert rule đã load: **Status → Rules**
- [ ] Job name khớp giữa `prometheus.yml` và `alerts.yml`
- [ ] Time range trong Graph đúng (Last 5 minutes)

## 📚 Tài liệu tham khảo

- [Prometheus Querying](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Prometheus Alerting](https://prometheus.io/docs/alerting/latest/overview/)
