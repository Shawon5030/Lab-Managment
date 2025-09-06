from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Lab, Category, Product, LoanRequest, LoanHistory

# =============================
# Custom User Admin
# =============================
class UserAdmin(BaseUserAdmin):
    # Fields to display in list view
    list_display = ('username', 'email', 'is_student', 'is_teacher', 'is_hod', 'second_layer_is_student','is_staff', 'is_active')
    list_filter = ('is_student', 'is_teacher', 'is_hod', 'is_staff', 'is_active')
    
    # Fields to edit in detail view
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role & Extra Info', {'fields': ('is_student','second_layer_is_student', 'is_teacher', 'is_hod', 'semester', 'department', 'roll_number')}),
    )

    # Fields available in create user page
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Role & Extra Info', {'fields': ('is_student', 'is_teacher', 'is_hod', 'semester', 'department', 'roll_number')}),
    )

admin.site.register(User, UserAdmin)


# =============================
# Lab Admin
# =============================
class LabAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
admin.site.register(Lab, LabAdmin)


# =============================
# Category Admin
# =============================
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'image_preview')
    search_fields = ('name',)
    
    # Show image preview in admin
    def image_preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" width="50" height="50" />'
        return '-'
    image_preview.allow_tags = True
    image_preview.short_description = 'Image'
    
admin.site.register(Category, CategoryAdmin)


# =============================
# Product Admin
# =============================
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'category', 'lab', 'status', 'in_stock', 'price', 'base_price')
    list_filter = ('status', 'category', 'lab', 'in_stock')
    search_fields = ('name', 'category__name', 'lab__name')
    
    # Optional: show image preview
    def image_preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" width="50" height="50" />'
        return '-'
    image_preview.allow_tags = True
    image_preview.short_description = 'Image'

admin.site.register(Product, ProductAdmin)


# =============================
# LoanRequest Admin
# =============================
class LoanRequestAdmin(admin.ModelAdmin):
    list_display = ('product', 'requested_by', 'for_student', 'status', 'request_date', 'approved_by', 'approved_date')
    list_filter = ('status', 'request_date', 'approved_date')
    search_fields = ('product__name', 'requested_by__username', 'for_student__username', 'approved_by__username')
    
admin.site.register(LoanRequest, LoanRequestAdmin)


# =============================
# LoanHistory Admin
# =============================
class LoanHistoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'borrower', 'taken_date', 'returned_date')
    list_filter = ('taken_date', 'returned_date')
    search_fields = ('product__name', 'borrower__username')

admin.site.register(LoanHistory, LoanHistoryAdmin)

from django.contrib import admin
from .models import ProductTransfer

@admin.register(ProductTransfer)
class ProductTransferAdmin(admin.ModelAdmin):
    list_display = (
        'product', 
        'from_lab', 
        'to_lab', 
        'quantity', 
        'transferred_by', 
        'transferred_at'
    )
    list_filter = ('from_lab', 'to_lab', 'transferred_at', 'transferred_by')
    search_fields = ('product__name', 'from_lab__name', 'to_lab__name', 'transferred_by__username')
    readonly_fields = ('transferred_at',)
    ordering = ('-transferred_at',)
