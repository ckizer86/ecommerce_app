from django.db import models
from time import gmtime, localtime, strftime
from datetime import date, datetime
import re, bcrypt

# Create your models here.

class Validators(models.Manager):
    def registervalidation(self, postData):
        errors = {}
        all_users = User.objects.all()
        dob = postData['dob']
        today = str(date.today())
        comptoday = date.today()
        year = comptoday.year - 18
        month = '{:02d}'.format(comptoday.month)
        day = '{:02d}'.format(comptoday.day)
        age = f"{year}-{month}-{day}"
        if len(postData['first_name']) < 2:
            errors['first_name'] = "First name must be more than two characters"
        if len(postData['last_name']) < 2:
            errors['last_name'] = "Last name must be more than two characters"
        if len(postData['pw']) < 8:
            errors['pw_length'] = "Password must contain at least eight characters"
        if postData['pw'] != postData['confirm_pw']:
            errors['pw_mismatch'] = "Passwords do not match"
        if postData['dob'] == "":
            errors['dob_empty'] = "You must enter a date of birth"
        if postData['address1'] == "":
            errors['address1'] = "First address line can not be empty"
        if postData['city'] == "":
            errors['city'] = "City can not be empty"
        if postData['state'] == "":
            errors['state'] = "You must select a state"
        if postData['zip'] == "":
            errors['zip'] = "Zipcode can not be empty"
        name_regex = re.compile(r'^[a-zA-Z]')
        if not name_regex.match(postData['first_name']):
            errors['first_name_letters'] = "First name can only contain letters"
        if not name_regex.match(postData['last_name']):
            errors['last_name_letters'] = "Last name can only contain letters"
        EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
        if not EMAIL_REGEX.match(postData['email']):
            errors['email_format'] = "Invalid email address"
        for user in all_users:
            if postData['email'] == user.email:
                errors['email_unique'] = "Email already exists"
        if postData['dob'] > str(today):
            errors['dob_past'] = "Date of Birth must be in the past"
        if dob > age:
            errors['dob2'] = "Must be 18 years or older"

        return errors

    def loginvalidation(self, postData):
        errors={}
        email = postData['email']
        pw = postData['pw']
        if email == "":
            errors['email_empty'] = "You must enter an email"
            return errors
        logged_user = User.objects.filter(email=email)
        user = logged_user[0]
        
        if not user:
            errors['email'] = "Invalid email"
            return errors
        if postData['pw'] == "":
            print(user.password)
            errors['pw_empty'] = "You must enter a password"
            return errors

        return errors

    def catvalidation(self, postData):
        errors={}
        category = postData['name']
        if category == "":
            errors['cat'] = "You can not create an unnamed cateogry"

        return errors

    def createproduct(self, postData):
        errors={}
        name = postData['name']
        img = postData['pic']
        stock = postData['stock']
        amount = postData['amt']

        if name == "":
            errors['name'] = "Product name can not be empty."
        for pname in Product.objects.all():
            if name == pname.name:
                errors['unique'] = "Product name already exists."
        if img == "":
            errors['img'] = "You must enter an image link."
        if stock == "":
            errors['stock'] = "You must enter a stock amount."
        if amount == "":
            errors['amount'] = "You must enter a price for the product."

        return errors

class User(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    level = models.IntegerField(max_length=1, default=1)
    dob = models.DateField()
    address_1 = models.CharField(max_length=255)
    address_2 = models.CharField(max_length=255, default="")
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    zip = models.IntegerField(max_length=5)
    total = models.FloatField(null=True, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = Validators()
    #useraddress
    #userorders
    #userlike
    #usecart

class Product(models.Model):
    name = models.CharField(max_length=255)
    desc = models.TextField()
    amount = models.FloatField(max_length=25)
    pic = models.CharField(max_length=255, default="")
    likes = models.ManyToManyField(User, related_name="userlike")
    stock = models.IntegerField()
    cart = models.ManyToManyField(User, related_name="renamedcart")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = Validators()
    #categories
    #orders
    #productincart

class Category(models.Model):
    name = models.CharField(max_length=255)
    product = models.ManyToManyField(Product, related_name="categories")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Order(models.Model):
    product = models.TextField()
    user = models.ForeignKey(User, related_name="userorders", on_delete = models.CASCADE)
    tracking = models.CharField(max_length=255, default="")
    subtotal = models.FloatField(default=0)
    tax = models.FloatField(default=0)
    total = models.FloatField(default=0)
    shipping = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
class Store(models.Model):
    name = models.CharField(max_length=255)
    address_1 = models.CharField(max_length=255)
    address_2 = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    zip = models.IntegerField(max_length=5)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Cart(models.Model):
    user = models.ForeignKey(User, related_name="usecart", on_delete = models.CASCADE)
    pid = models.IntegerField(default=0)
    pic = models.CharField(max_length=255, default="")
    name = models.CharField(max_length=255)
    amount = models.FloatField(null = True, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
