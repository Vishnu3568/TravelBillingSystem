# Travel Billing System Backend Application package
import os
import sys

# Safeguard to append backend directory to sys.path for isolated execution/ide analysis
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
