import sys
import os

print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")

sys.path.insert(0, os.getcwd())
print(f"Python path: {sys.path[:3]}")

try:
    print("Importing uvicorn...")
    import uvicorn
    print("uvicorn imported")
    
    print("Importing api_service...")
    from services.api_service import app
    print("api_service imported")
    
    print("Starting server on port 8006...")
    uvicorn.run(app, host="0.0.0.0", port=8006, log_level="debug")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
