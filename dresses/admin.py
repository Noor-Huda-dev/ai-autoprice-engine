from django.contrib import admin
from django.utils.html import format_html
from .models import Category, SubCategory, Product, Order, OrderItem, UserProfile, ShopInfo, Tag, ProductImage, ProductStock, ContactMessage, ShippingAddress

class ProductStockInline(admin.TabularInline):
    model = ProductStock
    extra = 1

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 4

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductStockInline, ProductImageInline] 
    list_display = ('name', 'price', 'fabric', 'category', 'stock','base_price','dynamic_price','product_views','sales_count')
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'image_tag')
    prepopulated_fields = {'slug': ('name',)}

    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 50px; height:auto;" />'.format(obj.image.url))
        return "-"
    image_tag.short_description = 'Image'

@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'slug', 'is_featured')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('category',)

class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'product_total', 'total_price']

admin.site.register(OrderItem)
admin.site.register(UserProfile)
admin.site.register(ShopInfo)
admin.site.register(Tag)
admin.site.register(ContactMessage)
admin.site.register(ShippingAddress)
admin.site.register(Order)