from django.db.models import fields
from django.shortcuts import render, redirect
from django.http.response import JsonResponse, HttpResponse
from django.views.generic import FormView
from django.urls import reverse
from django.conf import settings
from django.http.response import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import stripe
from django.contrib import messages
import bcrypt
from time import gmtime, localtime, strftime
from datetime import date, datetime
from .models import *
import ast

# payments/views.py

@csrf_exempt
def stripe_webhook(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    endpoint_secret = settings.STRIPE_ENDPOINT_SECRET
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        print("Payment was successful.")
        # TODO: run some custom code here

    return HttpResponse(status=200)

def SuccessView(request):
    return render(request, "success.html")


def CancelledView(request):
    return render(request, "cancelled.html")

@csrf_exempt
def create_checkout_session(request):
    if request.method == 'GET':
        domain_url = 'http://localhost:8000/'
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            # Create new Checkout Session for the order
            # Other optional params include:
            # [billing_address_collection] - to display billing address details on the page
            # [customer] - if you have an existing Stripe Customer ID
            # [payment_intent_data] - capture the payment later
            # [customer_email] - prefill the email input in the form
            # For full details see https://stripe.com/docs/api/checkout/sessions/create

            # ?session_id={CHECKOUT_SESSION_ID} means the redirect will have the session ID set as a query param
            checkout_session = stripe.checkout.Session.create(
                client_reference_id=request.user.id if request.user.is_authenticated else None,
                success_url=domain_url + 'success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=domain_url + 'cancelled/',
                payment_method_types=['card'],
                mode='payment',
                line_items=[
                    {
                        'name': 'T-shirt',
                        'quantity': 1,
                        'currency': 'usd',
                        'amount': '2000',
                    }
                ]
            )
            return JsonResponse({'sessionId': checkout_session['id']})
        except Exception as e:
            return JsonResponse({'error': str(e)})

# new
@csrf_exempt
def stripe_config(request):
    if request.method == 'GET':
        stripe_config = {'publicKey': settings.STRIPE_PUBLISHABLE_KEY}
        return JsonResponse(stripe_config, safe=False)

# Create your views here.
def index(request):
    context={
        "all_products": Product.objects.all(),
        "all_categories": Category.objects.all(),
        "all_stores": Store.objects.all(),
    }
    
    return render(request, "index.html", context)

def login_page(request):
    if "user_id" in request.session:
        return redirect ('/dashboard')

    return render(request, "login.html")

def login(request):
    if request.method == "POST":
        errors = User.objects.loginvalidation(request.POST)
        if errors:
            for error in errors.values():
                messages.error(request,error)
            return redirect('/login')
        email = request.POST['email']
        
        logged_user = User.objects.filter(email=email)
        logged_user = logged_user[0]
        if bcrypt.checkpw(request.POST['pw'].encode(), logged_user.password.encode()):
            request.session["user_id"] = logged_user.id
            request.session["username"] = f"{logged_user.first_name} {logged_user.last_name}"
            return redirect('/dashboard')
        else:
            messages.error(request, "Invalid password")
            return redirect('/login')


    
    return redirect('/login')

def register_page(request):

    return render(request, "register.html")

def register(request):
    if request.method == "POST":
        errors = User.objects.registervalidation(request.POST)
        if errors:
            for error in errors.values():
                messages.error(request,error)
            return redirect('/register')
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        password = bcrypt.hashpw(request.POST["pw"].encode(), bcrypt.gensalt()).decode()
        dob = request.POST['dob']
        address_1 = request.POST['address1']
        address_2 = request.POST['address2']
        city = request.POST['city']
        state = request.POST['state']
        zip = request.POST['zip']

        user = User.objects.create(first_name=first_name, last_name=last_name, email=email, password=password, dob=dob, address_1=address_1, address_2=address_2, city=city, state=state, zip=zip)
        request.session["user_id"] = user.id
        request.session["username"] = f"{user.first_name} {user.last_name}"
        return redirect('/dashboard')

    return redirect('/register')

def category(request, id):
    cat = Category.objects.get(id=id)
    context={
        "catproducts": cat.product.all(),
        "all_categories": Category.objects.all(),
        "category": cat,
    }

    return render(request, "category.html", context)

def product(request, id):
    productid = id
    productinfo = Product.objects.get(id=productid)
    if "user_id" not in request.session:
        context = {
        "product": productinfo,
        "all_categories": Category.objects.all(),
    }
        return render(request, "product.html", context)
    userid = request.session["user_id"]
    user = User.objects.get(id=userid) 
    context = {
        "product": productinfo,
        "all_categories": Category.objects.all(),
        "likes": productinfo.likes.filter(id=userid),
        "user": user,
    }

    return render(request, "product.html", context)

def addcat(request):
    if "user_id" not in request.session:
        return redirect ('/login')
    userid = request.session["user_id"]
    user = User.objects.get(id=userid)
    if user.level != 3:
        return redirect('/dashboard')
    if request.method == "POST":
        errors = User.objects.catvalidation(request.POST)
        if errors:
            for error in errors.values():
                messages.error(request,error)
            return redirect('/admin/add_product')
        name = request.POST['name']
        Category.objects.create(name=name)
        return redirect('/admin/add_product')

    return redirect('/admin')

def addcart(request):
    if "user_id" not in request.session:
        return redirect ('/login')
    if request.method == "POST":
        
        userid = request.session["user_id"]
        pid = request.POST['pid']
        quantity = int(request.POST['quantity'])
        user = User.objects.get(id=userid)
        product = Product.objects.get(id=pid)
        product.stock = product.stock - quantity
        product.save()
        name = product.name
        amount = product.amount
        pic = product.pic
        total = user.total


        for count in range(0, quantity):
            count += 1
            cart = Cart.objects.create(user=user, pid=pid, pic=pic, name=name, amount=amount)
            user.total = user.total + product.amount
            user.save()
            

    return redirect('/cart')

def removecart(request,id):
    if "user_id" not in request.session:
        return redirect ('/login')
    pid = id
    userid = request.session["user_id"]
    user = User.objects.get(id=userid)
    cart = user.usecart.all()
    product = Product.objects.get(id=pid)
    
    for item in cart:
        if item.pid == pid:
            rid = item.id
            removeitem = Cart.objects.get(id=rid)
            product.stock += 1
            product.save()
            user.total = user.total - product.amount
            user.save()
            removeitem.delete()
            return redirect('/cart')
    return redirect('/cart')

def cart(request):
    if "user_id" not in request.session:
        return redirect ('/login')
    
    userid = request.session["user_id"]
    user = User.objects.get(id=userid)
    subtotal = user.total
    tax = float(subtotal * .0825)
    shipping = float(5.00)
    total = float(subtotal + tax + shipping)

    context = {
        "all_categories": Category.objects.all(),
        "cart_products": user.usecart.all(),
        "user": user,
        "subtotal": subtotal,
        "shipping": shipping,
        "tax": tax,
        "total": total,
    }

    return render(request, "cart.html", context)

def likeditems(request):
    if "user_id" not in request.session:
        return redirect ('/login')
    userid = request.session["user_id"]
    user = User.objects.get(id=userid)
    context = {
        "liked_products": user.userlike.all(),
        "all_categories": Category.objects.all(),
    }


    return render(request, "like.html", context)

def likeitem(request):
    if "user_id" not in request.session:
        return redirect ('/login')
    userid = request.session["user_id"]
    user = User.objects.get(id=userid)
    if request.method == "POST":
        id = request.POST['postid']
        product = Product.objects.get(id=id)
        product.likes.add(user)

        return redirect(f'/product/{id}')
    return redirect('/')

def unlikeitem(request):
    if "user_id" not in request.session:
        return redirect ('/login')
    userid = request.session["user_id"]
    user = User.objects.get(id=userid)
    if request.method == "POST":
        id = request.POST['postid']
        product = Product.objects.get(id=id)
        product.likes.remove(user)

        return redirect(f'/product/{id}')
    return redirect('/')

def dashboard(request):
    if "user_id" not in request.session:
        return redirect ('/login')
    userid = request.session["user_id"]
    user = User.objects.get(id=userid)
    if user.level == 3:

        return redirect('/admin')
    if "user_id" not in request.session:
        return redirect ('/login')

    return render(request, "dashboard.html")

def accountinfo(request):
    if "user_id" not in request.session:
        return redirect ('/login')
    
    userid = request.session["user_id"]
    user = User.objects.get(id=userid)
    month = '{:02d}'.format(user.dob.month)
    day = '{:02d}'.format(user.dob.day)
    context = {
        "user": user,
        "month": month,
        "day": day,
    }

    return render(request, "accountinfo.html", context)

def accountupdate(request):
    if request.method == "POST":
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        password = bcrypt.hashpw(request.POST["new_pw"].encode(), bcrypt.gensalt()).decode()
        dob = request.POST['dob']
        address1 = request.POST['address1']
        address2 = request.POST['address2']
        city = request.POST['city']
        state = request.POST['state']
        zip = request.POST['zip']

        userid = request.session["user_id"]
        user = User.objects.get(id=userid)

        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.password = password
        user.dob = dob
        user.address_1 = address1
        user.address_2 = address2
        user.city = city
        user.state = state
        user.zip = zip
        user.save()
        return redirect('/dashboard/account')

    return redirect('/')

def recentorders(request):
    if "user_id" not in request.session:
        return redirect ('/login')

    userid = request.session["user_id"]
    user = User.objects.get(id=userid)
    userorders = user.userorders.all()
    context={
        "userorders": userorders,
    }

    return render(request, "recentorders.html", context)

def submitorder(request):
    if "user_id" not in request.session:
        return redirect ('/login')
    if request.method == "POST":
        userid = request.session["user_id"]
        user = User.objects.get(id=userid)
        
        subtotal = ast.literal_eval(request.POST['subtotal'])
        tax = ast.literal_eval(request.POST['tax'])
        shipping = ast.literal_eval(request.POST['shipping'])
        usercart = user.usecart.all()
        productlist = {"product":[]}
        total = float(subtotal + tax + shipping)

        for product in usercart:
            rid = product.id
            productid = Cart.objects.get(id=rid)
            pid = productid.pid
            orderproduct = Product.objects.get(id=pid)
            pamount = str("{:.2f}".format(orderproduct.amount))
            prodid = str(orderproduct.id)
            productlist["product"].append('Product ID: ' + prodid + ' - ' + orderproduct.name + " : " + pamount)
            destroyitem = Cart.objects.get(id=rid)
            destroyitem.delete()
        Order.objects.create(product=productlist, user=user, subtotal=subtotal, tax=tax, total=total, shipping=shipping)
        user.total = 0
        user.save()

        return redirect('/dashboard')

    return redirect('/')

def vieworder(request, id):
    if "user_id" not in request.session:
        return redirect ('/login')
    userid = request.session["user_id"]
    user = User.objects.get(id=userid)
    
    for order in user.userorders.all():
        if order.id == id:
            order = Order.objects.get(id=id)
            product_dict = ast.literal_eval(order.product)
            context = {
                "order":order,
                "productlist": product_dict,
            }
            return render(request, "vieworder.html", context)

    return redirect('/dashboard')

def admindash(request):
    if "user_id" not in request.session:
        return redirect ('/login')
    userid = request.session["user_id"]
    user = User.objects.get(id=userid)
    if user.level != 3:

        return redirect('/dashboard')

    return render(request, "admindashboard.html")

def adminneworders(request):
    if "user_id" not in request.session:
        return redirect ('/login')
    userid = request.session["user_id"]
    user = User.objects.get(id=userid)
    if user.level != 3:

        return redirect('/dashboard')
    context ={
        "orders":Order.objects.all(),
    }

    return render(request, "adminneworders.html", context)

def adminpastorders(request):
    if "user_id" not in request.session:
        return redirect ('/login')
    userid = request.session["user_id"]
    user = User.objects.get(id=userid)
    if user.level != 3:

        return redirect('/dashboard')
    context ={
        "orders":Order.objects.all(),
    }

    return render(request, "adminpastorders.html", context)

def adminvieworder(request, id):
    if "user_id" not in request.session:
        return redirect ('/login')
    userid = request.session["user_id"]
    user = User.objects.get(id=userid)
    if user.level != 3:

        return redirect('/dashboard')
    order = Order.objects.get(id=id)
    product_dict = ast.literal_eval(order.product)
    context = {
        "order": order,
        "productlist": product_dict,
    }

    return render(request, "adminvieworder.html", context)

def updatetracking(request):
    if "user_id" not in request.session:
        return redirect ('/login')
    userid = request.session["user_id"]
    user = User.objects.get(id=userid)
    if user.level != 3:

        return redirect('/dashboard')
    if request.method == "POST":
        tracking = request.POST['tracking']
        oid = request.POST['oid']
        order = Order.objects.get(id=oid)
        order.tracking = tracking
        order.save()

        return redirect(f'/admin/order/{oid}')

    return redirect('/admin')

def products(request):
    if "user_id" not in request.session:
        return redirect ('/login')
    userid = request.session["user_id"]
    user = User.objects.get(id=userid)
    if user.level != 3:

        return redirect('/dashboard')

    context = {
        "all_products": Product.objects.all(),
        "all_categories": Category.objects.all(),

    }

    return render(request, "products.html", context)

def addprod(request):
    if "user_id" not in request.session:
        return redirect ('/login')
    userid = request.session["user_id"]
    user = User.objects.get(id=userid)
    if user.level != 3:

        return redirect('/dashboard')
    context = {
        'all_categories': Category.objects.all(),
    }
    return render(request, "addproduct.html", context)

def addingprod(request):
    if "user_id" not in request.session:
        return redirect ('/login')
    userid = request.session["user_id"]
    user = User.objects.get(id=userid)
    if user.level != 3:

        return redirect('/dashboard')
    if request.method == "POST":
        errors = Product.objects.createproduct(request.POST)
        if errors:
            for error in errors.values():
                messages.error(request,error)
            return redirect('/admin/add_product')
        name = request.POST['name']
        desc = request.POST['desc']
        amount = request.POST['amt']
        pic = request.POST['pic']
        stock = request.POST['stock']
        

        product = Product.objects.create(name=name, desc=desc, amount=amount, pic=pic, stock=stock)
        categories = request.POST.getlist('categories')
        for category in categories:
            product.categories.add(category)

        return redirect(f'/product/{product.id}')
    return redirect('/admin/products')

def editprod(request, id):
    if "user_id" not in request.session:
        return redirect ('/login')
    userid = request.session["user_id"]
    user = User.objects.get(id=userid)
    if user.level != 3:

        return redirect('/dashboard')
    product = Product.objects.get(id=id)
    thesecats = product.categories.all()
    context = {
        "product": product,
        "excats": Category.objects.exclude(product=id),
        "currentcats": thesecats,
    }

    return render(request, "editproduct.html", context)

def edittingprod(request):
    if request.method == "POST":
        name = request.POST['name']
        desc = request.POST['desc']
        amount = request.POST['amt']
        pic = request.POST['pic']
        stock = request.POST['stock']
        id = request.POST['pid']
        all_categories = Category.objects.all()
        product = Product.objects.get(id=id)
        
        for category in all_categories:
            product.categories.remove(category)

        categories = request.POST.getlist('categories')
        
        for newcategory in categories:
            product.categories.add(newcategory)
        
        
        product.name = name
        product.desc = desc
        product.amount = amount
        product.pic = pic
        product.stock = stock
        product.save()


        return redirect(f'/admin/product/edit/{id}')
    return redirect('/')

def storeinfo(request):
    if "user_id" not in request.session:
        return redirect ('/login')
    userid = request.session["user_id"]
    user = User.objects.get(id=userid)
    if user.level != 3:

        return redirect('/dashboard')

    context = {
        "store": Store.objects.all()
    }

    return render(request, "store.html", context)

def createstore(request):
    if request.method == "POST":
        name = request.POST['storename']
        address1 = request.POST['address1']
        address2 = request.POST['address2']
        city = request.POST['city']
        state = request.POST['state']
        zip = request.POST['zip']
        Store.objects.create(name=name, address_1=address1, address_2=address2, city=city, state=state, zip=zip)
        return redirect('/admin/store')
    return redirect('/')

def editstore(request):
    if request.method == "POST":
        name = request.POST['storename']
        address1 = request.POST['address1']
        address2 = request.POST['address2']
        city = request.POST['city']
        state = request.POST['state']
        zip = request.POST['zip']
        storeid = request.POST['storeid']
        store = Store.objects.get(id=storeid)
        store.name = name
        store.address_1 = address1
        store.address_2 = address2
        store.city = city
        store.state = state
        store.zip = zip
        store.save()
        return redirect('/admin/store')

    return redirect('/')

def logout(request):
    request.session.flush()
    return redirect('/')