#!/bin/bash
# ================================
# Termux GitHub → Render deploy script
# ================================

# 1️⃣ Go to bot repo
cd ~/mlbb-bot || exit

# 2️⃣ Clean unnecessary files
echo "✅ Cleaning cache / temp files..."
rm -rf __pycache__ *.pyc *.log *.sqlite *.db node_modules/ .DS_Store Thumbs.db .env

# 3️⃣ Ensure .gitignore exists
cat > .gitignore <<EOL
# Python
__pycache__/
*.pyc

# Logs / DB
*.log
*.sqlite
*.db

# Node / JS
node_modules/

# OS / Editor
.DS_Store
Thumbs.db

# Env
.env
EOL

# 4️⃣ Add main files to commit
git add ml.py requirements.txt start.sh .gitignore

# 5️⃣ Commit changes
git commit -m "Update bot code for Render deploy" 2>/dev/null || echo "No changes to commit"

# 6️⃣ Ensure main branch
git checkout -b main 2>/dev/null || echo "Main branch exists, continuing..."

# 7️⃣ Set SSH remote (replace with your GitHub SSH URL)
git remote set-url origin git@github.com:htetaungthuya/mlbb-cloud-run.git
git remote -v

# 8️⃣ Force push to GitHub (overwrite old content)
git push -u origin main --force

echo "✅ Selected files pushed to GitHub."
echo "Next: Render will auto deploy based on your main branch."
echo "Check Render dashboard for logs / live bot status."
