# 🚀 Push to GitHub - Step by Step Guide

## ⚠️ IMPORTANT: Before You Start

1. **Verify `.env` is NOT tracked:**
   ```bash
   cat .gitignore | grep .env
   ```
   Should show `.env` in the list.

2. **Remove any committed secrets:**
   - Check that your `.env` file has no real tokens
   - We already have `.env.example` as the template

## 📋 Step-by-Step Instructions

### Step 1: Initialize Git (if not already done)

```bash
cd "c:\Projects\POC\Debugger Agent"
git init
```

### Step 2: Configure Git (first time only)

```bash
git config user.name "Your Name"
git config user.email "your-email@example.com"
```

### Step 3: Add All Files

```bash
git add .
```

### Step 4: Verify What Will Be Committed

```bash
git status
```

**✅ Should see:**
- `.gitignore`
- `.env.example`
- `README.md`
- `requirements.txt`
- `agent/*.py`
- `SETUP.md`

**❌ Should NOT see:**
- `.env` (this should be ignored)
- `venv/` (this should be ignored)
- `__pycache__/` (this should be ignored)

### Step 5: Create Initial Commit

```bash
git commit -m "Initial commit: FREE Debug Agent POC"
```

### Step 6: Create GitHub Repository

**Option A: Via GitHub Web UI**
1. Go to https://github.com/new
2. Name: `debugger-agent` or `free-debug-agent`
3. Description: "AI-powered bug investigation agent using Claude, Jira, and GitHub"
4. Set as **Public** or **Private**
5. ⚠️ **DO NOT** initialize with README, .gitignore, or license
6. Click "Create repository"

**Option B: Via GitHub CLI** (if installed)
```bash
gh repo create debugger-agent --public --source=. --remote=origin
```

### Step 7: Add Remote and Push

```bash
# Add remote (replace YOUR-USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR-USERNAME/debugger-agent.git

# Verify remote
git remote -v

# Push to GitHub
git branch -M main
git push -u origin main
```

### Step 8: Verify on GitHub

1. Go to your repository on GitHub
2. **Check that `.env` is NOT visible** ✅
3. Check that `.env.example` IS visible ✅
4. Check that `README.md` displays properly ✅

## 🔄 Future Updates

### To push new changes:

```bash
# Check what changed
git status

# Add specific files
git add file1.py file2.py

# Or add all changes
git add .

# Commit with message
git commit -m "Description of changes"

# Push to GitHub
git push
```

## 🚨 Emergency: Remove Accidentally Committed Secrets

If you accidentally committed secrets:

```bash
# Remove from last commit (not yet pushed)
git reset --soft HEAD~1

# Remove specific file from tracking
git rm --cached agent/.env

# Commit the removal
git commit -m "Remove .env from tracking"

# Force push (if already pushed)
git push -f origin main
```

**Then immediately:**
1. Rotate all exposed API keys/tokens
2. Update `.env` with new tokens
3. Verify `.gitignore` includes `.env`

## ✅ Checklist Before Push

- [ ] `.gitignore` file exists and includes `.env`
- [ ] `.env.example` exists with placeholder values
- [ ] `.env` file has NO real tokens (all removed)
- [ ] `README.md` is complete and helpful
- [ ] All Python files are included
- [ ] `requirements.txt` is up to date
- [ ] Ran `git status` and verified no sensitive files
- [ ] Tested the code works after removing tokens

## 🎉 Success!

Your code is now safely on GitHub without any secrets! 🚀

Share the repository: `https://github.com/YOUR-USERNAME/debugger-agent`
