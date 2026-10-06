from django.db import models


class Employee(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    department = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    joining_date = models.DateField()

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Asset(models.Model):
    STATUS_CHOICES = [
        ('Available', 'Available'),
        ('Assigned', 'Assigned'),
        ('Maintenance', 'Maintenance'),
        ('Retired', 'Retired'),
    ]

    asset_name = models.CharField(max_length=150)
    asset_code = models.CharField(max_length=50, unique=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    brand = models.CharField(max_length=100)
    purchase_date = models.DateField()
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Available'
    )

    def __str__(self):
        return self.asset_name


class Assignment(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.PROTECT)
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT)
    assigned_date = models.DateField()
    returned_date = models.DateField(null=True, blank=True)
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"{self.asset.asset_name} - {self.employee.name}"


class Maintenance(models.Model):
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('Retired', 'Retired'),
    ]

    asset = models.ForeignKey(Asset, on_delete=models.PROTECT)
    issue = models.TextField()
    reported_date = models.DateField()
    repair_date = models.DateField(null=True, blank=True)
    repair_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Open'
    )
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"{self.asset.asset_name} - {self.status}"