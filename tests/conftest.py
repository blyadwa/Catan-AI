import os
import sys

# Use stub modules for numpy and pygame before importing game code
STUB_DIR = os.path.join(os.path.dirname(__file__), 'stubs')
sys.path.insert(0, STUB_DIR)

# Add code directory to path
CODE_DIR = os.path.join(os.path.dirname(__file__), '..', 'code')
sys.path.insert(0, os.path.abspath(CODE_DIR))

# Ensure pygame does not require a display
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
