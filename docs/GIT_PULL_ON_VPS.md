# Hướng dẫn Pull Code trên VPS không cần đăng nhập Git

Nếu bạn gặp lỗi khi pull code trên VPS do có local changes, hãy làm theo các bước sau:

## 🔍 Vấn đề thường gặp

### 1. Divergent branches

Khi pull code trên VPS, bạn có thể gặp lỗi:
```
hint: You have divergent branches and need to specify how to reconcile them.
fatal: Need to specify how to reconcile divergent branches.
```

**Giải pháp nhanh**:
```bash
# Cấu hình Git để merge khi pull (khuyến nghị)
git config pull.rebase false

# Hoặc chỉ cho repo này
git config --local pull.rebase false

# Sau đó pull lại
git pull origin main
```

### 2. Local changes conflict

```
error: Your local changes to the following files would be overwritten by merge
```

Hoặc Git yêu cầu commit/push trước khi pull.

## ✅ Giải pháp

### Cách 1: Stash local changes (Khuyến nghị)

Nếu có thay đổi local không quan trọng:

```bash
# Lưu tạm thời các thay đổi
git stash

# Pull code mới
git pull origin main

# Nếu cần khôi phục thay đổi (thường không cần)
# git stash pop
```

### Cách 2: Reset local changes (Nếu không cần giữ thay đổi)

```bash
# Xem các file bị thay đổi
git status

# Discard tất cả thay đổi local
git reset --hard HEAD

# Pull code mới
git pull origin main
```

### Cách 3: Xóa các file được generate (models, data, mlflow)

Các file này sẽ được tạo lại khi chạy training:

```bash
# Xóa các file/folder được ignore (sẽ được tạo lại)
rm -rf models/
rm -rf data/features_with_anomaly.parquet
rm -rf mlflow/mlflow.db
rm -rf src/__pycache__/
rm -rf **/__pycache__/

# Pull code mới
git pull origin main
```

### Cách 4: Force pull (Cẩn thận - sẽ mất local changes)

```bash
# Backup nếu cần
cp -r models/ models_backup/ 2>/dev/null || true

# Fetch và reset về remote
git fetch origin
git reset --hard origin/main

# Pull lại
git pull origin main
```

## 🛡️ Prevent vấn đề trong tương lai

### Đảm bảo .gitignore đã được cập nhật

File `.gitignore` đã được cập nhật để ignore:
- `models/` - Model files
- `data/` - Data files (trừ dataset source)
- `mlflow/` - MLflow database
- `__pycache__/` - Python cache
- `*.pyc`, `*.pyo` - Compiled Python files
- `*.parquet`, `*.joblib`, `*.pkl` - Generated data files
- `*.log` - Log files
- `.env` - Environment files

### Kiểm tra trạng thái trước khi pull

```bash
# Xem các file đang bị thay đổi
git status

# Nếu chỉ có các file trong .gitignore, bạn có thể pull an toàn
git pull origin main
```

### Sử dụng script helper (Khuyến nghị)

Script `fix_git_pull.sh` đã được tạo sẵn:

```bash
# Cấp quyền
chmod +x scripts/fix_git_pull.sh

# Chạy script
./scripts/fix_git_pull.sh
```

Script này sẽ:
- ✅ Cấu hình Git pull strategy
- ✅ Tự động stash local changes nếu cần
- ✅ Pull code mới nhất
- ✅ Hướng dẫn restore stashed changes nếu có

## 📝 Files có thể gây conflict

Nếu vẫn gặp vấn đề với các file sau, chúng đã được track trong Git:

- `src/data/EV_Predictive_Maintenance_Dataset_15min.csv` - Dataset file (nên giữ trong repo)
- `src/__pycache__/*.pyc` - Cache files (có thể xóa)

Để remove cache files khỏi Git tracking (nhưng giữ lại local):

```bash
# Remove từ Git index nhưng giữ file local
git rm -r --cached src/__pycache__/

# Commit thay đổi
git commit -m "Remove __pycache__ from Git tracking"

# Push (cần đăng nhập Git một lần để push)
git push origin main
```

## 💡 Best Practices

1. **Luôn kiểm tra trước khi pull**:
   ```bash
   git status
   ```

2. **Stash thay đổi không quan trọng**:
   ```bash
   git stash
   git pull origin main
   ```

3. **Không commit files được ignore**:
   - Models, data, cache files sẽ được tạo lại khi chạy training
   - Không cần commit chúng

4. **Sử dụng separate branches cho development và production**:
   - Develop trên local
   - Pull main trên VPS (production)

## 🆘 Nếu vẫn gặp vấn đề

1. Kiểm tra `.gitignore` đã được cập nhật chưa
2. Kiểm tra file nào đang gây conflict: `git status`
3. Backup files quan trọng trước khi reset
4. Xem logs: `git log --oneline -5`

