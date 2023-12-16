from django.db import models

class LabCoatInventory(models.Model):
    SIZE_CHOICES = (
        ('S', 'Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
        ('XL', 'Extra Large'),
        ('XXL', 'Extra Extra Large'),
    )

    size = models.CharField(max_length=3, choices=SIZE_CHOICES, unique=True)
    total = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'Total {self.get_size_display()} Lab Coats in Inventory: {self.total}'
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Create an Inventoryupdate record with the new total
        InventoryUpdate.objects.create(
            size=self.size,
            quantity_update=self.total
        )
    
class InventoryUpdate(models.Model):
    SIZE_CHOICES = (
        ('S', 'Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
        ('XL', 'Extra Large'),
        ('XXL', 'Extra Extra Large'),
    )

    size = models.CharField(max_length=20, choices=LabCoatInventory.SIZE_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    quantity_update = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.get_size_display()} - {self.timestamp}"

    

class LabCoatAddStock(models.Model):
    size = models.CharField(max_length=3, choices=LabCoatInventory.SIZE_CHOICES)
    quantity = models.PositiveIntegerField()
    date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        inventory, created = LabCoatInventory.objects.get_or_create(size=self.size)
        inventory.total += self.quantity
        inventory.save()

class LabCoatDistribution(models.Model):
    RECIPIENT_CHOICES = [
        ('student', 'Student'),
        ('staff', 'Staff'),
    ]

    user_id = models.CharField(max_length=10)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    size = models.CharField(max_length=3, choices=LabCoatInventory.SIZE_CHOICES)
    recipient_type = models.CharField(max_length=7, choices=RECIPIENT_CHOICES)
    quantity = models.PositiveIntegerField()
    date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
    # Check if this is a new record or an update
        is_new = self._state.adding

        if is_new:
            # Try to get the existing inventory record
            try:
                inventory = LabCoatInventory.objects.get(size=self.size)
            except LabCoatInventory.DoesNotExist:
                raise ValueError(f"No inventory record found for size {self.size}")

            # Check if there are enough lab coats in the inventory
            if self.quantity > inventory.total:
                raise ValueError("Cannot distribute more lab coats than are in inventory")

            # Reduce the inventory count
            inventory.total = max(0, inventory.total - self.quantity)
            inventory.save()

        # Call the original save method
        super().save(*args, **kwargs)

