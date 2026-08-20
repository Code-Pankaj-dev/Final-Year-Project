from django.db import models
from django.contrib.auth.models import User


class ContactModel(models.Model):
    name = models.CharField(max_length=100)
    mob = models.CharField(max_length=15)
    email = models.EmailField()
    request_type = models.CharField(max_length=100)
    blood_group = models.CharField(max_length=10)
    msg = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.name


class DonateBloodModel(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    blood_group = models.CharField(max_length=10)
    weight = models.IntegerField()
    address = models.TextField()
    last_donation = models.DateField(null=True, blank=True)
    hemoglobin = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=60, default="Approved", blank=True)

    def __str__(self):
        return f"{self.name} ({self.blood_group})"


class RequestBloodModel(models.Model):
    blood_group = models.CharField(max_length=10)
    units_needed = models.IntegerField()
    urgency = models.CharField(max_length=20, default="Normal")
    patient_name = models.CharField(max_length=100)
    required_by = models.DateField()
    contact_phone = models.CharField(max_length=15)
    hospital_name = models.CharField(max_length=100)
    hospital_address = models.TextField()
    status = models.CharField(max_length=20, default="Pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient_name} - {self.blood_group} ({self.units_needed} units)"


class DonorRegisterModel(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    full_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=20)
    dob = models.DateField()
    age = models.IntegerField()
    blood_group = models.CharField(max_length=5)
    weight = models.IntegerField()
    mobile = models.CharField(max_length=10)
    email = models.EmailField()
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    address = models.TextField()
    last_donation = models.DateField(blank=True, null=True)
    hemoglobin = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    disease = models.CharField(max_length=50, blank=True, null=True, default="None")
    disease_details = models.TextField(blank=True, null=True, default="")
    medicine = models.CharField(max_length=50, blank=True, null=True, default="No")
    previous_donation = models.CharField(max_length=50, blank=True, null=True, default="No")
    status = models.CharField(max_length=20, default="Pending")
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.full_name


class LoginModel(models.Model):
    role = models.CharField(max_length=100)
    email = models.EmailField()
    password = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.email} ({self.role})"


class BloodStock(models.Model):
    BLOOD_GROUP_CHOICES = (
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    )
    blood_group = models.CharField(max_length=5, unique=True, choices=BLOOD_GROUP_CHOICES)
    units = models.PositiveIntegerField(default=10)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.blood_group}: {self.units} units"

    @property
    def status_level(self):
        if self.units >= 10:
            return 'high'
        elif self.units >= 5:
            return 'medium'
        else:
            return 'low'