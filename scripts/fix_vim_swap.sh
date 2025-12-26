#!/bin/bash

# Script để fix vim swap file issues khi Git merge
# Sử dụng: ./scripts/fix_vim_swap.sh

set -e

echo "🔧 Fixing vim swap file issues..."

# Tìm và xóa swap files
echo "🧹 Cleaning up vim swap files..."
SWAP_FILES=$(find .git -name "*.swp" -o -name ".*.swp" 2>/dev/null || true)

if [ -n "$SWAP_FILES" ]; then
    echo "Found swap files:"
    echo "$SWAP_FILES"
    echo ""
    read -p "Delete these swap files? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        find .git -name "*.swp" -type f -delete 2>/dev/null || true
        find .git -name ".*.swp" -type f -delete 2>/dev/null || true
        echo "✅ Swap files deleted"
    fi
else
    echo "✅ No swap files found"
fi

# Kiểm tra xem có vim process đang chạy không
echo ""
echo "🔍 Checking for running vim processes..."
VIM_PIDS=$(ps aux | grep -E '[v]im.*MERGE_MSG' | awk '{print $2}' || true)

if [ -n "$VIM_PIDS" ]; then
    echo "Found vim processes: $VIM_PIDS"
    echo ""
    read -p "Kill these vim processes? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "$VIM_PIDS" | xargs kill -9 2>/dev/null || true
        echo "✅ Vim processes killed"
    fi
else
    echo "✅ No vim processes found"
fi

# Cấu hình Git editor
echo ""
echo "📝 Configuring Git editor..."
if command -v nano &> /dev/null; then
    git config core.editor "nano"
    echo "✅ Git editor set to 'nano'"
elif command -v vi &> /dev/null; then
    git config core.editor "vi"
    echo "✅ Git editor set to 'vi'"
else
    echo "⚠️  No suitable editor found. Using default."
fi

# Cấu hình để không mở editor khi merge (nếu muốn)
echo ""
read -p "Configure Git to skip editor for merge commits? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git config core.mergeoptions "--no-edit"
    echo "✅ Git configured to skip editor for merges"
fi

echo ""
echo "✅ Done! You can now try 'git pull origin main' again."

