from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Custom template filter to access dictionary items by key
    Usage: {{ my_dict|get_item:key_variable }}
    """
    if dictionary is None:
        return None
    
    # Handle nested keys with dot notation
    if '.' in str(key):
        parts = str(key).split('.')
        value = dictionary
        for part in parts:
            if value is None:
                return None
            if isinstance(value, dict):
                value = value.get(part)
            else:
                try:
                    value = getattr(value, part)
                    if callable(value):
                        value = value()
                except (AttributeError, TypeError):
                    return None
        return value
    
    # Handle direct key access
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    
    # Handle attribute access for objects
    try:
        return getattr(dictionary, key)
    except (AttributeError, TypeError):
        return None 