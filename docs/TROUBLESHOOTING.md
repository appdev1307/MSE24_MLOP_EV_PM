# Troubleshooting Guide - MLOps EV Predictive Maintenance

Hướng dẫn xử lý các lỗi thường gặp khi deploy và chạy dự án.

## 🔴 Permission Denied Errors

### 1. Script không chạy được

**Lỗi**:
```bash
bash: ./scripts/deploy_vps.sh: Permission denied
```

**Nguyên nhân**: Script không có quyền thực thi.

**Giải pháp**:
```bash
chmod +x scripts/deploy_vps.sh
chmod +x scripts/download_dataset.sh
./scripts/deploy_vps.sh
```

---

### 2. Docker Permission Denied

**Lỗi**:
```bash
permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock
```

**Nguyên nhân**: User không có quyền truy cập Docker socket.

**Giải pháp 1: Thêm user vào docker group (Khuyến nghị)**

```bash
# Thêm user vào docker group
sudo usermod -aG docker $USER

# Áp dụng thay đổi ngay (không cần logout)
newgrp docker

# Kiểm tra
docker ps
```

**Giải pháp 2: Sử dụng sudo (tạm thời)**

```bash
sudo docker compose up -d
```

⚠️ **Lưu ý**: Sử dụng sudo có thể gây vấn đề với file permissions. Nên dùng giải pháp 1.

**Giải pháp 3: Fix Docker socket permissions**

```bash
# Chỉ nên dùng trong trường hợp đặc biệt
sudo chmod 666 /var/run/docker.sock
```

---

### 3. File/Directory Permission Denied

**Lỗi**: Không thể đọc/ghi files trong project directory.

**Giải pháp**:
```bash
# Kiểm tra ownership
ls -la

# Thay đổi ownership về user hiện tại
sudo chown -R $USER:$USER .

# Cấp quyền đọc/ghi
chmod -R 755 .
```

---

### 4. Kaggle Credentials Permission Denied

**Lỗi**: Không thể download dataset từ Kaggle.

**Giải pháp**:
```bash
# Set permissions cho kaggle.json
chmod 600 ~/.kaggle/kaggle.json

# Kiểm tra file tồn tại
ls -la ~/.kaggle/kaggle.json

# Nếu chưa có, tạo từ Kaggle API token
# 1. Vào https://www.kaggle.com/settings
# 2. Create API token
# 3. Lưu vào ~/.kaggle/kaggle.json
```

---

## 🟡 Service Issues

### 1. Service không start

**Kiểm tra**:
```bash
# Xem logs
docker compose logs [service_name]

# Xem status
docker compose ps

# Xem logs real-time
docker compose logs -f [service_name]
```

**Giải pháp thường gặp**:
- Port đã được sử dụng → Xem phần "Port Issues"
- Out of memory → Xem phần "Resource Issues"
- Config sai → Kiểm tra docker-compose.yml

---

### 2. Service crash/restart liên tục

**Kiểm tra**:
```bash
# Xem logs để tìm lỗi
docker compose logs [service_name] | tail -50

# Kiểm tra resource usage
docker stats
```

**Giải pháp**:
- Kiểm tra logs để tìm nguyên nhân
- Kiểm tra memory/CPU usage
- Kiểm tra config files

---

## 🔵 Port Issues

### Port đã được sử dụng

**Lỗi**:
```bash
Error: bind: address already in use
```

**Tìm process đang dùng port**:
```bash
# Tìm process
sudo lsof -i :8000
# Hoặc
sudo netstat -tuln | grep 8000

# Kill process (cẩn thận!)
sudo kill -9 [PID]
```

**Hoặc đổi port trong docker-compose.yml**:
```yaml
ports:
  - '8001:8000'  # Thay vì 8000:8000
```

---

## 🟢 Resource Issues

### Out of Memory

**Kiểm tra**:
```bash
# Memory usage
free -h

# Docker stats
docker stats

# Disk space
df -h
```

**Giải pháp**:
- Tăng RAM cho VPS
- Giảm số lượng services chạy đồng thời
- Tối ưu Docker images
- Clean up unused Docker resources:
  ```bash
  docker system prune -a
  ```

---

### Disk Space Full

**Kiểm tra**:
```bash
df -h
docker system df
```

**Giải pháp**:
```bash
# Clean up Docker
docker system prune -a

# Remove unused volumes
docker volume prune

# Remove old images
docker image prune -a
```

---

## 🟣 Network Issues

### Không thể truy cập services từ bên ngoài

**Kiểm tra**:
```bash
# Firewall status
sudo ufw status

# Ports đang listen
sudo netstat -tuln
```

**Giải pháp**:
```bash
# Mở ports trong firewall
sudo ufw allow 8000/tcp
sudo ufw allow 5000/tcp
sudo ufw allow 3000/tcp
sudo ufw allow 9090/tcp

# Reload firewall
sudo ufw reload
```

---

### Services không kết nối được với nhau

**Kiểm tra**:
- Tất cả services đều trong cùng Docker network (tự động với docker-compose)
- Service names trong docker-compose.yml đúng
- Environment variables đúng

**Giải pháp**:
```bash
# Kiểm tra network
docker network ls
docker network inspect [network_name]

# Restart services
docker compose restart
```

---

## 🔴 Dataset Issues

### Dataset không tìm thấy

**Lỗi**: `FileNotFoundError: src/data/EV_Predictive_Maintenance_Dataset_15min.csv`

**Kiểm tra**:
```bash
ls -la src/data/
```

**Giải pháp**:
```bash
# Download dataset
chmod +x scripts/download_dataset.sh
./scripts/download_dataset.sh

# Hoặc download thủ công từ Kaggle
# Và đặt vào src/data/EV_Predictive_Maintenance_Dataset_15min.csv
```

---

### Dataset format sai

**Kiểm tra**:
```bash
# Xem header của file
head -1 src/data/EV_Predictive_Maintenance_Dataset_15min.csv
```

**Giải pháp**: Đảm bảo file CSV có đúng format và encoding UTF-8.

---

## 🟡 MLflow Issues

### MLflow không kết nối được với MinIO

**Lỗi**: `Connection refused` hoặc `Access Denied`

**Kiểm tra**:
```bash
# MinIO đang chạy
docker compose ps minio

# MinIO logs
docker compose logs minio

# Test connection
curl http://localhost:9000
```

**Giải pháp**:
- Kiểm tra environment variables trong docker-compose.yml
- Đảm bảo MinIO đã start trước MLflow
- Kiểm tra credentials (minioadmin/minioadmin)

---

### MinIO Bucket không tồn tại (NoSuchBucket)

**Lỗi**: 
```
An error occurred (NoSuchBucket) when calling the PutObject operation: 
The specified bucket does not exist
```

**Nguyên nhân**: Bucket `mlflow-artifacts` chưa được tạo trong MinIO.

**Giải pháp 1: Sử dụng script tự động (Khuyến nghị)**

```bash
chmod +x scripts/create_minio_bucket.sh
./scripts/create_minio_bucket.sh
```

**Giải pháp 2: Tạo bucket thủ công qua CLI**

```bash
# Đảm bảo MinIO đang chạy
docker compose up -d minio
sleep 5

# Set alias
docker compose exec minio mc alias set local http://localhost:9000 minioadmin minioadmin

# Tạo bucket
docker compose exec minio mc mb local/mlflow-artifacts

# Kiểm tra
docker compose exec minio mc ls local
```

**Giải pháp 3: Tạo qua MinIO Console**

1. Mở browser: `http://YOUR_VPS_IP:9001`
2. Login với `minioadmin` / `minioadmin`
3. Click "Create Bucket"
4. Đặt tên: `mlflow-artifacts`
5. Click "Create Bucket"

**Kiểm tra bucket đã tạo**:
```bash
docker compose exec minio mc ls local
```

Bạn sẽ thấy `mlflow-artifacts` trong danh sách.

---

### Models không load được từ Registry

**Lỗi**: `Failed to load model from MLflow Registry`

**Kiểm tra**:
```bash
# MLflow UI
# http://localhost:5000

# Kiểm tra models đã được register chưa
# Xem trong Model Registry tab
```

**Giải pháp**:
- Train models trước: `docker compose run --rm trainer`
- Kiểm tra model stage (Production/Staging)
- Kiểm tra MLFLOW_MODEL_STAGE environment variable

---

## 🟢 Training Issues

### Training failed

**Kiểm tra logs**:
```bash
docker compose logs trainer
```

**Nguyên nhân thường gặp**:
- Dataset không tìm thấy
- Out of memory
- Dependencies thiếu

**Giải pháp**:
- Kiểm tra dataset
- Tăng memory cho container
- Rebuild image: `docker compose build trainer`

---

## 📞 Getting Help

Nếu vẫn gặp vấn đề:

1. **Kiểm tra logs**: `docker compose logs -f`
2. **Kiểm tra system resources**: `htop`, `df -h`, `free -h`
3. **Kiểm tra Docker**: `docker info`, `docker ps -a`
4. **Xem documentation**: `docs/DEPLOY_VPS.md`
5. **Check GitHub Issues**: Tạo issue mới nếu cần

---

## 💡 Quick Fixes

### Reset toàn bộ (Cẩn thận - sẽ xóa data!)

```bash
# Stop và xóa tất cả
docker compose down -v

# Clean up Docker
docker system prune -a

# Rebuild và start lại
docker compose build
docker compose up -d
```

### Restart tất cả services

```bash
docker compose restart
```

### Xem tất cả logs

```bash
docker compose logs -f
```

