#!/bin/bash
# Start SIEMply backend server
source /opt/SIEMPLY/venv/bin/activate
cd /opt/SIEMPLY/backend
python main.py --port 5050
