from django.db.models import Count, Min, Max
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, F
from django.template.loader import render_to_string
from django.db import transaction
from decimal import Decimal
from django.http import HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from .forms import ContactForm, ShippingAddressForm
from .models import Product, Category, SubCategory, UserProfile, Wishlist, Tag, ProductStock, ContactMessage, ShippingAddress, CartItem, OrderItem, Order, Cart
from django.core.mail import send_mail
from django.conf import settings
def home(request):
    cart_total_quantity = 0
    cart_items = []
    
    if request.user.is_authenticated:
        try:
            # Get the user's cart. get_or_create returns a tuple: (object, created_boolean)
            current_cart, created = Cart.objects.get_or_create(user=request.user)
            cart_items = current_cart.cartitem_set.all()
            cart_total_quantity = current_cart.total_quantity # Ensure your Cart model has this property or method
        except Exception as e:
            print(f"Error fetching/creating cart for user {request.user.username}: {e}")
            cart_total_quantity = 0
            cart_items = []
    else:
        # For anonymous users, get cart data from session
        session_cart = request.session.get('cart', {})
        # Assuming session_cart stores product_id (or product_id|size) as key and quantity as value
        # Example: {'1': {'quantity': 2}, '2|M': {'quantity': 1}}
        # Or if it's just {'product_id': quantity}:
        # cart_total_quantity = sum(session_cart.values())
        
        # If session_cart stores dictionaries like {'product_id': {'quantity': X, 'size': Y}}
        cart_total_quantity = sum(item_data.get('quantity', 0) for item_data in session_cart.values())
        
        # You might also want to fetch actual Product objects for cart_items for anonymous user
        # This part is more complex if you need product details in the cart sidebar for anonymous users.
        # For now, let's keep cart_items empty for anonymous if not strictly needed or fetched elsewhere.
        # If you need product details for anonymous cart, you'll need to query Product model based on session_cart keys.
        # Example for anonymous cart_items (simplified, might need more detail):
        # product_ids_in_session = [k.split('|')[0] for k in session_cart.keys()] # Extract product IDs
        # products_in_cart = Product.objects.filter(id__in=product_ids_in_session)
        # cart_items_for_anon = []
        # for product in products_in_cart:
        #     for key, data in session_cart.items():
        #         if str(product.id) == key.split('|')[0]:
        #             cart_items_for_anon.append({
        #                 'product': product,
        #                 'quantity': data.get('quantity', 0),
        #                 'size': data.get('size', None) # If size is stored in session
        #             })
        # cart_items = cart_items_for_anon # Assign this to cart_items if you want to use it in template

    categories = Category.objects.all()

    # Initial product queryset
    products = Product.objects.all()
    featured_products = Product.objects.filter(is_featured=True)[:8]

    # Filters from URL
    selected_availability = request.GET.getlist('availability')
    selected_colors = request.GET.getlist('color')
    selected_fabrics = request.GET.getlist('fabric')
    max_price_filter = request.GET.get('price')

    # Apply filters
    if selected_colors:
        products = products.filter(color__in=selected_colors)

    if selected_fabrics:
        products = products.filter(fabric__in=selected_fabrics)

    if max_price_filter:
        try:
            max_price_value = int(max_price_filter)
            products = products.filter(price__lte=max_price_value)
        except ValueError:
            pass  # Ignore invalid price filter

    # Stock-based availability filtering
    if selected_availability:
        if 'In Stock' in selected_availability:
            # Filter products that have at least one stock item with stock > 0
            products = products.filter(productstock__stock__gt=0).distinct()
        elif 'Out of Stock' in selected_availability:
            # Filter products where sum of all stock items is 0 or no stock records exist
            products_in_stock_ids = ProductStock.objects.filter(stock__gt=0).values_list('product__id', flat=True)
            products = products.exclude(id__in=products_in_stock_ids)

    # Filter options for sidebar
    if Product.objects.exists():
        min_price = Product.objects.aggregate(Min('price'))['price__min'] or 0
        max_price = Product.objects.aggregate(Max('price'))['price__max'] or 100000
    else:
        min_price = 0
        max_price = 100000

    # Counts for availability options might need adjustment based on ProductStock
    availability_options = [
        {'label': 'In Stock', 'count': Product.objects.filter(productstock__stock__gt=0).distinct().count()},
        {'label': 'Out of Stock', 'count': Product.objects.exclude(productstock__stock__gt=0).distinct().count()},
    ]

    colors = Product.objects.values('color').distinct()
    color_options = [{'color': c['color'], 'count': Product.objects.filter(color=c['color']).count()} for c in colors if c['color']]

    fabrics = Product.objects.values('fabric').distinct()
    fabric_options = [{'fabric': f['fabric'], 'count': Product.objects.filter(fabric=f['fabric']).count()} for f in fabrics if f['fabric']]

    headings = [
        "READY TO WEAR",
        "FESTIVE EDIT",
        "SUMMER ESSENTIALS",
        "LUXURY PRET",
        "CASUAL COLLECTION"
    ]
    subheadings = [
        "EID || NEW ARRIVALS",
        "Celebrate in Style",
        "Cool Looks for Hot Days",
        "Elegant Styles for Every Occasion",
        "Everyday Comfort Redefined"
    ]

    context = {
        'featured_products': featured_products,
        'products': products,
        'cart': cart_items, # This will be the list of CartItem objects for the user's cart (or anonymous dict for session)
        'cart_count': cart_total_quantity, # Total number of items (sum of quantities)
        'sidebar_visible': request.GET.get('show_filters') == '1',
        'headings': headings,
        'subheadings': subheadings,
        'categories': categories,
        'min_price': min_price,
        'max_price': max_price,
        'availability': availability_options,
        'colors': color_options,
        'fabrics': fabric_options,
        'selected_availability': selected_availability,
        'selected_colors': selected_colors,
        'selected_fabrics': selected_fabrics,
    }

    return render(request, 'dresses/home.html', context)

def shop_all(request):
    categories = Category.objects.all()
    products = Product.objects.all()
    trending_tags = Tag.objects.filter(is_trending=True)
    return render(request, 'dresses/category_page.html', {
        'categories': categories,
        'products': products,
        'trending_tags': trending_tags,
    })

def shop_by_category(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category)
    subcategories = SubCategory.objects.filter(category=category)
    trending_tags = Tag.objects.filter(is_trending=True)
    categories = Category.objects.all()
    products_dict = {str(product.id): product for product in Product.objects.all()}

    return render(request, 'dresses/category_page.html', {
        'category': category,
        'subcategories': subcategories,
        'products': products,
        'trending_tags': trending_tags,
        'products_dict': products_dict,
        'categories': categories,
    })

def shop_by_subcategory(request, category_slug, subcategory_slug):
    category = get_object_or_404(Category, slug=category_slug)
    subcategory = get_object_or_404(SubCategory, slug=subcategory_slug, category=category)
    products = Product.objects.filter(subcategory=subcategory)
    trending_tags = Tag.objects.filter(is_trending=True)
    subcategories = SubCategory.objects.filter(category=category)
    categories = Category.objects.all()
    products_dict = {str(product.id): product for product in Product.objects.all()}

    return render(request, 'dresses/category_page.html', {
        'category': category,
        'subcategory': subcategory,
        'subcategories': subcategories,
        'products': products,
        'trending_tags': trending_tags,
        'products_dict': products_dict,
        'categories': categories,
    })

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    # Auto increase views
    product.product_views += 1
    product.save()
    images = product.gallery_images.all()

    # Get stock details for display (e.g., available sizes and their stock)
    product_stocks = ProductStock.objects.filter(product=product, stock__gt=0)
    available_sizes = [{'size': ps.size, 'stock': ps.stock} for ps in product_stocks]

    # --- Cart Logic for authenticated users in product detail ---
    cart_items_count = 0
    if request.user.is_authenticated:
        current_cart, created = Cart.objects.get_or_create(user=request.user)
        cart_items_count = current_cart.total_quantity # Using Cart model property
    # --- End Cart Logic ---

    # Recently viewed logic
    recently_viewed_ids = request.session.get('recently_viewed', [])
    
    # Add current product to recently viewed, limit to a certain number (e.g., 5-10)
    if product.id in recently_viewed_ids:
        recently_viewed_ids.remove(product.id) # Move to front if already exists
    recently_viewed_ids.insert(0, product.id)
    request.session['recently_viewed'] = recently_viewed_ids[:8] # Keep last 8

    # Fetch recently viewed products, excluding the current one
    recently_viewed_products = Product.objects.filter(id__in=request.session['recently_viewed']).exclude(id=product.id)
    # Maintain order of recently viewed products
    recently_viewed_products_ordered = sorted(
        recently_viewed_products, 
        key=lambda p: request.session['recently_viewed'].index(p.id)
    )


    context = {
        'product': product,
        'images': images,
        'available_sizes': available_sizes, # Pass available sizes and their stock
        'recently_viewed_products': recently_viewed_products_ordered,
        'cart_count': cart_items_count, # Pass cart count for header/sidebar
    }
    return render(request, 'dresses/product_detail.html', context)

def shop(request):
    products = Product.objects.all()
    categories = Category.objects.all()
    colors = Product.objects.values_list('color', flat=True).distinct()
    # products_dict is not typically needed here
    category_slug = request.GET.get('category')
    price_ranges = request.GET.getlist('price_range')
    availability = request.GET.getlist('availability')
    selected_colors = request.GET.getlist('color')
    sort = request.GET.get('sort')

    if category_slug:
        products = products.filter(category__slug=category_slug)

    if '0-1999' in price_ranges:
        products = products.filter(price__lte=1999)
    if '2000-3999' in price_ranges:
        products = products.filter(price__gte=2000, price__lte=3999)
    if '4000-5999' in price_ranges:
        products = products.filter(price__gte=4000, price__lte=5999)
    if '6000+' in price_ranges:
        products = products.filter(price__gte=6000)

    # Filtering by stock considering ProductStock
    if 'in_stock' in availability:
        products = products.filter(productstock__stock__gt=0).distinct()
    if 'out_of_stock' in availability:
        products_in_stock_ids = ProductStock.objects.filter(stock__gt=0).values_list('product__id', flat=True)
        products = products.exclude(id__in=products_in_stock_ids)

    if selected_colors:
        products = products.filter(color__in=selected_colors)

    if sort == 'latest':
        products = products.order_by('-created_at')
    elif sort == 'low':
        products = products.order_by('price')
    elif sort == 'high':
        products = products.order_by('-price')

    context = {
        'products': products,
        'categories': categories,
        'colors': colors,
        # 'products_dict': products_dict, # Not typically needed
    }
    return render(request, 'dresses/shop.html', context)


@login_required # Or handle anonymous users differently
def checkout(request):
    user = request.user
    
    # Get the user's cart (assuming it exists for logged-in users)
    try:
        user_cart = Cart.objects.get(user=user)
    except Cart.DoesNotExist:
        # If no cart, maybe redirect to an empty cart page or home
        messages.info(request, "Your cart is empty. Please add items before checking out.")
        return redirect('home') # Or 'cart_view' if you have one

    cart_items = user_cart.cartitem_set.all()

    if not cart_items.exists():
        messages.info(request, "Your cart is empty. Please add items before checking out.")
        return redirect('home') # Or 'cart_view'

    order = Order.objects.filter(user=user, is_paid=False, status='Pending').first()

    if not order:
     order = Order.objects.create(
        user=user,
        is_paid=False,
        status='Pending',
        total_amount=Decimal('0.00')
    )
     order_created = True
    else:
        order_created = False


    if order_created: # If a new order was just created, populate its items from the cart
        with transaction.atomic():
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.product.price, # Use product's current price
                    size=cart_item.size
                )
            # After creating order items, update the order's total_amount
            # This uses the @property total_price which sums product_total and shipping_cost
            order.total_amount = order.total_price 
            order.save()
    else:
        # If the order already existed (not newly created), ensure its total_amount is up-to-date
        # based on current order items (in case cart was modified then user came back to checkout)
        # You might need more sophisticated logic here if you allow editing order items directly
        # on the checkout page, but for now, re-calculate and save.
        current_order_items = order.orderitems.all()
        if not current_order_items.exists() and cart_items.exists():
            # If existing order has no items but cart does, populate it
            with transaction.atomic():
                for cart_item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        quantity=cart_item.quantity,
                        price=cart_item.product.price,
                        size=cart_item.size
                    )
        # Always update total_amount from the properties before rendering checkout
        order.total_amount = order.total_price
        order.save()


    # Try to get existing shipping address for pre-filling the form
    try:
        shipping_address_instance = ShippingAddress.objects.get(user=user)
        shipping_form = ShippingAddressForm(instance=shipping_address_instance)
    except ShippingAddress.DoesNotExist:
        shipping_form = ShippingAddressForm()

    context = {
        'cart_items': cart_items,
        'order': order, # Pass the order object for product_total, shipping_cost, total_price
        'cart_total_quantity': user_cart.total_quantity, # Use Cart model property
        'shipping_form': shipping_form, # Pass the shipping address form
    }
    return render(request, 'dresses/checkout.html', context)


@transaction.atomic
@login_required # Or your custom decorator if handling guest checkout differently
def place_order(request):
    if request.method == 'POST':
        user = request.user
        
        # Get the current cart (it must exist for logged-in users to place an order)
        try:
            cart = Cart.objects.get(user=user)
        except Cart.DoesNotExist:
            messages.error(request, "Your cart is empty. Please add items before placing an order.")
            return redirect('home') # Or an empty cart page

        if not cart.cartitem_set.exists():
            messages.error(request, "Your cart is empty. Cannot place an empty order.")
            return redirect('home')

        # Retrieve shipping details from the POST request
        first_name = request.POST.get('first_name_hidden')
        last_name = request.POST.get('last_name_hidden')
        address1 = request.POST.get('address1_hidden')
        address2 = request.POST.get('address2_hidden', '')
        country = request.POST.get('country_hidden')
        province = request.POST.get('province_hidden')
        city = request.POST.get('city_hidden')
        postal_code = request.POST.get('postal_code_hidden')
        phone_number = request.POST.get('phone_number_hidden')
        payment_method = request.POST.get('payment_method')

        # Basic validation
        if not all([first_name, last_name, address1, country, province, city, postal_code, phone_number, payment_method]):
            messages.error(request, "Please provide all required shipping and payment information.")
            return redirect('checkout')

        try:
            with transaction.atomic():
                # Get or create ShippingAddress
                shipping_address, created = ShippingAddress.objects.get_or_create(
                    user=user, # Link address to user
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'address1': address1,
                        'address2': address2,
                        'country': country,
                        'province': province,
                        'city': city,
                        'postal_code': postal_code,
                        'phone_number': phone_number,
                    }
                )
                if not created:
                    # Update existing address if details might change
                    shipping_address.first_name = first_name
                    shipping_address.last_name = last_name
                    shipping_address.address1 = address1
                    shipping_address.address2 = address2
                    shipping_address.country = country
                    shipping_address.province = province
                    shipping_address.city = city
                    shipping_address.postal_code = postal_code
                    shipping_address.phone_number = phone_number
                    shipping_address.save()

                # Create the Order
                order = Order.objects.create(
                    user=user, # Use 'user' for consistency with authentication
                    # 'customer' field in Order model seems redundant if 'user' is used.
                    # If 'customer' is intended for guest users, the logic needs to be split.
                    # For logged-in users, 'user' is sufficient. I'm keeping both for now as per your model.
                    customer=user, # Assign customer field to current user too
                    shipping_address=shipping_address,
                    payment_method=payment_method,
                    # shipping_cost gets its default from the model (170.00)
                    status='Pending' # Set initial status
                )

                # Move items from Cart to OrderItem
                for cart_item in cart.cartitem_set.all():
                    # Before creating OrderItem, check ProductStock for availability
                    if not cart_item.product.is_unstitched:
                        product_stock = get_object_or_404(ProductStock, product=cart_item.product, size=cart_item.size)
                        if product_stock.stock < cart_item.quantity:
                            raise Exception(f"Not enough stock for {cart_item.product.name} ({cart_item.size}). Available: {product_stock.stock}, Requested: {cart_item.quantity}")
                        # Decrease stock
                        product_stock.stock -= cart_item.quantity
                        product_stock.save()
                    else:
                        # Handle stock for unstitched products (assuming direct on Product model)
                        if cart_item.product.stock < cart_item.quantity:
                            raise Exception(f"Not enough stock for {cart_item.product.name}. Available: {cart_item.product.stock}, Requested: {cart_item.quantity}")
                        cart_item.product.stock -= cart_item.quantity
                        cart_item.product.save()

                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        quantity=cart_item.quantity,
                        price=cart_item.product.price, # Capture price at time of order
                        size=cart_item.size
                    )
                # Auto increase sales
                cart_item.product.sales_count += cart_item.quantity
                cart_item.product.save()
                # After all OrderItems are created, calculate and set the final total_amount
                order.total_amount = order.total_price # Use the @property 'total_price'
                order.save() # Save the order to persist the total_amount

                # Clear the cart after order is placed
                cart.cartitem_set.all().delete() 
                # Don't delete the cart object itself as it's a OneToOne with User and will be reused
                # cart.delete() # Commented out as per typical cart lifecycle

                messages.success(request, "Your order has been placed successfully!")
                return redirect('order_confirmation', order_id=order.id)

        except Exception as e:
            messages.error(request, f"An error occurred while placing your order: {e}")
            return redirect('checkout')

    return redirect('checkout') # If not POST request, redirect to checkout


def order_confirmation(request, order_id):
    # Ensure the order belongs to the current user for security
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = order.orderitems.all() # Fetch related order items

    context = {
        'order': order,
        'order_items': order_items, # Pass items to display on confirmation page
    }
    return render(request, 'dresses/order_confirmation.html', context)

@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-order_date')
    return render(request, 'dresses/my_orders.html', {'orders': orders})

@login_required
def user_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-id')
    return render(request, 'dresses/orders.html', {'orders': orders}) # Updated template path

def about(request):
    return render(request, 'dresses/static_pages/about.html')

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        ContactMessage.objects.create(
            name=name,
            email=email,
            subject=subject,
            message=message
        )

        send_mail(
            subject=f"New Contact Message: {subject}",
            message=f"From: {name}\nEmail: {email}\n\nMessage:\n{message}",
            from_email=settings.DEFAULT_FROM_EMAIL, # Use setting for from_email
            recipient_list=['evilbutterfly901@gmail.com'], # Your recipient email
            fail_silently=False,
        )

        messages.success(request, "Your message has been sent successfully!")
        return render(request, 'dresses/static_pages/contact_success.html')

    return render(request, 'dresses/static_pages/contact.html')

def faqs(request):
    return render(request, 'dresses/static_pages/faqs.html')

def return_policy(request):
    return render(request, 'dresses/static_pages/return_policy.html')

def order_tracking(request):
    # This view might need more complex logic to actually track orders
    # based on an order ID provided by the user.
    products = Product.objects.all()
    products_dict = {product.id: product for product in products}

    return render(request, 'dresses/order_tracking.html', {
        'products_dict': products_dict,
        })

def privacy_policy(request):
    return render(request, 'dresses/static_pages/privacy_policy.html')

def payment_info(request):
    return render(request, 'dresses/static_pages/payment_info.html')

def shipping_info(request):
    return render(request, 'dresses/static_pages/shipping_info.html')

def newsletter_signup(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        # Here you would typically save the email to a NewsletterSubscriber model
        # or integrate with a mailing list service.
        messages.success(request, "Thank you for subscribing!")
        return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def add_to_wishlist_redirect(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    Wishlist.objects.get_or_create(user_profile=user_profile, product=product) # Use get_or_create to prevent duplicates
    messages.success(request, "Product added to your wishlist!")
    return redirect('home')

@login_required
def wishlist_items(request):
    wishlist_items = Wishlist.objects.filter(user_profile__user=request.user)
    items = []
    for item in wishlist_items:
        product = item.product
        items.append({
            "id": product.id,
            "name": product.name,
            "slug": product.slug,
            "price": product.price,
            "image_url": product.image.url if product.image else '/static/img/default-product.jpg',
        })
    return JsonResponse({"items": items})

def add_to_wishlist(request, product_id):
    if not request.user.is_authenticated:
        messages.warning(request, "⚠ Please login to add items to your Wishlist.")
        next_url = request.GET.get('next', '/')
        # You might want to pass 'next_url' to the login page so user is redirected back
        return redirect(f"{settings.LOGIN_URL}?next={next_url}") # Redirect to login

    product = get_object_or_404(Product, id=product_id)
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Use get_or_create to add to wishlist, preventing duplicates
    wishlist_item, item_created = Wishlist.objects.get_or_create(user_profile=user_profile, product=product)

    if item_created:
        messages.success(request, f"{product.name} added to your wishlist!")
    else:
        messages.info(request, f"{product.name} is already in your wishlist.")

    next_url = request.GET.get('next', '/')
    return redirect(next_url)

@login_required
def remove_from_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    user_profile = get_object_or_404(UserProfile, user=request.user) # Get, not get_or_create
    
    # Try to delete the wishlist item
    deleted_count, _ = Wishlist.objects.filter(user_profile=user_profile, product=product).delete()

    if deleted_count > 0:
        messages.success(request, f"{product.name} removed from your wishlist.")
        return JsonResponse({"status": "removed", "message": "Product removed from wishlist."})
    else:
        messages.info(request, f"{product.name} was not found in your wishlist.")
        return JsonResponse({"status": "not_found", "message": "Product not found in wishlist."})

@login_required
def wishlist_count(request):
    count = 0
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        count = user_profile.wishlist.count()
    except UserProfile.DoesNotExist:
        pass # User has no profile yet, wishlist count is 0
    return JsonResponse({'count': count})


def get_cart_data(request):
    """
    Helper function to get cart data for both authenticated and anonymous users.
    Returns a dictionary with 'cart_items', 'cart_total', 'cart_count'.
    """
    cart_items = []
    cart_total = Decimal('0.00')
    cart_count = 0
    
    if request.user.is_authenticated:
        user_cart, created = Cart.objects.get_or_create(user=request.user)
        # Assuming CartItem has direct access to product.price
        cart_items = user_cart.cartitem_set.all()
        cart_total = user_cart.total_price # Use the property from Cart model
        cart_count = user_cart.total_quantity # Use the property from Cart model
    else:
        # For anonymous users: use session-based cart
        session_cart = request.session.get('cart', {})
        product_ids = [int(key.split('|')[0]) for key in session_cart.keys()]
        
        if product_ids:
            # Fetch all products in one query for efficiency
            products_in_cart = Product.objects.filter(id__in=product_ids)
            products_map = {product.id: product for product in products_in_cart}

            for key, item_data in session_cart.items():
                product_id = int(key.split('|')[0])
                item_size = item_data.get('size')
                item_quantity = item_data.get('quantity', 0)

                product = products_map.get(product_id)
                if product:
                    # Create a "mock" CartItem object for display in templates
                    # This object mimics the attributes of a real CartItem for template rendering
                    mock_cart_item = type('CartItem', (object,), {
                        'product': product,
                        'quantity': item_quantity,
                        'size': item_size,
                        'get_total': lambda p=product, q=item_quantity: p.price * q
                    })()
                    cart_items.append(mock_cart_item)
                    cart_total += product.price * item_quantity
                    cart_count += item_quantity

    return {
        'cart_items': cart_items,
        'cart_total': cart_total,
        'cart_count': cart_count,
    }

# --- CART VIEWS ---

@login_required # Agar yeh page sirf logged-in users ke liye hai, warna hata dein
def cart_view(request):
    cart_data = get_cart_data(request) # Use the helper function

    context = {
        'cart_items': cart_data['cart_items'],
        'total': cart_data['cart_total'],
        'cart_count': cart_data['cart_count'],
    }
    return render(request, 'dresses/cart_page.html', context)


def cart_sidebar_view(request):
    cart_data = get_cart_data(request) # Use the helper function

    context = {
        'items': cart_data['cart_items'], # Naming convention 'items' for sidebar
        'total': cart_data['cart_total'],
        'cart_count': cart_data['cart_count'],
    }
    # Render the partial template for the cart sidebar content
    cart_html = render_to_string('dresses/partials/cart_sidebar_content.html', context, request=request)
    return JsonResponse({'cart_html': cart_html, 'cart_count': cart_data['cart_count']})


def cart_sidebar(request):
    # This view seems redundant with cart_sidebar_view.
    # If it's called via AJAX to update sidebar content, delegate to the more complete view.
    return cart_sidebar_view(request) # Delegate to the more complete view


# Removed @login_required to support anonymous cart
def add_to_cart(request, product_slug):
    if request.method == 'POST':
        product = get_object_or_404(Product, slug=product_slug)
        quantity = int(request.POST.get('quantity', 1))
        size = request.POST.get('size', None)

        if not product.is_unstitched and not size:
            return JsonResponse({'success': False, 'message': 'Please select a size.'}, status=400)

        # Check product stock (logic remains same, it's good)
        if not product.is_unstitched:
            if size:
                try:
                    product_stock = ProductStock.objects.get(product=product, size=size)
                    if product_stock.stock < quantity:
                        return JsonResponse({'success': False, 'message': f'Only {product_stock.stock} of {product.name} ({size}) left in stock.'}, status=400)
                except ProductStock.DoesNotExist:
                    return JsonResponse({'success': False, 'message': f'{product.name} ({size}) is out of stock or size not found.'}, status=400)
            else:
                return JsonResponse({'success': False, 'message': 'Please select a size for this product.'}, status=400)
        else:
            if product.stock < quantity:
                return JsonResponse({'success': False, 'message': f'Only {product.stock} of {product.name} left in stock.'}, status=400)

        # --- Handle cart for Authenticated vs. Anonymous users ---
        if request.user.is_authenticated:
            user_cart, created = Cart.objects.get_or_create(user=request.user)
            cart_item, created_item = CartItem.objects.get_or_create(
                cart=user_cart,
                product=product,
                size=size
            )
            if not created_item:
                cart_item.quantity += quantity
                cart_item.save()
            else:
                cart_item.quantity = quantity
                cart_item.save()
            user_cart.save() # Ensure cart is saved, especially if total_quantity/price properties are lazily updated

        else: # Anonymous user handling
            session_cart = request.session.get('cart', {})
            # Create a unique key for product + size combination
            item_key = f"{product.id}|{size if size else 'None'}"

            if item_key in session_cart:
                session_cart[item_key]['quantity'] += quantity
            else:
                session_cart[item_key] = {
                    'product_id': product.id,
                    'quantity': quantity,
                    'size': size,
                    'price': str(product.price) # Store Decimal as string to avoid precision issues in session
                }
            request.session['cart'] = session_cart
            request.session.modified = True # Crucial: Inform Django that session data has changed

        # Get updated cart data for response (works for both authenticated and anonymous)
        cart_data = get_cart_data(request)
        return JsonResponse({'success': True, 'message': 'Item added to cart!', 'cart_count': cart_data['cart_count']})

    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=400)


# Removed @login_required to support anonymous cart
def decrease_quantity(request, product_slug, size=None):
    product = get_object_or_404(Product, slug=product_slug)

    if request.user.is_authenticated:
        user_cart = get_object_or_404(Cart, user=request.user)
        # Determine the CartItem based on whether the product is unstitched or has a size
        if product.is_unstitched:
            cart_item = get_object_or_404(CartItem, cart=user_cart, product=product, size=None)
        else:
            if not size: # Size is mandatory for stitched products
                return JsonResponse({'success': False, 'error': 'Size is required to decrease quantity for this product.'})
            cart_item = get_object_or_404(CartItem, cart=user_cart, product=product, size=size)

        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
            messages.info(request, f"Quantity of {product.name} decreased to {cart_item.quantity}.")
        else:
            # If quantity is 1, remove the item
            cart_item.delete()
            messages.info(request, f"{product.name} removed from cart.")
        user_cart.save() # Ensure cart is saved to update related properties

    else: # Anonymous user handling
        session_cart = request.session.get('cart', {})
        item_key = f"{product.id}|{size if size else 'None'}"

        if item_key in session_cart:
            if session_cart[item_key]['quantity'] > 1:
                session_cart[item_key]['quantity'] -= 1
                messages.info(request, f"Quantity of {product.name} decreased.")
            else:
                del session_cart[item_key] # Remove item if quantity becomes 0
                messages.info(request, f"{product.name} removed from cart.")
            request.session['cart'] = session_cart
            request.session.modified = True
        else:
            return JsonResponse({'success': False, 'error': 'Item not found in your cart.'})

    # Recalculate cart count and render updated sidebar HTML
    cart_data = get_cart_data(request)
    cart_html = render_to_string(
        'dresses/partials/cart_sidebar_content.html', 
        {'items': cart_data['cart_items'], 'total': cart_data['cart_total']}, 
        request=request
    )
    return JsonResponse({'success': True, 'cart_count': cart_data['cart_count'], 'cart_html': cart_html})


# Removed @login_required to support anonymous cart
def remove_from_cart(request, product_slug, size=None):
    product = get_object_or_404(Product, slug=product_slug)

    if request.user.is_authenticated:
        user_cart = get_object_or_404(Cart, user=request.user)
        # Determine the CartItem based on whether the product is unstitched or has a size
        if product.is_unstitched:
            cart_item = get_object_or_404(CartItem, cart=user_cart, product=product, size=None)
        else:
            if not size: # Size is mandatory for stitched products
                return JsonResponse({'success': False, 'error': 'Size is required to remove this product.'})
            cart_item = get_object_or_404(CartItem, cart=user_cart, product=product, size=size)

        cart_item.delete()
        messages.info(request, f"{product.name} removed from cart.")
        user_cart.save() # Ensure cart is saved to update related properties

    else: # Anonymous user handling
        session_cart = request.session.get('cart', {})
        item_key = f"{product.id}|{size if size else 'None'}"

        if item_key in session_cart:
            del session_cart[item_key]
            messages.info(request, f"{product.name} removed from cart.")
            request.session['cart'] = session_cart
            request.session.modified = True
        else:
            return JsonResponse({'success': False, 'error': 'Item not found in your cart.'})

    # Recalculate cart count and render updated sidebar HTML
    cart_data = get_cart_data(request)
    cart_html = render_to_string(
        'dresses/partials/cart_sidebar_content.html', 
        {'items': cart_data['cart_items'], 'total': cart_data['cart_total']}, 
        request=request
    )
    return JsonResponse({'success': True, 'cart_count': cart_data['cart_count'], 'cart_html': cart_html})


@login_required
def address_view(request):
    try:
        address = ShippingAddress.objects.get(user=request.user)
    except ShippingAddress.DoesNotExist:
        address = None
    return render(request, 'dresses/address.html', {'address': address}) # Updated template path


@login_required
def add_address(request):
    try:
        address = ShippingAddress.objects.get(user=request.user)
        # If an address already exists, redirect to update it instead of adding a new one
        messages.info(request, "You already have a saved address. Please update it if needed.")
        return redirect('update_address') 
    except ShippingAddress.DoesNotExist:
        pass

    if request.method == 'POST':
        form = ShippingAddressForm(request.POST)
        if form.is_valid():
            shipping_address = form.save(commit=False)
            shipping_address.user = request.user
            shipping_address.save()
            messages.success(request, "Shipping address saved successfully!")
            return redirect('address_view') # Redirect to the address view page
        else:
            messages.error(request, "Please correct the errors in the address form.")
    else:
        form = ShippingAddressForm()

    context = {'form': form}
    return render(request, 'dresses/add_address.html', context) # Updated template path

@login_required
def update_address(request):
    address = get_object_or_404(ShippingAddress, user=request.user)

    if request.method == 'POST':
        form = ShippingAddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, "Shipping address updated successfully!")
            return redirect('address_view') # Redirect to the address view page
        else:
            messages.error(request, "Please correct the errors in the address form.")
    else:
        form = ShippingAddressForm(instance=address)
    
    context = {'form': form}
    return render(request, 'dresses/update_address.html', context) # Updated template path
def get_dynamic_price(request):

    product_id = request.GET.get('product_id')

    product = Product.objects.get(id=product_id)

    return JsonResponse({
        'price': float(product.dynamic_price)
    })
def ai_dashboard(request):

    products = Product.objects.all()

    total_products = products.count()

    total_orders = Order.objects.count()

    most_viewed = products.order_by('-product_views').first()

    most_sold = products.order_by('-sales_count').first()

    highest_price = products.order_by('-dynamic_price').first()

    lowest_price = products.order_by('dynamic_price').first()

    trending_products = products.order_by(
        '-sales_count',
        '-product_views'
    )[:5]

    # CHART DATA

    labels = []

    prices = []

    for product in products:

        labels.append(product.name)

        prices.append(
            float(product.dynamic_price or product.price)
        )

    context = {

        'total_products': total_products,

        'total_orders': total_orders,

        'most_viewed': most_viewed,

        'most_sold': most_sold,

        'highest_price': highest_price,

        'lowest_price': lowest_price,

        'trending_products': trending_products,

        # CHART

        'labels': labels,

        'prices': prices,
    }

    return render(
        request,
        'dashboard/ai_dashboard.html',
        context
    )

def dynamic_pricing(request):

    products = Product.objects.all().order_by('-sales_count')

    context = {
        'products': products
    }

    return render(
        request,
        'dashboard/dynamic_pricing.html',
        context
    )
def products_dashboard(request):
    return render(request, 'dashboard/products_dashboard.html')


def orders_dashboard(request):
    return render(request, 'dashboard/orders_dashboard.html')


def categories_dashboard(request):
    return render(request, 'dashboard/categories_dashboard.html')

def lock_discount(request, product_id):

    product = get_object_or_404(Product, id=product_id)

    product.discount_locked = True

    product.save()

    return redirect('dynamic_pricing')


def unlock_discount(request, product_id):

    product = get_object_or_404(Product, id=product_id)

    product.discount_locked = False

    product.save()

    return redirect('dynamic_pricing')
def toggle_discount_lock(request, product_id):

    product = get_object_or_404(Product, id=product_id)

    product.discount_locked = not product.discount_locked

    product.save()

    return redirect('dynamic_pricing')