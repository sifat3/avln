from calendar import monthrange
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from .forms import *
from django.contrib import messages
from .models import *
from datetime import datetime
import os
from datetime import datetime, timedelta
from django.core.wsgi import get_wsgi_application
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpResponseRedirect
from django.urls import reverse



month = datetime.now().strftime('%B').upper()
current_day_of_month = datetime.now().strftime('%d')

today = timezone.now().date()
last_day = monthrange(today.year, today.month)[1]
var = today.day == last_day


@login_required(login_url='login')
def clear_backend(request):
    
    if request.user.profile.role == 'manager':
        # deleting company info
        company = Company.objects.first()
        if company:
            company.total_profit += company.profit
            company.profit = 0
            company.waste = 0
            company.cost = 0
            company.save()
        # deleting vendor info
        vendors = Profile.objects.filter(role='vendor')
        for vendor in vendors:
            vendor.total_profit += vendor.profit
            vendor.profit = 0
            vendor.save()
        # deleting old orders
        seven_days_ago = timezone.now() - timedelta(days=7)
        Order.objects.filter(is_shipped=True, order_date__lte=seven_days_ago).delete()
        Order.objects.filter(is_cancel=True, order_date__lte=seven_days_ago).delete()

    return HttpResponseRedirect(reverse('manager'))


@login_required(login_url='login')
def adminpanel(request):
    if request.user.profile.role == 'vendor':
        messages.error(request, "You do not have permission to view this page.")
        return redirect('user_panel')
    orders = Order.objects.all()
    company = Company.objects.get(id=1)
    products = Product.objects.all()
    pending_vendors = Profile.objects.filter(is_verified=False, verification_applied=True)

    if request.method == "POST":
        if request.POST['query'] == "product":
            product = Product.objects.get(id=request.POST['product_id'])
            quantity = int(request.POST['quantity'])
            product.available += quantity
            # company.cost += quantity * product.buying_price
            # company.profit -= quantity * product.buying_price
            product.save()
            company.save()
        elif request.POST['query'] == "paper":
            if request.POST['product_id'] == 'a3':
                quantity = int(request.POST['quantity'])
                company.a3_paper += quantity
                company.cost += quantity * 30
                company.profit -= quantity * 30
            elif request.POST['product_id'] == 'a4':
                quantity = int(request.POST['quantity'])
                company.a4_paper += quantity
                company.cost += quantity * 15
                company.profit -= quantity * 15
            company.save()
        elif request.POST['query'] == "ink":
            if request.POST['product_id'] == 'white':
                company.white_ink += 1
            elif request.POST['product_id'] == 'black':
                company.black_ink += 1
            elif request.POST['product_id'] == 'cyan':
                company.cyan_ink += 1
            elif request.POST['product_id'] == 'magenta':
                company.magenda_ink += 1
            elif request.POST['product_id'] == 'yellow':
                company.yellow_ink += 1
            company.save()
        elif request.POST['query'] == 'cost':
            amount = float(request.POST['amount'])
            reason = request.POST['reason']
            cost = Other_cost.objects.create(amount=amount, reason=reason)
            company.profit -= amount
            company.cost += amount
            company.save()
            cost.save()
        return HttpResponseRedirect(reverse('manager'))

    total_price = 0
    for product in Product.objects.all():
        total_price += product.buying_price*product.available

    investment_left = company.investment - total_price 

    context = {
        'orders': orders,
        'company': company,
        'products': products,
        'investment_left' : investment_left,
        'month': month,
        'pending_vendors': pending_vendors,
        'var': var,
    }

    return render(request, 'core/admin.html', context)

@login_required(login_url='login')
def due_list(request):

    dues = Profile.objects.filter(due__gt=0)

    return render(request, 'core/due.html', {'dues': dues})

@login_required(login_url='login')
def paid(request, pk):
    vendor = Profile.objects.get(id=pk)
    due = vendor.due
    vendor.due = 0
    vendor.profit += due
    company = Company.objects.get(id=1)
    company.total_due_vendors -= due
    company.save()
    vendor.save()
    subject = "Payment from AVLN"
    message = f"Dear Vendor, We cleared your due of {due} TAKA, via {vendor.mobile_banking} Number: 0{vendor.mobile_banking_number}."
    from_email = settings.EMAIL_HOST_USER
    recipient = [vendor.user.email]
    send_mail(subject, message, from_email, recipient_list=recipient)
    return redirect('due_list')


@login_required(login_url='login')
def shipped(request, pk):
    order = Order.objects.get(id=pk)
    order.is_printed = False
    order.is_shipped = True
    company = Company.objects.get(id=1)
    company.profit += order.profit
    order.vendor.profile.due += order.vendor_profit
    company.total_due_vendors += order.vendor_profit
    order.save()
    order.vendor.profile.save()
    company.save()
    messages.success(request, "Status Changed to SHIPPED")
    subject = f"Order ID: 00{pk} has been Shipped"
    message = f"Dear Vendor, We shipped your order: 00{pk}, Your profit: {order.vendor_profit} TAKA should be added to the due. Thank you."
    from_email = settings.EMAIL_HOST_USER
    recipient = [order.vendor.email]
    send_mail(subject, message, from_email, recipient_list=recipient)
    return redirect('manager')

@login_required(login_url='login')
def printed(request, pk):
    order = Order.objects.get(id=pk)
    company = Company.objects.get(id=1)
    a3 = 0
    a4 = 0
    if order.front_print:
        if order.front_print.lower() == 'a3':
            a3 += 1
        elif order.front_print.lower() == 'a4':
            a4 += 1

    if order.back_print:
        if order.back_print.lower() == 'a3':
            a3 += 1
        elif order.back_print.lower() == 'a4':
            a4 += 1

    a3 *= order.quantity
    a4 *= order.quantity
    company.a3_paper -= a3
    company.a4_paper -= a4
    order.order_confirmed = False
    order.is_printed = True

    order.save()
    company.save()
    messages.success(request, "Status Changed to PRINTED")
    return redirect('manager')



def userpanel(request):
    orders = Order.objects.all()
    if request.method == 'POST':
        name = request.POST['name']
        brand_name = request.POST['brand_name']
        page_link = request.POST['page_link']
        nid = request.FILES['nid']
        mobile_banking = request.POST['mobile_banking']
        mobile_banking_number = request.POST['mobile_banking_number']
        user = request.user.profile
        user.name = name
        user.brand_name = brand_name
        user.page_link = page_link
        user.nid = nid
        user.mobile_banking = mobile_banking
        user.mobile_banking_number = mobile_banking_number
        user.verification_applied = True
        user.save()
        subject = "Request for verification Submitted!"
        message = f"Dear User, Thank you for taking the time to verify. We will review your application and active your panel as soon as possible. Thank you!"
        from_email = settings.EMAIL_HOST_USER
        recipient = [request.user.email]
        send_mail(subject, message, from_email, recipient_list=recipient)
        return redirect('user_panel')
        

    return render(request, 'core/user.html', {"orders": orders, 'month': month})


def vendor_register(request):
    if request.method == 'POST':
        username = request.POST['username']
        password1 = request.POST['password']
        password2 = request.POST['password2']
        email = request.POST['email']
        if User.objects.filter(username=username).exists():
            messages.error(request, "User Exists")
            return redirect('vendor_register')
        else:
            if password1 == password2:
                user = User.objects.create_user(username=username, email=email, password=password1)
                user.profile.role = 'vendor'
                user.profile.save()
                login(request, user)
                subject = "Welcome to AVLN"
                message = f"Dear User, Thank you for registering with us. We request you to provide the extra informations listed on your panel to make you verified."
                from_email = settings.EMAIL_HOST_USER
                recipient = [user.email]
                send_mail(subject, message, from_email, recipient_list=recipient)
                return redirect('user_panel')
            else:
                messages.error(request, "Passwords don't match")
                return redirect('vendor_register')

    return render(request, 'core/register.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('user_panel')
        else:
            messages.error(request, 'Invalid credentials')
            return redirect('login')
        
    return render(request, 'core/login.html')


@login_required(login_url='login')
def logout_view(request):
    logout(request)
    return redirect('user_panel')


@login_required(login_url='login')
def place_single_order(request):
    products = Product.objects.all()

    if request.method == 'POST':
        vendor = request.user
        product = Product.objects.get(id=request.POST['product'])
        quantity = request.POST['quantity']
        front_print = request.POST['front_print']
        if 'front_design' in request.FILES:
            front_design = request.FILES['front_design']
        else:
            front_design = None
        if 'back_design' in request.FILES:
            back_design = request.FILES['back_design']
        else:
            back_design = None
        if 'back_print' in request.POST:
            back_print = request.POST['back_print']
        else:
            back_print = None
        # back_print = request.POST['back_print']
        if 'mockup_front' in request.FILES:
            mockup_front = request.FILES['mockup_front']
        else:
            mockup_front = None
        if 'mockup_back' in request.FILES:
            mockup_back = request.FILES['mockup_back']
        else:
            mockup_back = None
        cost = 0
        profit = 0
        cost += product.price
        profit += 30
        if front_print:
            if front_print.lower() == 'a3':
                 cost += 80
                 profit += 40
            else:
                cost += 50
                profit += 25
        if back_print:
            if back_print.lower() == 'a3':
                cost += 80
                profit += 40
            else:
                cost += 50
                profit += 25
        if front_print and back_print:
            cost += 15
            profit += 15
        elif front_print or back_print:
            cost += 10
            profit += 10
        else:
            messages.error(request, 'Please Choose at least one print.')
            return redirect('place_single_order')

        quantity = int(quantity)
        cost = cost * quantity
        profit = profit * quantity
        collection_amount = float(request.POST['collection_amount'])
        customer_name = request.POST['customer_name']
        customer_full_address = request.POST['customer_full_address']
        customer_city = request.POST['customer_city']
        customer_phone = request.POST['customer_phone']
        if customer_city.lower() == 'dhaka':
            cost += 70
        else:
            cost += 120
        
        advance_amount = cost * 0.3

        vendor_profit = collection_amount - cost

        if cost > collection_amount:
            messages.error(request, "Collection amount is less than Total Cost")
            return redirect('place_single_order')
        else:
            if product.available >= quantity:
                order = Order.objects.create(vendor=vendor, product=product, quantity=quantity, front_design=front_design, front_print=front_print, back_design=back_design, back_print=back_print, mockup_back=mockup_back, mockup_front=mockup_front, customer_name=customer_name, customer_full_address=customer_full_address, customer_city=customer_city, customer_phone=customer_phone, collection_amount=collection_amount)
                product.available -= quantity
                product.save()
                order.cost = cost
                order.advance_amount = advance_amount
                order.vendor_profit = vendor_profit
                order.profit = profit
                order.save()
                subject = "Order placed!"
                message = f"Dear Vendor, Your order: 00{order.id} has been successfully placed. Please pay the advanced payment to confirm your order."
                from_email = settings.EMAIL_HOST_USER
                recipient = [vendor.email]
                send_mail(subject, message, from_email, recipient_list=recipient)
                return redirect('order_confirm', order.id)
            else:
                messages.error('quantity', 'Not enough stock available for this product.')
                return redirect('place_single_order')


    return render(request, 'core/place_order.html', {'products':products})


@login_required(login_url='login')
def order_confirm(request, pk):
    order = Order.objects.get(id=pk)
    if request.method == 'POST':
        payment_id = request.POST['payment_id']
        order.payment_id = payment_id
        order.advance_paid = True
        order.save()
        return redirect('order_confirm', pk)
    return render(request, 'core/confirm.html', {'order': order})

@login_required(login_url='login')
def order_verify(request, pk):
    order = Order.objects.get(id=pk)
    order.order_confirmed = True
    order.save()
    return redirect('manager')

@login_required(login_url='login')
def order_cancel(request, pk):
    order = Order.objects.get(id=pk)
    product = order.product
    company = Company.objects.get(id=1)
    if order.is_printed or order.is_shipped:
        messages.error(request, "Sorry, order can't be cancelled.")
        return redirect('user_panel')
    else:
        if order.order_confirmed == True:
            order.vendor.profile.due += order.advance_amount
            company.total_due_vendors += order.advance_amount
        order.is_cancel = True
        order.order_confirmed = False
        product.available += order.quantity
        product.save()
        order.save()
        company.save()
        order.vendor.profile.save()

    messages.error(request, "Order cancelled.")
    return redirect('user_panel')

@login_required(login_url='login')
def order_details(request, pk):
    order = Order.objects.get(id=pk)

    return render(request, 'core/order_details.html', {'order': order})



@login_required(login_url='login')
def update_profile(request):
    profile = request.user.profile 

    if profile.role != 'vendor':

        messages.error(request, "You do not have permission to update the profile.")
        return redirect('home')

    if request.method == 'POST':
        name = request.POST.get('name')
        brand_name = request.POST.get('brand_name')
        page_link = request.POST.get('page_link')
        mobile_banking = request.POST.get('mobile_banking')
        mobile_banking_number = request.POST.get('mobile_banking_number')

        # Update profile fields with new data
        profile.name = name
        profile.brand_name = brand_name
        profile.page_link = page_link
        profile.mobile_banking = mobile_banking
        profile.mobile_banking_number = mobile_banking_number
        profile.save()

        messages.success(request, "Profile updated successfully!")
        return redirect ('update_profile')
    
    return render(request, 'core/update.html', {'profile': profile, 'query': 'profile'})



# new product add
def add_product(request):
    if request.method == 'POST':
        name = request.POST['name']
        color = request.POST['color']
        GSM = request.POST['GSM']
        buying_price = request.POST['buying_price']
        price = request.POST['price']
        available = request.POST['available']
        size = request.POST['size'].upper()
        product = Product.objects.create(name=name, color=color, GSM=GSM, buying_price=buying_price, price=price, size=size, available=available)
        product.save()
        return redirect('manager')
    
    return render(request, 'core/add_product.html')


#ink use
@login_required(login_url='login')
def ink_use(request, pk):
    company = Company.objects.get(id=1)
    if pk == 1:
        company.white_ink -= 1
        company.cost += 600
        company.profit -= 600
    elif pk == 2:
        company.black_ink -= 1
        company.cost += 600
        company.profit -= 600
    elif pk == 3:
        company.cyan_ink -= 1
        company.cost += 600
        company.profit -= 600
    elif pk == 4:
        company.magenda_ink -= 1
        company.cost += 600
        company.profit -= 600
    elif pk == 5:
        company.yellow_ink -= 1
        company.cost += 600
        company.profit -= 600
    
    company.save()
    return HttpResponseRedirect(reverse('manager'))



#waste
@login_required(login_url='login')
def product_waste(request, pk):

    product = Product.objects.get(id=pk)
    company = Company.objects.get(id=1)
    product.available -= 1
    company.waste += 190
    company.profit -= 190
    company.save()
    product.save()
    return HttpResponseRedirect(reverse('manager'))


@login_required(login_url='login')
def stock_waste(request, pk):

    company = Company.objects.get(id=1)
    if pk == 3:
        company.a3_paper -= 1
        company.waste += 30
        company.profit -= 30
    elif pk == 4:
        company.a4_paper -= 1
        company.waste += 15
        company.profit -= 15
    company.save()
    return HttpResponseRedirect(reverse('manager'))


@login_required(login_url='login')
def confirm_vendor(request, pk):
    vendor = Profile.objects.get(id=pk)
    vendor.is_verified = True
    vendor.save()
    subject = "Your Panel is now ACTIVE!"
    message = f"Dear Vendor, We reviewed and confirmed your verification reqeuest. You can place order from your panel. Thank you."
    from_email = settings.EMAIL_HOST_USER
    recipient = [vendor.user.email]
    send_mail(subject, message, from_email, recipient_list=recipient)
    return redirect('manager')


def reset_pass(request):
    if request.method == 'POST':
        username = request.POST['username']
        try:
            user = User.objects.get(username=username)
        except:
            user = None

        if user:
            subject = "Your Password Reset Link!"
            message = f"Your password reset link - http://127.0.0.1:8000/reset-confirm32493847957834973459fsdlfjkasgsghkuj2kj343h24ksjdhfasdf/{user.id}"
            from_email = settings.EMAIL_HOST_USER
            recipient = [user.email]
            send_mail(subject, message, from_email, recipient_list=recipient)
            messages.success(request, 'We have sent you the reset link, in your registered email.')
            return redirect('reset_pass')

        else:
            messages.success(request, 'User does not exists.')
            return redirect('reset_pass')

    return render(request, 'core/password_reset_form.html')


def reset_confirm(request, pk):

    id = int(pk)

    if request.method == 'POST':
        user = User.objects.get(id=id)
        password = request.POST['password']
        password1 = request.POST['password1']
        if password == password1:
            user.set_password(password)
            user.save()
            return redirect('login')
        else:
            messages.success(request, "Passwords don't match.")
            return redirect('reset_confirm', pk=id)


    return render(request, 'core/password_reset_confirm.html')