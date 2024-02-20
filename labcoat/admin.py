from django.contrib import admin
from .models import LabCoatInventory, LabCoatAddStock, LabCoatDistribution

@admin.register(LabCoatInventory)
class LabCoatInventoryAdmin(admin.ModelAdmin):
    list_display = ['size', 'total']
    readonly_fields = ('display_change_log',)

    def display_change_log(self, obj):
        log_entries = obj.change_log
        if log_entries:
            return '\n'.join([f"{entry['date']}: {entry['change']} ({entry['type']})" for entry in log_entries])
        return "No change log available."

    display_change_log.short_description = "Change Log"
    display_change_log.allow_tags = True

@admin.register(LabCoatAddStock)
class LabCoatAddStockAdmin(admin.ModelAdmin):
    list_display = ['size', 'quantity', 'date']

@admin.register(LabCoatDistribution)
class LabCoatDistributionAdmin(admin.ModelAdmin):
    list_display = ['user_id', 'name', 'size', 'quantity', 'date', 'recipient_type']
