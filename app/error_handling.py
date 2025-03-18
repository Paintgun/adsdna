import functools
import logging
import traceback

logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def safe_process(default_return=None, item_id_arg=1):
    """
    Decorator for safely processing a single item.
    Returns default_return if processing fails.
    
    Args:
        default_return: Value to return if processing fails
        item_id_arg: Position of the item ID argument (default is 1, which is the second argument)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Extract item ID from args or kwargs
                item_id = "unknown"
                if len(args) > item_id_arg:
                    item_id = args[item_id_arg]
                elif "client" in kwargs:
                    item_id = kwargs["client"]
                
                logger.error(f"Error processing {item_id} in {func.__name__}: {str(e)}")
                logger.error(traceback.format_exc())
                return default_return
        return wrapper
    return decorator