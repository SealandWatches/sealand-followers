print("THIS IS THE SCRIPT THAT IS RUNNING")
import os, sys
print("FILE:", __file__)
print("ENV KEYS:", sorted(os.environ.keys()))
sys.exit(1)
