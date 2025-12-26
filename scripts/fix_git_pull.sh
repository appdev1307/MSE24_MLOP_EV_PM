#!/bin/bash

# Script để fix các vấn đề khi pull code trên VPS
# Sử dụng: ./scripts/fix_git_pull.sh

set -e

echo "🔧 Fixing Git pull configuration..."

# Cấu hình Git để merge khi pull (thay vì rebase)
echo "📝 Configuring Git pull strategy..."
git config pull.rebase false

# Cấu hình Git editor để tránh vim swap file issues
# Sử dụng nano thay vì vim (dễ dùng hơn trên VPS)
if ! git config --get core.editor > /dev/null 2>&1; then
    echo "📝 Configuring Git editor to nano..."
    git config core.editor "nano"
    echo "✅ Git editor configured to 'nano'"
fi

# Hoặc chỉ cho repo này
# git config --local pull.rebase false

echo "✅ Git pull strategy configured to 'merge'"

# Kiểm tra xem có local changes không
if [ -n "$(git status --porcelain)" ]; then
    echo ""
    echo "⚠️  Warning: You have local changes"
    echo "   Files changed:"
    git status --short
    
    echo ""
    read -p "Do you want to stash local changes? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "📦 Stashing local changes..."
        git stash
        echo "✅ Local changes stashed"
    else
        echo "⚠️  Keeping local changes. You may need to resolve conflicts manually."
    fi
fi

# Kiểm tra và fix unfinished merge
if [ -f .git/MERGE_HEAD ]; then
    echo ""
    echo "⚠️  Found unfinished merge. Aborting..."
    git merge --abort 2>/dev/null || true
    echo "✅ Unfinished merge aborted"
fi

# Clean up any vim swap files that might cause issues
echo ""
echo "🧹 Cleaning up any vim swap files..."
find .git -name "*.swp" -type f -delete 2>/dev/null || true
find .git -name ".*.swp" -type f -delete 2>/dev/null || true

# Clean up merge state files
echo "🧹 Cleaning up merge state files..."
rm -f .git/MERGE_HEAD 2>/dev/null || true
rm -f .git/CHERRY_PICK_HEAD 2>/dev/null || true
rm -f .git/REBASE_HEAD 2>/dev/null || true
rm -f .git/MERGE_MSG 2>/dev/null || true

# Pull code (sử dụng --no-edit để tránh mở editor)
echo ""
echo "🔄 Pulling latest code from origin/main..."
git pull origin main --no-edit 2>/dev/null || git pull origin main

echo ""
echo "✅ Done! Code updated successfully."

# Nếu đã stash, thông báo
if [ -n "$(git stash list)" ]; then
    echo ""
    echo "💡 Note: You have stashed changes. To restore them:"
    echo "   git stash pop"
fi

