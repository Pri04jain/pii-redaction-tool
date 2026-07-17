# 🔄 Git Workflow Guide

**Project**: PII Redaction Tool  
**Repository**: [Add URL after GitHub push]

---

## 📝 Commit History

### Commit 1: Initial Setup ✅
```
Commit: 19c521e
Message: chore: initialize project with configuration and documentation
Date: 2026-07-17
Files: 33 files, 6320 insertions
```

**Includes**:
- Project structure (src/, tests/, docs/)
- All 4 redactor implementations (Regex, NER, Presidio, Hybrid)
- Utility modules (document_handler, fake_data_generator, evaluator, pii_patterns)
- Web interface (Flask app + HTML template)
- CLI interface
- Configuration files (.gitignore, .env.example, requirements.txt)
- Documentation (README, TASKS, NEXT_STEPS, implementation docs)
- Deployment config (Procfile, runtime.txt)

---

## 🎯 Upcoming Commits

### Next Commits (Pending)

#### Commit 2: Test Data Preparation
```bash
# After splitting documents and creating annotations
git add tests/test_data/*.docx tests/ground_truth/*.json
git commit -m "test: add split test documents and ground truth annotations"
```

#### Commit 3: POC Evaluation
```bash
# After creating and running evaluation script
git add src/poc_evaluation.py evaluation/
git commit -m "feat(evaluation): add POC evaluation script and results"
```

#### Commit 4: Analysis Report
```bash
# After completing analysis
git add evaluation/poc_comparison_report.md
git commit -m "docs: add POC analysis and approach recommendation"
```

---

## 🚀 Git Commands Reference

### Daily Workflow

```bash
# 1. Check status
git status

# 2. Stage files
git add <files>
# or stage all changes
git add .

# 3. Commit with message
git commit -m "type(scope): description"

# 4. View commit history
git log --oneline

# 5. Push to GitHub (after setting up remote)
git push origin main
```

### Useful Commands

```bash
# View last commit
git show HEAD

# Undo last commit (keep changes)
git reset --soft HEAD~1

# View diff before committing
git diff

# View staged diff
git diff --cached

# Amend last commit (if not pushed yet)
git commit --amend -m "new message"
```

---

## 📋 Commit Message Conventions

We follow [Conventional Commits](https://www.conventionalcommits.org/):

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `test`: Adding/updating tests
- `refactor`: Code restructuring
- `perf`: Performance improvement
- `style`: Code style/formatting
- `chore`: Build/config changes

### Scopes (Optional)
- `redactor`: Redactor implementations
- `utils`: Utility modules
- `evaluation`: Evaluation framework
- `web`: Web interface
- `cli`: CLI interface

### Examples

```bash
# Good commits
git commit -m "feat(redactor): implement regex-based PII detection"
git commit -m "test: add ground truth annotations for evaluation"
git commit -m "docs: add POC evaluation results"
git commit -m "fix(web): handle large file uploads correctly"
git commit -m "perf(redactor): optimize entity merging in hybrid mode"

# Avoid
git commit -m "update"
git commit -m "fixes"
git commit -m "changes"
```

---

## 🌿 Branch Strategy

For this project (solo development), we'll use a simple workflow:

```
main (stable, deployable code)
```

### For Team Projects (Future)
```
main
  ├── develop (integration)
  │   ├── feature/regex-redactor
  │   ├── feature/web-interface
  │   └── feature/evaluation
  └── hotfix/critical-bug
```

---

## 📤 GitHub Setup

### Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `pii-redaction-tool`
3. Description: "PII Redaction Tool with multiple detection approaches"
4. Visibility: Private (for assignment) or Public (after submission)
5. **Don't** initialize with README (we have one)
6. Click "Create repository"

### Step 2: Connect Local to GitHub

```bash
cd "d:\PII Redaction Tool"

# Add remote
git remote add origin https://github.com/YOUR_USERNAME/pii-redaction-tool.git

# Verify remote
git remote -v

# Push to GitHub
git branch -M main
git push -u origin main
```

### Step 3: Verify

```bash
# Check remote branches
git branch -r

# View all branches
git branch -a
```

---

## 🔐 .gitignore Rules

Our `.gitignore` excludes:

✅ **Excluded** (Not in repo):
- Assignment files (REQUIREMENTS.md, Enterprise Data - Assignment.txt)
- Source documents (Red Herring Prospectus.docx)
- Virtual environment (venv/)
- Python cache (__pycache__/)
- Environment variables (.env)
- Test data (tests/test_data/*.docx)
- Output files (output/, uploads/, downloads/)
- Evaluation results (evaluation/*.json, *.png)

✅ **Included** (In repo):
- Source code (src/)
- Documentation (*.md)
- Configuration (.gitignore, requirements.txt)
- Templates (templates/)
- Tests (test_*.py)
- Deployment config (Procfile, runtime.txt)

---

## 📊 Repository Statistics

After initial commit:
- **Files tracked**: 33
- **Lines of code**: 6,320+
- **Commits**: 1
- **Branches**: 1 (main)

---

## 🎯 Commit Checklist

Before each commit:

- [ ] Code runs without errors
- [ ] No sensitive data (passwords, API keys)
- [ ] Files follow .gitignore rules
- [ ] Commit message follows convention
- [ ] Changes are related and atomic
- [ ] TASKS.md updated if applicable

---

## 🆘 Common Issues

### Issue: Large files rejected
```bash
# Check file sizes
git ls-files --size

# Remove large file from staging
git reset HEAD path/to/large/file

# Add to .gitignore
echo "large-file.docx" >> .gitignore
```

### Issue: Accidentally committed sensitive data
```bash
# Remove from last commit (if not pushed)
git rm --cached sensitive-file.txt
git commit --amend --no-edit

# If already pushed, contact GitHub support
```

### Issue: Merge conflicts
```bash
# View conflicts
git status

# Edit conflicted files, then:
git add conflicted-file.py
git commit -m "fix: resolve merge conflicts"
```

---

## 📈 Progress Tracking

| Date | Commit | Description | Files | Lines |
|------|--------|-------------|-------|-------|
| 2026-07-17 | 19c521e | Initial project setup | 33 | +6,320 |
| TBD | - | Test data preparation | TBD | TBD |
| TBD | - | POC evaluation | TBD | TBD |

---

## 🎓 Learning Resources

- [Git Documentation](https://git-scm.com/doc)
- [GitHub Guides](https://guides.github.com/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Atlassian Git Tutorial](https://www.atlassian.com/git/tutorials)

---

**Last Updated**: 2026-07-17 21:05  
**Next Action**: Set up GitHub remote and push
