import os

def get_welcome_message():
    return {"message": "Welcome to the Product Service"}

def get_version():
    return {"version": os.getenv("API_VERSION", "unknown")}

def health():
    return {"status": "ok"}
