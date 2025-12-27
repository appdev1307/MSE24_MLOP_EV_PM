#!/bin/bash

# Script để fix lỗi "unfinished merge" khi pull code trên VPS
# Sử dụng: ./scripts/fix_unfinished_merge.sh

set -e

echo "🔧 Fixing unfinished merge..."

# Kiểm tra xem có MERGE_HEAD không
if [ -f .git/MERGE_HEAD ]; then
    echo "⚠️  Found unfinished merge (MERGE_HEAD exists)"
    echo ""
    
    # Hiển thị trạng thái
    echo "📊 Current status:"
    git status --short
    
    echo ""
    echo "Options:"
    echo "1. Abort merge (discard merge, keep your changes)"
    echo "2. Complete merge (commit the merge)"
    echo "3. Reset to remote (discard all local changes)"
    echo ""
    read -p "Choose option (1/2/3): " -n 1 -r
    echo
    
    case $REPLY in
        1)
            echo "🔄 Aborting merge..."
            git merge --abort
            echo "✅ Merge aborted"
            echo ""
            echo "💡 You can now try: git pull origin main"
            ;;
        2)
            echo "📝 Completing merge..."
            
            # Kiểm tra xem có conflicts không
            if [ -n "$(git diff --name-only --diff-filter=U)" ]; then
                echo "⚠️  There are merge conflicts that need to be resolved:"
                git diff --name-only --diff-filter=U
                echo ""
                echo "Please resolve conflicts manually, then run:"
                echo "  git add ."
                echo "  git commit"
            else
                # Tự động commit merge
                git commit --no-edit || git commit -m "Merge branch 'main' of origin into local"
                echo "✅ Merge completed"
            fi
            ;;
        3)
            echo "⚠️  WARNING: This will discard all local changes!"
            read -p "Are you sure? (yes/no): " -r
            echo
            if [[ $REPLY == "yes" ]]; then
                echo "🔄 Resetting to remote..."
                git merge --abort 2>/dev/null || true
                git reset --hard origin/main
                echo "✅ Reset to remote completed"
            else
                echo "❌ Cancelled"
                exit 1
            fi
            ;;
        *)
            echo "❌ Invalid option"
            exit 1
            ;;
    esac
else
    echo "✅ No unfinished merge found"
    
    # Kiểm tra các file merge khác
    if [ -f .git/CHERRY_PICK_HEAD ]; then
        echo "⚠️  Found unfinished cherry-pick"
        read -p "Abort cherry-pick? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git cherry-pick --abort
            echo "✅ Cherry-pick aborted"
        fi
    fi
    
    if [ -f .git/REBASE_HEAD ]; then
        echo "⚠️  Found unfinished rebase"
        read -p "Abort rebase? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git rebase --abort
            echo "✅ Rebase aborted"
        fi
    fi
fi

# Clean up any swap files
echo ""
echo "🧹 Cleaning up swap files..."
find .git -name "*.swp" -type f -delete 2>/dev/null || true
find .git -name ".*.swp" -type f -delete 2>/dev/null || true

echo ""
echo "✅ Done!"

