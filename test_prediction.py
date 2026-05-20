import os
import django

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tariqworldwide.settings')
django.setup()

from dresses.price_predictor import predict_price

price = predict_price(
    50,          # product_views
    25,          # sales
    100,         # base_price
    "Premium",   # category (STRING)
    "Night",     # season (STRING)
    "SUV"        # vehicle_type (ignored but keep string)
)

print("Predicted Price:", price)