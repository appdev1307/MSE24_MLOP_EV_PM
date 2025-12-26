#!/bin/bash

# Script để fix các vấn đề khi pull code trên VPS
# Sử dụng: ./scripts/fix_git_pull.sh

set -e

echo "🔧 Fixing Git pull configuration..."

# Cấu hình Git để merge khi pull (thay vì rebase)
echo "📝 Configuring Git pull strategy..."
git config pull.rebase false

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

# Pull code
echo ""
echo "🔄 Pulling latest code from origin/main..."
git pull origin main

echo ""
echo "✅ Done! Code updated successfully."

# Nếu đã stash, thông báo
if [ -n "$(git stash list)" ]; then
    echo ""
    echo "💡 Note: You have stashed changes. To restore them:"
    echo "   git stash pop"
fi

