#!/bin/bash

# Script to set up Python linting tools for the backend

echo "Installing Python linting tools..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install linting tools
pip install flake8 mypy black isort

echo "Setting up pre-commit hook..."
cat > .git/hooks/pre-commit << 'EOL'
#!/bin/bash

# Run flake8
echo "Running flake8..."
flake8 backend/

# Run mypy for type checking
echo "Running mypy..."
mypy backend/

# Run black for code formatting
echo "Running black..."
black --check backend/

# Run isort for import sorting
echo "Running isort..."
isort --check backend/
EOL

chmod +x .git/hooks/pre-commit

echo "Linting setup complete!" 