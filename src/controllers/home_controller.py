import os

def get_welcome_message():
    """
    Get welcome message for the Product Service.
    
    Returns:
        dict: Welcome message
    """
    return {"message": "Welcome to the Product Service"}

def get_version():
    """
    Get API version information.
    
    Returns:
        dict: API version from environment variable or 'unknown'
    """
    return {"version": os.getenv("API_VERSION", "unknown")}

def health():
    """
    Health check endpoint.
    
    Returns:
        dict: Health status indicator
    """
    return {"status": "ok"}
