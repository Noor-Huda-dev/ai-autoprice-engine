from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from .price_predictor import predict_price
from django.contrib.auth import get_user_model
from django.conf import settings
from decimal import Decimal

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    def __str__(self):
        return self.name

class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    is_featured = models.BooleanField(default=False)  # for "highlighted black tag" style

    def __str__(self):
        return f"{self.category.name} > {self.name}"
    
class Tag(models.Model):
    name = models.CharField(max_length=50)
    is_trending = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    
User = get_user_model() 

class Product(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products'
    )

    subcategory = models.ForeignKey(
        SubCategory,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    name = models.CharField(max_length=200)

    slug = models.SlugField(
        unique=True,
        blank=True
    )

    is_unstitched = models.BooleanField(default=False)
    discount_locked = models.BooleanField(default=False)

    description = models.TextField()

    fabric = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    stock = models.PositiveIntegerField(default=0)

    # Current selling price
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    # Original/base price
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )

    # AI predicted price
    dynamic_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    # ML Inputs
    product_views = models.PositiveIntegerField(default=0)

    sales_count = models.PositiveIntegerField(default=0)

    average_rating = models.FloatField(default=0.0)

    season = models.CharField(
        max_length=50,
        default='Night'
    )

    image = models.ImageField(
        upload_to='products/',
        blank=True,
        null=True
    )

    is_featured = models.BooleanField(default=False)

    tag = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    sku = models.CharField(max_length=100)

    fabric_details = models.TextField(
        default="Not specified"
    )

    is_recent = models.BooleanField(default=False)

    color = models.CharField(max_length=50)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

def save(self, *args, **kwargs):

    # Auto slug
    if not self.slug:
        self.slug = slugify(self.name)

    # Save original price first time only
    if not self.base_price or self.base_price == 0:
        self.base_price = self.price

    try:

        # Predict AI price
        predicted_price = predict_price(
            product_views=self.product_views,
            sales=self.sales_count,
            base_price=float(self.base_price),
            category="Premium",
            season=self.season,
            vehicle_type="SUV"
        )

        # Safety limits
        minimum_price = float(self.base_price) * 0.70
        maximum_price = float(self.base_price) * 1.30

        # Clamp prediction
        final_price = max(
            minimum_price,
            min(predicted_price, maximum_price)
        )

        # STOP DISCOUNT FEATURE
        if not self.discount_locked:

            # Save dynamic price
            self.dynamic_price = round(final_price, 2)

            # Update actual product price
            self.price = self.dynamic_price

    except Exception as e:
        print("Dynamic Pricing Error:", e)

    super().save(*args, **kwargs)

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='gallery_images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='product_gallery/')

    def __str__(self):
        return f"Image for {self.product.name}"

class ProductStock(models.Model):
    SIZE_CHOICES = [
        ('XS', 'Extra Small'),
        ('S', 'Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
        ('XL', 'Extra Large'),
        ('XXL', 'Double Extra Large'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.CharField(max_length=10, choices=SIZE_CHOICES)
    stock = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('product', 'size')

    def __str__(self):
        return f"{self.product.name} - {self.size} ({self.stock} in stock)"
    
class ShopInfo(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    hours = models.CharField(max_length=100)

    def __str__(self):
        return self.name

User = get_user_model()

class ShippingAddress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True) # Allow null for guest checkout if applicable
    # Add these fields if they are missing or rename existing ones to match
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    address1 = models.CharField(max_length=255)
    address2 = models.CharField(max_length=255, blank=True, null=True) # Optional second address line
    city = models.CharField(max_length=100)
    province = models.CharField(max_length=100) # Or state, region, depending on country
    postal_code = models.CharField(max_length=20) # Or zip_code
    phone_number = models.CharField(max_length=20, blank=True, null=True) # Phone number is often optional or needs specific formatting
    country = models.CharField(max_length=100, default='Pakistan') # Assuming Pakistan based on time zone

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}, {self.address1}, {self.city}"

    class Meta:
        verbose_name_plural = "Shipping Addresses" # Good practice for plural name

class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
        ('Complete', 'Complete'), # Capitalized 'Complete' for consistency
    ]
    PAYMENT_CHOICES = [
        ('COD', 'Cash on Delivery'),
        ('CARD', 'Card'),
        ('JAZZCASH', 'Jazzcash'),
        ('BANK', 'Bank Transfer'),
    ]
    complete = models.BooleanField(default=False) # Indicates if the order process is complete
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending') # Capitalized 'Pending' for consistency
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='customer_orders', null=True, blank=True)
    # The 'user' field seems redundant if 'customer' is also a ForeignKey to User.
    # It's usually either 'customer' or 'user', not both, linking to the person who placed the order.
    # If 'user' means a staff user managing the order, rename it clearly.
    # For now, I'm keeping it as is, but it's a potential area for simplification.
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_orders', null=True, blank=True) # Consider if this is needed in addition to 'customer'
    shipping_address = models.ForeignKey(ShippingAddress, on_delete=models.SET_NULL, null=True, blank=True)
    shipping_cost = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('170.00'))
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='COD')
    is_paid = models.BooleanField(default=False)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) # This is the field to set the final total!
    order_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) # Added for update tracking

    def __str__(self):
        return f"Order No. {self.id} - {self.customer.username if self.customer else 'Guest'}"
    
    @property
    def product_total(self):
        total = sum(Decimal(item.line_total) for item in self.orderitems.all())
        return total

    @property
    def total_price(self):
        return self.product_total + Decimal(self.shipping_cost)

class OrderItem(models.Model):

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='orderitems')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    size = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} @ Rs. {self.price} - Size: {self.size or 'N/A'}"

    @property
    def line_total(self):
        return self.quantity * self.price
class Cart(models.Model):
    # Ensure this class definition is present and not nested or mis-indented
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {self.user.username}"

    @property
    def total_quantity(self):
        return self.cartitem_set.aggregate(total=models.Sum('quantity'))['total'] or 0

    @property
    def total_price(self):
        total = Decimal('0.00')
        for item in self.cartitem_set.all():
            total += item.product.price * item.quantity
        return total

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    size = models.CharField(max_length=10, null=True, blank=True) # Allow null for unstitched or if no size selected
    
    class Meta:
        # Ensures that a user can't add the same product with the same size multiple times
        unique_together = ('cart', 'product', 'size') 

    def __str__(self):
        return f"{self.quantity} x {self.product.name} ({self.size or 'N/A'}) in {self.cart.user.username}'s cart"

    def save(self, *args, **kwargs):
        # Optional: Add validation here to ensure quantity doesn't exceed stock
        if not self.product.is_unstitched and self.size:
            try:
                product_stock = ProductStock.objects.get(product=self.product, size=self.size)
                if self.quantity > product_stock.stock:
                    # Or raise a ValidationError if you prefer
                    self.quantity = product_stock.stock # Cap quantity to available stock
            except ProductStock.DoesNotExist:
                self.quantity = 0 # If stock record doesn't exist for size, set quantity to 0
        elif self.product.is_unstitched:
            if self.quantity > self.product.stock:
                self.quantity = self.product.stock
        
        super().save(*args, **kwargs)

    @property
    def get_total(self):
        return self.product.price * self.quantity

    
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    wishlist = models.ManyToManyField('Product', through='Wishlist', related_name='wishlisted_by')
    
    email = models.EmailField(blank=True)
    full_name = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.user.username

class Wishlist(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='wishlist_items',null=True,blank=True)
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('user_profile', 'product')

    def __str__(self):
        return f"{self.user_profile.user.username} - {self.product.name} (x{self.quantity})"
    
class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=100)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name} - {self.subject}"