#!/bin/bash
# Start SIEMply backend server
source venv/bin/activate
cd backend
python main.py --host 0.0.0.0 --port 5050 