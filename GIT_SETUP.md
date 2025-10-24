# Git Setup and Usage Guide for SIEMPLY

## Repository Information
- **GitHub Repository**: https://github.com/asimchamp/SIEMPLY
- **Branch**: main
- **Git LFS**: Enabled for database files (*.db)

## Initial Setup (Already Completed)
The repository has been initialized with the following:
- ✅ Git repository initialized
- ✅ Git LFS installed and configured
- ✅ Remote repository added
- ✅ .gitignore created
- ✅ .gitattributes configured
- ✅ github-update.sh script ready

## Using the GitHub Update Script

### Interactive Mode (Recommended)
Simply run the script without arguments to access the interactive menu:

```bash
./github-update.sh
```

This will show you:
- Current repository status
- Database and environment file status
- Interactive menu with options

### Quick Update Mode
For fast updates with automatic timestamp:

```bash
./github-update.sh quick
```

This will:
1. Add all changes
2. Commit with timestamp
3. Push to current branch
4. Generate PR URL if not on main

### Push to Main Branch
To push directly to the main branch:

```bash
./github-update.sh main
```

⚠️ **Warning**: This pushes directly to main. Use with caution.

### Create New Branch
To create a new feature branch:

```bash
./github-update.sh branch
```

This will:
1. Prompt for branch name
2. Create and switch to new branch
3. Commit your changes
4. Push to GitHub
5. Generate Pull Request URL

### Check Status
To see current repository status:

```bash
./github-update.sh status
```

## Interactive Menu Options

When you run `./github-update.sh`, you'll see these options:

1. **Quick Update** - Fast commit & push with timestamp
2. **Push to main branch** - Direct push to main (requires confirmation)
3. **Create new branch and push** - Create feature branch workflow
4. **Show current status** - Display repository and file status
5. **Manage database & env files** - Database backup and file management
6. **Exit** - Close the script

## Database Management

The script automatically tracks `backend/siemply.db` with Git LFS.

### Database & Environment Files Menu
From the main menu, select option 5 to access:

1. **Ensure all files are tracked** - Verify LFS tracking
2. **Show file status** - Check database and file status
3. **Backup database** - Create timestamped backup
4. **Back to main menu** - Return to main options

### Manual Database Backup
```bash
cp backend/siemply.db backend/siemply.db.backup.$(date +%Y%m%d_%H%M%S)
```

## Important Notes

### Security
- ✅ `.env` files are **NOT** tracked for security
- ✅ Database files use Git LFS for efficiency
- ✅ Logs and temporary files are ignored
- ✅ Virtual environments are excluded

### What Gets Tracked
- ✅ Source code (Python, JavaScript, TypeScript)
- ✅ Configuration files (non-sensitive)
- ✅ Database files (via Git LFS)
- ✅ Documentation (Markdown, YAML)
- ✅ Scripts and tools
- ✅ `track.json` (AI change tracking)

### What Gets Ignored
- ❌ `.env` files (sensitive credentials)
- ❌ `node_modules/` and `venv/` directories
- ❌ Log files (`*.log`)
- ❌ Job logs (`backend/logs/**/*.json`)
- ❌ Database backups (`*.db.backup.*`)
- ❌ IDE files (`.vscode/`, `.idea/`)
- ❌ OS files (`.DS_Store`, `Thumbs.db`)

## Git LFS File Tracking

The following file types use Git LFS:
- `*.db` - SQLite database files
- `*.tar.gz` - Tar archives
- `*.zip` - Zip archives
- `*.tgz` - Compressed tar archives

To check LFS status:
```bash
git lfs ls-files
```

## Common Workflows

### Daily Development
1. Make your changes
2. Run `./github-update.sh quick`
3. Enter commit message
4. Changes are pushed!

### Feature Development
1. Make your changes
2. Run `./github-update.sh branch`
3. Enter branch name (e.g., `feature-new-dashboard`)
4. Enter commit message
5. Click the PR URL to create Pull Request

### Checking Status
```bash
./github-update.sh status
# or
git status
```

### Viewing Commit History
```bash
git log --oneline -10  # Last 10 commits
```

## Troubleshooting

### Git LFS Issues
If Git LFS files aren't syncing:
```bash
git lfs install
git lfs track "*.db"
git add .gitattributes
```

### Remote Repository Issues
If remote is not configured:
```bash
git remote add origin https://github.com/asimchamp/SIEMPLY.git
```

### Authentication Issues
If you get authentication errors, you may need to:
1. Set up SSH keys for GitHub
2. Or use Personal Access Token for HTTPS

### Check Remote
```bash
git remote -v
```

## First Push to GitHub

To perform your first push to GitHub:

```bash
# Option 1: Interactive (recommended for first push)
./github-update.sh

# Option 2: Quick push
./github-update.sh quick
```

⚠️ **Note**: The first push may take longer as Git LFS uploads database files.

## Additional Resources

- **GitHub Repository**: https://github.com/asimchamp/SIEMPLY
- **Git Documentation**: https://git-scm.com/doc
- **Git LFS Documentation**: https://git-lfs.github.com/

## Support

For issues with the repository:
1. Check `./github-update.sh status`
2. Review `.gitignore` and `.gitattributes`
3. Verify Git LFS with `git lfs ls-files`
4. Check remote with `git remote -v`

