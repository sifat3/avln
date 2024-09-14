from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum, F


class Other_cost(models.Model):
    amount = models.FloatField(default=0)
    reason = models.TextField(blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)


class Company(models.Model):
    a3_paper = models.PositiveIntegerField(default=0)
    a4_paper = models.PositiveIntegerField(default=0)
    white_ink = models.PositiveIntegerField(default=0)
    black_ink = models.PositiveIntegerField(default=0)
    cyan_ink = models.PositiveIntegerField(default=0)
    magenda_ink = models.PositiveIntegerField(default=0)
    yellow_ink = models.PositiveIntegerField(default=0)
    total_due_vendors = models.FloatField(default=0)
    profit = models.FloatField(default=0)
    waste = models.FloatField(default=0)
    cost = models.FloatField(default=0)
    investment = models.FloatField(default=0)
    total_profit = models.FloatField(default=0)


class Product(models.Model):
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=100)
    GSM = models.IntegerField()
    buying_price = models.FloatField()
    available = models.IntegerField()
    price = models.FloatField(default=0)
    SIZE_CHOICES = [
        ("S", "S"),
        ("M", "M"),
        ("L", "L"),
        ("XL", "XL"),
        ("XXL", "XXL"),
        ("XXXL", "XXXL"),
    ]
    size = models.CharField(max_length=5, choices=SIZE_CHOICES, default=0)

    def __str__(self) -> str:
        return self.name + " - " + self.color + " - " + self.size
    
total_price = Product.objects.aggregate(total=Sum(F('buying_price')*F('available')))['total']

class Profile(models.Model):
    ROLE_CHOICES = [
        ('vendor', 'Vendor'),
        ('manager', 'Manager'),
        ('operator', 'Operator'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='vendor')
    is_verified = models.BooleanField(default=False)  # For vendors needing verification
    verification_applied = models.BooleanField(default=False)
    name = models.CharField(max_length=100, blank=True, null=True)
    brand_name = models.CharField(max_length=1000, blank=True, null=True)
    page_link = models.CharField(max_length=2000, blank=True, null=True)
    nid = models.FileField(upload_to='upload', blank=True, null=True)
    profit = models.FloatField(default=0)
    due = models.FloatField(default=0)
    mobile_banking = models.CharField(max_length=200, null=True, blank=True)
    mobile_banking_number = models.IntegerField(null=True, blank=True)
    total_profit = models.FloatField(default=0)
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    


class Order(models.Model):

    vendor = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # One product per order
    quantity = models.PositiveIntegerField()
    front_print = models.CharField(max_length=10, null=True, blank=True)
    front_design = models.ImageField(upload_to='upload', null=True, blank=True)
    back_print = models.CharField(max_length=10, null=True, blank=True)
    back_design = models.ImageField(upload_to='upload', null=True, blank=True)
    mockup_front = models.ImageField(upload_to='upload', null=True, blank=True)
    mockup_back = models.ImageField(upload_to='upload', null=True, blank=True)
    order_date = models.DateTimeField(auto_now_add=True)
    is_printed = models.BooleanField(default=False)
    is_shipped = models.BooleanField(default=False)
    is_cancel = models.BooleanField(default=False)
    advance_amount = models.FloatField(default=0)
    advance_paid = models.BooleanField(default=False)
    order_confirmed = models.BooleanField(default=False)
    payment_id = models.CharField(max_length=500, blank=True, null=True)
    collection_amount = models.FloatField(default=0)
    cost = models.FloatField(default=0)
    vendor_profit = models.FloatField(default=0)
    profit = models.FloatField(default=0)
    customer_name = models.CharField(max_length=1000, blank=True, null=True)
    customer_full_address = models.CharField(max_length=1000, blank=True, null=True)
    customer_city = models.CharField(max_length=1000, blank=True, null=True)
    customer_phone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"Order {self.id} by {self.vendor.username} for {self.product.name}"
