"""
Handler Registry - Maps event types to their handler functions
"""
from src.consumer.handlers.order_completed_handler import handle_order_completed
from src.consumer.handlers.inventory_depleted_handler import handle_inventory_depleted
from src.consumer.handlers.review_created_handler import handle_review_created

# Registry mapping event types to handler functions
HANDLERS = {
    'order.completed': handle_order_completed,
    'inventory.depleted': handle_inventory_depleted,
    'review.created': handle_review_created,
}

def get_handler(event_type: str):
    """
    Get handler function for given event type
    
    Args:
        event_type: The type of event to handle
        
    Returns:
        Handler function or None if no handler registered
    """
    return HANDLERS.get(event_type)
