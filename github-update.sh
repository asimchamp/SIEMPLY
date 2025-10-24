#!/bin/bash

# SIEMPLY GitHub Update Script
# Unified script for managing code updates to GitHub repository

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  SIEMPLY GitHub Update Tool${NC}"
    echo -e "${BLUE}================================${NC}"
}

# Function to check if git is initialized
check_git() {
    if [ ! -d ".git" ]; then
        print_error "Git repository not initialized. Please run 'git init' first."
        exit 1
    fi
}

# Function to check if we're in the project directory
check_project() {
    if [ ! -f "README.md" ] || [ ! -d "backend" ] || [ ! -d "frontend" ]; then
        print_error "Please run this script from the SIEMPLY project root directory."
        exit 1
    fi
}

# Function to ensure database and env files are tracked
ensure_files_tracked() {
    print_status "Ensuring database and environment files are tracked..."
    
    # Check if Git LFS is installed and configured
    if ! command -v git-lfs > /dev/null 2>&1; then
        print_warning "Git LFS not installed. Installing..."
        if command -v apt-get > /dev/null 2>&1; then
            curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | sudo bash
            sudo apt-get install -y git-lfs
        elif command -v brew > /dev/null 2>&1; then
            brew install git-lfs
        else
            print_error "Cannot install Git LFS automatically. Please install it manually."
            return 1
        fi
        git lfs install
    fi
    
    # Ensure .gitattributes exists for LFS tracking
    if [ ! -f ".gitattributes" ]; then
        print_status "Creating .gitattributes for Git LFS..."
        echo "*.db filter=lfs diff=lfs merge=lfs -text" > .gitattributes
        git add .gitattributes
    fi
    
    # Note: .env and *.db in .gitignore is intentional for security
    # SIEMPLY uses .gitignore to exclude sensitive files while using Git LFS for databases
    
    # Ensure database files are tracked with LFS
    if [ -f "backend/siemply.db" ]; then
        print_status "Found backend/siemply.db, ensuring it's tracked with LFS..."
        git add "backend/siemply.db" 2>/dev/null || true
    fi
    
    # Ensure .env files are tracked (optional - comment out if you don't want .env in git)
    # Uncomment these lines if you want to track .env files in your private repo
    # if [ -f ".env" ]; then
    #     print_status "Found root .env, ensuring it's tracked..."
    #     git add ".env" 2>/dev/null || true
    # fi
    # 
    # if [ -f "frontend/.env" ]; then
    #     print_status "Found frontend/.env, ensuring it's tracked..."
    #     git add "frontend/.env" 2>/dev/null || true
    # fi
    
    print_status "Note: .env files are NOT being tracked for security. Modify script if needed."
    
    print_status "✅ Database and environment files are now tracked with Git LFS"
}

# Function to manage database and env files
manage_database_env_files() {
    print_status "Database and Environment Files Management"
    echo "============================================="
    echo ""
    
    while true; do
        echo "Choose an action:"
        echo "1) Ensure all files are tracked"
        echo "2) Show file status"
        echo "3) Backup database (siemply.db)"
        echo "4) Back to main menu"
        echo ""
        
        read -p "Enter your choice (1-4): " choice
        
        case $choice in
            1)
                ensure_files_tracked
                echo ""
                ;;
            2)
                show_status
                echo ""
                ;;
            3)
                if [ -f "backend/siemply.db" ]; then
                    backup_name="backend/siemply.db.backup.$(date +%Y%m%d_%H%M%S)"
                    print_status "Creating backup: $backup_name"
                    cp "backend/siemply.db" "$backup_name"
                    print_status "✅ Database backup created successfully"
                else
                    print_error "backend/siemply.db not found"
                fi
                echo ""
                ;;
            4)
                return
                ;;
            *)
                print_error "Invalid choice. Please try again."
                ;;
        esac
    done
}

# Function to show current status
show_status() {
    echo -e "${CYAN}Current Repository Status:${NC}"
    echo "Branch: $(git branch --show-current)"
    echo "Repository: $(git remote get-url origin)"
    echo ""
    
    # Show database and env file status
    echo -e "${CYAN}Database Files:${NC}"
    if [ -f "backend/siemply.db" ]; then
        if git lfs ls-files 2>/dev/null | grep -q "backend/siemply.db" || false; then
            echo -e "${GREEN}✅ backend/siemply.db exists - LFS tracked${NC}"
        else
            echo -e "${GREEN}✅ backend/siemply.db exists - not LFS tracked yet${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  backend/siemply.db not found${NC}"
    fi
    
    echo ""
    echo -e "${CYAN}Environment Files:${NC}"
    
    if [ -f ".env" ]; then
        echo -e "${GREEN}✅ .env exists (root)${NC}"
    else
        echo -e "${YELLOW}⚠️  .env not found in root${NC}"
    fi
    
    if [ -f "frontend/.env" ]; then
        echo -e "${GREEN}✅ frontend/.env exists${NC}"
    else
        echo -e "${YELLOW}⚠️  frontend/.env not found${NC}"
    fi
    
    # Check for important files
    echo ""
    echo -e "${CYAN}Important Files:${NC}"
    if [ -f "backend/siemply.db" ]; then
        echo -e "${GREEN}✅ backend/siemply.db exists${NC}"
    else
        echo -e "${YELLOW}⚠️  backend/siemply.db not found${NC}"
    fi
    
    if [ -f "track.json" ]; then
        echo -e "${GREEN}✅ track.json exists${NC}"
    else
        echo -e "${YELLOW}⚠️  track.json not found${NC}"
    fi
    
    echo ""
    
    if [ -n "$(git status --porcelain)" ]; then
        echo -e "${YELLOW}Changes detected:${NC}"
        git status --short
        echo ""
    else
        echo -e "${GREEN}No changes detected.${NC}"
    fi
}

# Function for quick update mode
quick_update() {
    print_status "Quick Update Mode"
    echo "=========================="
    
    # Ensure database and env files are tracked
    ensure_files_tracked
    
    # Check for changes
    if [ -z "$(git status --porcelain)" ]; then
        print_warning "No changes detected. Nothing to commit."
        return
    fi
    
    # Show current status
    echo -e "${GREEN}Current branch:${NC} $(git branch --show-current)"
    echo -e "${GREEN}Repository:${NC} $(git remote get-url origin)"
    echo ""
    
    # Get commit message
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    read -p "Enter commit message (or press Enter for timestamp): " commit_msg
    commit_msg=${commit_msg:-"Update: $timestamp"}
    
    # Add and commit
    print_status "Adding files..."
    git add .
    
    print_status "Committing changes..."
    git commit -m "$commit_msg"
    
    # Ask about branch
    current_branch=$(git branch --show-current)
    if [ "$current_branch" = "main" ]; then
        echo ""
        read -p "Push to main branch? (y/N): " push_main
        if [[ $push_main =~ ^[Yy]$ ]]; then
            print_status "Pushing to main branch..."
            git push origin main
            print_status "✅ Successfully pushed to main branch!"
        else
            print_warning "Skipped push to main branch."
        fi
    else
        print_status "Pushing to current branch: $current_branch"
        git push origin "$current_branch"
        
        # Generate PR URL
        repo_url=$(git remote get-url origin | sed 's/\.git$//')
        pr_url="$repo_url/compare/main...$current_branch"
        echo ""
        print_status "✅ Successfully pushed to branch: $current_branch"
        echo -e "${CYAN}Create Pull Request:${NC} $pr_url"
    fi
}

# Function for interactive mode
interactive_mode() {
    while true; do
        print_header
        echo ""
        show_status
        echo ""
        echo "Choose an option:"
        echo "1) Quick Update (fast commit & push)"
        echo "2) Push to main branch"
        echo "3) Create new branch and push"
        echo "4) Show current status"
        echo "5) Manage database & env files"
        echo "6) Exit"
        echo ""
        
        read -p "Enter your choice (1-6): " choice
        
        case $choice in
            1)
                quick_update
                echo ""
                read -p "Press Enter to continue..."
                ;;
            2)
                push_to_main
                echo ""
                read -p "Press Enter to continue..."
                ;;
            3)
                create_new_branch
                echo ""
                read -p "Press Enter to continue..."
                ;;
            4)
                show_status
                echo ""
                read -p "Press Enter to continue..."
                ;;
            5)
                manage_database_env_files
                echo ""
                read -p "Press Enter to continue..."
                ;;
            6)
                print_status "Goodbye!"
                exit 0
                ;;
            *)
                print_error "Invalid choice. Please try again."
                ;;
        esac
    done
}

# Function to push to main branch
push_to_main() {
    print_status "Push to Main Branch Mode"
    echo "=============================="
    
    current_branch=$(git branch --show-current)
    
    if [ "$current_branch" != "main" ]; then
        print_warning "You are currently on branch: $current_branch"
        read -p "Switch to main branch? (y/N): " switch_main
        if [[ $switch_main =~ ^[Yy]$ ]]; then
            git checkout main
            git pull origin main
        else
            print_error "Cannot push to main from different branch."
            return
        fi
    fi
    
    # Check for changes
    if [ -z "$(git status --porcelain)" ]; then
        print_warning "No changes detected. Nothing to commit."
        return
    fi
    
    # Show changes
    echo ""
    echo -e "${YELLOW}Changes to be committed:${NC}"
    git status --short
    echo ""
    
    # Get commit message
    read -p "Enter commit message: " commit_msg
    if [ -z "$commit_msg" ]; then
        print_error "Commit message is required."
        return
    fi
    
    # Confirm push
    echo ""
    print_warning "You are about to push to the main branch!"
    read -p "Are you sure? (y/N): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        print_warning "Push cancelled."
        return
    fi
    
    # Ensure database and env files are tracked
    ensure_files_tracked
    
    # Add, commit, and push
    print_status "Adding files..."
    git add .
    
    print_status "Committing changes..."
    git commit -m "$commit_msg"
    
    print_status "Pushing to main branch..."
    git push origin main
    
    print_status "✅ Successfully pushed to main branch!"
}

# Function to create new branch
create_new_branch() {
    print_status "Create New Branch Mode"
    echo "=========================="
    
    # Get branch name
    read -p "Enter branch name: " branch_name
    if [ -z "$branch_name" ]; then
        print_error "Branch name is required."
        return
    fi
    
    # Check if branch exists
    if git show-ref --verify --quiet refs/heads/"$branch_name"; then
        print_warning "Branch '$branch_name' already exists."
        read -p "Switch to existing branch? (y/N): " switch_branch
        if [[ $switch_branch =~ ^[Yy]$ ]]; then
            git checkout "$branch_name"
        else
            return
        fi
    else
        # Create and switch to new branch
        print_status "Creating new branch: $branch_name"
        git checkout -b "$branch_name"
    fi
    
    # Check for changes
    if [ -z "$(git status --porcelain)" ]; then
        print_warning "No changes detected. Nothing to commit."
        return
    fi
    
    # Show changes
    echo ""
    echo -e "${YELLOW}Changes to be committed:${NC}"
    git status --short
    echo ""
    
    # Get commit message
    read -p "Enter commit message: " commit_msg
    if [ -z "$commit_msg" ]; then
        print_error "Commit message is required."
        return
    fi
    
    # Ensure database and env files are tracked
    ensure_files_tracked
    
    # Add, commit, and push
    print_status "Adding files..."
    git add .
    
    print_status "Committing changes..."
    git commit -m "$commit_msg"
    
    print_status "Pushing to new branch..."
    git push origin "$branch_name"
    
    # Generate PR URL
    repo_url=$(git remote get-url origin | sed 's/\.git$//')
    pr_url="$repo_url/compare/main...$branch_name"
    
    print_status "✅ Successfully pushed to branch: $branch_name"
    echo ""
    echo -e "${CYAN}Create Pull Request:${NC} $pr_url"
    
    # Ask to open PR in browser
    read -p "Open Pull Request in browser? (y/N): " open_pr
    if [[ $open_pr =~ ^[Yy]$ ]]; then
        if command -v xdg-open > /dev/null; then
            xdg-open "$pr_url"
        elif command -v open > /dev/null; then
            open "$pr_url"
        else
            print_warning "Could not open browser automatically."
            print_status "Please manually open: $pr_url"
        fi
    fi
}

# Main script logic
main() {
    # Check prerequisites
    check_project
    check_git
    
    # Check if remote is configured
    if ! git remote get-url origin > /dev/null 2>&1; then
        print_error "No remote repository configured."
        print_status "Please add remote with: git remote add origin <repository-url>"
        exit 1
    fi
    
    # Check command line arguments
    if [ "$1" = "quick" ]; then
        quick_update
    elif [ "$1" = "main" ]; then
        push_to_main
    elif [ "$1" = "branch" ]; then
        create_new_branch
    elif [ "$1" = "status" ]; then
        show_status
    elif [ "$1" = "interactive" ] || [ -z "$1" ]; then
        interactive_mode
    else
        echo "Usage: $0 [quick|main|branch|status|interactive]"
        echo ""
        echo "Modes:"
        echo "  quick      - Quick update with timestamp (includes database files)"
        echo "  main       - Push to main branch (includes database files)"
        echo "  branch     - Create new branch and push (includes database files)"
        echo "  status     - Show current status"
        echo "  interactive - Interactive menu (default)"
        echo ""
        echo "Note: Database files (siemply.db) are tracked with Git LFS"
        echo "      .env files are NOT tracked by default for security."
        exit 1
    fi
}

# Run main function with all arguments