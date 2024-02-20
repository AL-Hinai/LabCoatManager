from django.db import models
import datetime

class LabCoatInventory(models.Model):
    SIZE_CHOICES = (
        ('S', 'Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
        ('XL', 'Extra Large'),
        ('XXL', '2X Large'),
        ('XXXL', '3X Large'),
        ('XXXXL', '4X Large'),
    )

    size = models.CharField(max_length=6, choices=SIZE_CHOICES, unique=True)
    change_log = models.JSONField(default=list)  # Stores the log of changes

    def calculate_total(self):
        add_stock_total = LabCoatAddStock.objects.filter(size=self.size).aggregate(total=models.Sum('quantity'))['total'] or 0
        distribution_total = LabCoatDistribution.objects.filter(size=self.size).aggregate(total=models.Sum('quantity'))['total'] or 0
        return add_stock_total - distribution_total

    @property
    def total(self):
        return self.calculate_total()

    def __str__(self):
        return f'{self.get_size_display()} - Total in Inventory: {self.total}'

    def log_change(self, change, change_type):
        self.change_log.append({
            'date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'change': change,
            'type': change_type
        })
        self.save()

class LabCoatAddStock(models.Model):
    size = models.CharField(max_length=6, choices=LabCoatInventory.SIZE_CHOICES)
    quantity = models.PositiveIntegerField()
    date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Check if a LabCoatInventory object exists for the current size
        if not LabCoatInventory.objects.filter(size=self.size).exists():
            # If not, create a new LabCoatInventory object
            LabCoatInventory.objects.create(size=self.size)
        super().save(*args, **kwargs)



class LabCoatDistribution(models.Model):
    RECIPIENT_CHOICES = [
        ('student', 'Student'),
        ('staff', 'Staff'),
    ]

    user_id = models.CharField(max_length=10)
    name = models.CharField(max_length=255)
    size = models.CharField(max_length=6, choices=LabCoatInventory.SIZE_CHOICES)
    recipient_type = models.CharField(max_length=7, choices=RECIPIENT_CHOICES)
    quantity = models.PositiveIntegerField()
    date = models.DateField()


