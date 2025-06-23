#!/bin/bash

# Script to install TypeScript type definitions required by the project

echo "Installing TypeScript type definitions..."

# Install React and related type definitions
npm install --save-dev @types/react @types/react-dom @types/node

# Install Material-UI related type definitions
npm install --save-dev @types/mui__material

# Install other required type definitions
npm install --save-dev @types/react-router-dom

echo "Rebuilding node modules..."
npm rebuild

echo "Running type check..."
npx tsc --noEmit

echo "TypeScript setup complete!" 