from django.contrib import admin
from .models import LabCoatInventory, InventoryUpdate, LabCoatAddStock, LabCoatDistribution

# Register your models with the admin site

@admin.register(LabCoatInventory)
class LabCoatInventoryAdmin(admin.ModelAdmin):
    list_display = ('size', 'total')
    list_filter = ('size',)
    search_fields = ('size',)

@admin.register(InventoryUpdate)
class InventoryUpdateAdmin(admin.ModelAdmin):
    list_display = ('size', 'quantity_update', 'timestamp')
    list_filter = ('size', 'timestamp', 'quantity_update')
    search_fields = ('size', 'quantity_update')

@admin.register(LabCoatAddStock)
class LabCoatAddStockAdmin(admin.ModelAdmin):
    list_display = ('size', 'quantity', 'date')
    list_filter = ('size', 'date')
    search_fields = ('size',)

@admin.register(LabCoatDistribution)
class LabCoatDistributionAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'name', 'email', 'size', 'recipient_type', 'quantity', 'date')
    list_filter = ('size', 'recipient_type', 'date')
    search_fields = ('user_id', 'name', 'email', 'size', 'recipient_type')

