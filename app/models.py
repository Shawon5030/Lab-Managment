from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone


# Custom User Model
class User(AbstractUser):
    is_student = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)
    is_hod = models.BooleanField(default=False)
    second_layer_is_student = models.BooleanField(default=False)

    # Only for Student
    semester = models.CharField(max_length=20, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    roll_number = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        role = "Teacher" if self.is_teacher else "Student" if self.is_student else "HOD"
        return f"{self.username} ({role})"

# Lab Model
class Lab(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    capacity = models.IntegerField(default=0, null=True, blank=True)
    image = models.ImageField(upload_to='labs', null=True, blank=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    in_charge = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='labs_incharge')
    
    def __str__(self):
        return self.name

# Category Model
class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='category', null=True, blank=True)

    def __str__(self):
        return self.name

# Product Model
class Product(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('pending', 'Pending'),
        ('in_loan', 'In Loan'),
        ('returned', 'Returned')
    ]

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='products', null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    base_price = models.DecimalField(max_digits=10,null=True, blank=True ,decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    lab = models.ForeignKey(Lab, on_delete=models.CASCADE, related_name='products')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    serial_number = models.CharField(max_length=100, blank=True, null=True)
    in_stock = models.BooleanField(default=True)

    def __str__(self):
        return self.name

# LoanRequest Model
class LoanRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='requests_made')
    for_student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='requests_received', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    request_date = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='requests_approved')
    approved_date = models.DateTimeField(null=True, blank=True)
    return_date = models.DateField(null=True, blank=True)
    return_status = models.BooleanField(default=False,null=True, blank=True)
    rejection_reason = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        if self.for_student:
            return f"{self.product.name} for {self.for_student.username} ({self.status})"
        return f"{self.product.name} by {self.requested_by.username} ({self.status})"

# LoanHistory Model
class LoanHistory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    borrower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    taken_date = models.DateTimeField(default=timezone.now)
    returned_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.product.name} borrowed by {self.borrower.username}"


class ProductTransfer(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    from_lab = models.ForeignKey(Lab, on_delete=models.CASCADE, related_name="transfers_out")
    to_lab = models.ForeignKey(Lab, on_delete=models.CASCADE, related_name="transfers_in")
    quantity = models.PositiveIntegerField(default=1)  # যদি future এ multiple item থাকে
    transferred_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transfers_made"
    )
    transferred_at = models.DateTimeField(auto_now_add=True)
    return_product = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.product.name} from {self.from_lab.name} to {self.to_lab.name} on {self.transferred_at.date()}"

