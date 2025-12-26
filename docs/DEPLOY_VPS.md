# Hướng dẫn Deploy lên VPS Ubuntu 24.04 LTS

Hướng dẫn chi tiết để deploy dự án MLOps EV Predictive Maintenance lên VPS Ubuntu 24.04 LTS.

## 📋 Yêu cầu hệ thống

- **OS**: Ubuntu 24.04 LTS x64
- **Docker**: Đã cài đặt Docker và Docker Compose
- **Git**: Đã cài đặt Git
- **RAM**: Tối thiểu 4GB (khuyến nghị 8GB+)
- **Disk**: Tối thiểu 20GB trống
- **Network**: Có kết nối internet để pull Docker images

## 🔧 Bước 1: Kiểm tra môi trường

### Kiểm tra Docker

```bash
# Kiểm tra Docker version
docker --version

# Kiểm tra Docker Compose
docker compose version

# Kiểm tra Docker daemon đang chạy
docker info
```

### Kiểm tra Git

```bash
git --version
```

### Kiểm tra ports cần thiết

Các ports sau sẽ được sử dụng:

- `2181` - Zookeeper
- `9092` - Kafka
- `9000` - MinIO API
- `9001` - MinIO Console
- `5000` - MLflow UI
- `8000` - FastAPI Inference API
- `9101` - Alert Service
- `9093` - Alertmanager
- `9090` - Prometheus
- `3000` - Grafana

Kiểm tra ports đang sử dụng:

```bash
sudo netstat -tuln | grep -E ':(2181|9092|9000|9001|5000|8000|9101|9093|9090|3000)'
```

## 📥 Bước 2: Clone dự án

Nếu chưa clone, thực hiện:

```bash
# Clone repository
git clone https://github.com/appdev1307/MSE24_MLOP_EV_PM.git

# Di chuyển vào thư mục dự án
cd MSE24_MLOP_EV_PM
```

Nếu đã clone, đảm bảo code là mới nhất:

```bash
cd MSE24_MLOP_EV_PM
git pull origin main
```

## 📊 Bước 3: Kiểm tra Dataset

Dataset cần có tại: `src/data/EV_Predictive_Maintenance_Dataset_15min.csv`

```bash
# Kiểm tra dataset
ls -lh src/data/EV_Predictive_Maintenance_Dataset_15min.csv
```

Nếu chưa có dataset, bạn cần:

1. Download từ Kaggle
2. Hoặc sử dụng script download (nếu có quyền truy cập)

## 🔥 Bước 4: Cấu hình Firewall (nếu cần)

Nếu VPS có firewall (UFW), mở các ports cần thiết:

```bash
# Mở ports cho các services
sudo ufw allow 8000/tcp  # FastAPI
sudo ufw allow 5000/tcp  # MLflow
sudo ufw allow 3000/tcp  # Grafana
sudo ufw allow 9090/tcp  # Prometheus

# Kiểm tra status
sudo ufw status
```

## 🚀 Bước 5: Deploy bằng script tự động (Khuyến nghị)

Sử dụng script deploy tự động:

```bash
# Cấp quyền thực thi (QUAN TRỌNG!)
chmod +x scripts/deploy_vps.sh
chmod +x scripts/download_dataset.sh

# Chạy script deploy
./scripts/deploy_vps.sh

# Nếu gặp lỗi "Permission denied", xem phần Troubleshooting bên dưới
```

Script sẽ tự động:

- ✅ Kiểm tra prerequisites
- ✅ Kiểm tra dataset
- ✅ Kiểm tra ports
- ✅ Build Docker images
- ✅ Start tất cả services
- ✅ Hiển thị thông tin truy cập

## 🛠️ Bước 6: Deploy thủ công (nếu cần)

Nếu không dùng script, thực hiện từng bước:

### 6.1. Build Docker images

```bash
# Build tất cả images
docker compose build

# Hoặc build từng service
docker compose build trainer
docker compose build fastapi-inference
docker compose build alert-service
```

### 6.2. Start services và tạo MinIO bucket

```bash
# Start MinIO trước
docker compose up -d minio

# Đợi MinIO sẵn sàng (5-10 giây)
sleep 5

# Tạo bucket cho MLflow artifacts (QUAN TRỌNG!)
chmod +x scripts/create_minio_bucket.sh
./scripts/create_minio_bucket.sh

# Hoặc tạo bucket thủ công:
docker compose exec minio mc alias set local http://localhost:9000 minioadmin minioadmin
docker compose exec minio mc mb local/mlflow-artifacts

# Start tất cả services còn lại
# Nếu gặp "permission denied", thử:
# - Thêm user vào docker group (xem Troubleshooting)
# - Hoặc dùng: sudo docker compose up -d
docker compose up -d

# Kiểm tra status
docker compose ps
```

### 6.3. Xem logs

```bash
# Xem logs tất cả services
docker compose logs -f

# Xem logs service cụ thể
docker compose logs -f fastapi-inference
docker compose logs -f mlflow
```

## 🎯 Bước 7: Train Models (Bắt buộc)

Trước khi sử dụng inference API, cần train models:

```bash
# Train tất cả models
docker compose run --rm trainer
```

Quá trình training sẽ:

1. Train Anomaly Detection model (Isolation Forest)
2. Train Classifier model (XGBoost)
3. Train RUL Prediction model (LightGBM)
4. Log models vào MLflow
5. Register models vào MLflow Model Registry

**Lưu ý**: Training có thể mất 5-15 phút tùy vào cấu hình VPS.

## ✅ Bước 8: Kiểm tra Services

### 8.1. Kiểm tra FastAPI Inference API

```bash
# Health check
curl http://localhost:8000/health

# Hoặc mở browser
# http://YOUR_VPS_IP:8000/docs
```

### 8.2. Kiểm tra MLflow

```bash
# Mở browser
# http://YOUR_VPS_IP:5000
```

### 8.3. Kiểm tra Grafana

```bash
# Mở browser
# http://YOUR_VPS_IP:3000
# Username: admin
# Password: admin
```

## 🌐 Bước 9: Cấu hình Domain/Reverse Proxy (Tùy chọn)

Nếu muốn truy cập qua domain thay vì IP, cấu hình Nginx reverse proxy:

### Cài đặt Nginx

```bash
sudo apt update
sudo apt install nginx -y
```

### Cấu hình Nginx cho FastAPI

Tạo file `/etc/nginx/sites-available/mlops-api`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/mlops-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 📝 Các lệnh quản lý thường dùng

### Xem status services

```bash
docker compose ps
```

### Xem logs

```bash
# Tất cả services
docker compose logs -f

# Service cụ thể
docker compose logs -f fastapi-inference
docker compose logs -f trainer
docker compose logs -f mlflow
```

### Restart service

```bash
docker compose restart fastapi-inference
```

### Stop services

```bash
# Stop tất cả
docker compose down

# Stop và xóa volumes
docker compose down -v
```

### Update code

```bash
# Cấu hình Git (chỉ cần làm 1 lần)
git config pull.rebase false
git config core.editor "nano"  # Tránh vim swap file issues

# Pull code mới
git pull origin main --no-edit

# Hoặc sử dụng script tự động (khuyến nghị)
chmod +x scripts/fix_git_pull.sh
./scripts/fix_git_pull.sh

# Rebuild và restart
docker compose build
docker compose up -d
```

**Lưu ý**:

- Nếu gặp lỗi "divergent branches", xem hướng dẫn trong `docs/GIT_PULL_ON_VPS.md`
- Nếu gặp vim swap file error, chạy: `./scripts/fix_vim_swap.sh`

## 🔍 Troubleshooting

### Permission Denied - Script không chạy được

**Lỗi**: `bash: ./scripts/deploy_vps.sh: Permission denied`

**Giải pháp**:

```bash
# Cấp quyền thực thi cho script
chmod +x scripts/deploy_vps.sh
chmod +x scripts/download_dataset.sh

# Sau đó chạy lại
./scripts/deploy_vps.sh
```

### Permission Denied - Docker commands

**Lỗi**: `permission denied while trying to connect to the Docker daemon socket`

**Giải pháp 1: Thêm user vào docker group (Khuyến nghị)**

```bash
# Thêm user hiện tại vào docker group
sudo usermod -aG docker $USER

# Logout và login lại để áp dụng thay đổi
# Hoặc chạy lệnh sau để áp dụng ngay (không cần logout)
newgrp docker

# Kiểm tra
docker ps
```

**Giải pháp 2: Sử dụng sudo (tạm thời)**

```bash
# Chạy với sudo
sudo docker compose up -d
sudo docker compose ps

# Lưu ý: Có thể gây vấn đề với file permissions
```

**Giải pháp 3: Fix Docker socket permissions**

```bash
# Kiểm tra permissions của Docker socket
ls -l /var/run/docker.sock

# Fix permissions (nếu cần)
sudo chmod 666 /var/run/docker.sock
# Hoặc tốt hơn: thêm user vào docker group (giải pháp 1)
```

### Permission Denied - File/Directory access

**Lỗi**: `Permission denied` khi truy cập files

**Giải pháp**:

```bash
# Kiểm tra ownership
ls -la

# Thay đổi ownership nếu cần (thay USERNAME bằng user của bạn)
sudo chown -R $USER:$USER .

# Hoặc cấp quyền đọc/ghi
chmod -R 755 .
```

### Permission Denied - Kaggle credentials

**Lỗi**: `Permission denied` khi download dataset

**Giải pháp**:

```bash
# Set proper permissions cho kaggle.json
chmod 600 ~/.kaggle/kaggle.json

# Kiểm tra file tồn tại
ls -la ~/.kaggle/kaggle.json
```

### Service không start

```bash
# Kiểm tra logs
docker compose logs [service_name]

# Kiểm tra ports
sudo netstat -tuln | grep [port_number]
```

### Out of memory

```bash
# Kiểm tra memory usage
free -h
docker stats

# Giảm số lượng services nếu cần
# Hoặc tăng RAM cho VPS
```

### Port đã được sử dụng

```bash
# Tìm process đang dùng port
sudo lsof -i :8000

# Kill process (cẩn thận!)
sudo kill -9 [PID]
```

### Dataset không tìm thấy

```bash
# Kiểm tra đường dẫn
ls -la src/data/

# Download lại dataset nếu cần
```

### MinIO Bucket không tồn tại (NoSuchBucket)

**Lỗi**: `An error occurred (NoSuchBucket) when calling the PutObject operation`

**Nguyên nhân**: Bucket `mlflow-artifacts` chưa được tạo trong MinIO.

**Giải pháp**:

```bash
# Cách 1: Sử dụng script tự động (Khuyến nghị)
chmod +x scripts/create_minio_bucket.sh
./scripts/create_minio_bucket.sh

# Cách 2: Tạo bucket thủ công
docker compose exec minio mc alias set local http://localhost:9000 minioadmin minioadmin
docker compose exec minio mc mb local/mlflow-artifacts

# Cách 3: Tạo qua MinIO Console
# 1. Mở http://YOUR_VPS_IP:9001
# 2. Login với minioadmin/minioadmin
# 3. Click "Create Bucket"
# 4. Đặt tên: mlflow-artifacts
# 5. Click "Create Bucket"

# Kiểm tra bucket đã tạo
docker compose exec minio mc ls local
```

## 📡 Access URLs sau khi deploy

Sau khi deploy thành công, truy cập các services:

| Service       | URL                            | Credentials           |
| ------------- | ------------------------------ | --------------------- |
| FastAPI API   | `http://YOUR_VPS_IP:8000`      | -                     |
| FastAPI Docs  | `http://YOUR_VPS_IP:8000/docs` | -                     |
| MLflow UI     | `http://YOUR_VPS_IP:5000`      | -                     |
| Grafana       | `http://YOUR_VPS_IP:3000`      | admin/admin           |
| Prometheus    | `http://YOUR_VPS_IP:9090`      | -                     |
| MinIO Console | `http://YOUR_VPS_IP:9001`      | minioadmin/minioadmin |

## 🔐 Bảo mật (Quan trọng)

### 1. Thay đổi passwords mặc định

- **Grafana**: Đổi password admin sau lần đăng nhập đầu tiên
- **MinIO**: Thay đổi `MINIO_ROOT_USER` và `MINIO_ROOT_PASSWORD` trong `docker-compose.yml`

### 2. Sử dụng HTTPS

Cấu hình SSL/TLS certificate (Let's Encrypt) cho Nginx nếu expose ra internet.

### 3. Firewall

Chỉ mở các ports cần thiết:

```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp     # HTTP (nếu dùng Nginx)
sudo ufw allow 443/tcp    # HTTPS
sudo ufw enable
```

### 4. Không expose tất cả ports

Chỉ expose các ports cần thiết ra internet. Các services internal (Kafka, Zookeeper) không cần expose.

## 📚 Tài liệu tham khảo

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [MLflow Documentation](https://www.mlflow.org/docs/latest/index.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## 💡 Tips

1. **Monitor resources**: Sử dụng `docker stats` để theo dõi resource usage
2. **Backup data**: Backup thư mục `mlflow/` và volumes quan trọng
3. **Log rotation**: Cấu hình log rotation cho Docker logs
4. **Auto-restart**: Sử dụng `restart: unless-stopped` trong docker-compose.yml cho production

## 🆘 Hỗ trợ

Nếu gặp vấn đề, kiểm tra:

1. Logs của services: `docker compose logs`
2. System resources: `htop`, `df -h`, `free -h`
3. Network connectivity: `ping`, `curl`
4. Docker daemon: `docker info`
