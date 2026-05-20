from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    try:
        return float(value) * float(arg)
    except:
        return 0

@register.filter
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

@register.filter
def index(sequence, position):
    try:
        return sequence[position]
    except (IndexError, TypeError):
        return ''

@register.filter
def split(value, delimiter):
    return value.split(delimiter)

@register.filter
def cart_total(cart, products_dict):
    # Safe guard: cart must be a dict
    if not isinstance(cart, dict):
        return 0

    total = 0
    for key, quantity in cart.items():
        try:
            product_id, size = key.split('|')
            product = products_dict.get(product_id)
            if product:
                total += product.price * int(quantity)
        except Exception:
            continue
    return total

@register.filter
def cart_total(cart, products_dict):
    total = 0
    if not isinstance(cart, dict):  # Ensure cart is a dictionary
        return total
    
    if products_dict:
        for product_id, item_data in cart.items():
            try:
                # Handle cases where item_data might be a dict or just quantity
                if isinstance(item_data, dict):
                    quantity = item_data.get('quantity', 0)
                else:
                    quantity = item_data  # Fallback if it's just the quantity
                
                # Convert product_id to string for lookup
                product = products_dict.get(str(product_id))
                if product and hasattr(product, 'price'):
                    total += product.price * quantity
            except (TypeError, AttributeError, ValueError):
                continue  # Skip invalid entries
    return total
@register.filter
def mul(value, arg):
    return value * arg