from app.models import *
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from .models import User
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import authenticate, login as auth_login
from django.shortcuts import render, redirect , get_object_or_404
from django.core.mail import EmailMessage
from django.db.models import Count
from datetime import datetime
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.views import PasswordResetDoneView
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.views import PasswordResetView
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView
from django.shortcuts import redirect
from django.contrib import messages
import logging
from django.contrib.auth import logout
from django.contrib.auth.decorators import user_passes_test
import threading
from django.template.loader import render_to_string
import logging
import socket
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Count
from .models import Lab, Product, Category

logger = logging.getLogger(__name__)

@login_required(login_url='login')
def home(request):
    lab = Lab.objects.all()
    return render(request,'home.html' , {"labs":lab})



def lab_product(request, lab_id=None):
   
    all_lab = Lab.objects.all()
    if not all_lab.exists():
        messages.error(request, "No labs available.")
        return redirect('home')

  
    if request.method == 'POST':
        transfer_id = request.POST.get('transfer_id')
        if transfer_id:
            product = ProductTransfer.objects.filter(id=transfer_id).first()
            product.return_product = True
            product.product.lab = product.from_lab
            product.product.save()
            product.save()
            messages.success(request, f"Product '{product.product.name}' returned to '{product.from_lab.name}' successfully.")
            return redirect('lab-product', lab_id=product.to_lab.id)
           
        lab_id = request.POST.get('lab_id')
    if not lab_id:
        lab_id = all_lab.first().id

    selected_lab = Lab.objects.filter(id=lab_id).first()
    if not selected_lab:
        messages.error(request, "Selected lab does not exist.")
        return redirect('home')

    
    lab_products = Product.objects.filter(lab=selected_lab)
    categories = Category.objects.filter(id__in=lab_products.values('category_id')).distinct()
    selected_category = request.GET.get('category', '')
    selected_status = request.GET.get('status', '')
    sort_by = request.GET.get('sort_by', '')

    if selected_category:
        lab_products = lab_products.filter(category__name=selected_category)
    if selected_status:
        lab_products = lab_products.filter(status=selected_status)
    if sort_by == "name_asc":
        lab_products = lab_products.order_by('name')
    elif sort_by == "name_desc":
        lab_products = lab_products.order_by('-name')
    elif sort_by == "recent":
        lab_products = lab_products.order_by('-id')

    total_products = lab_products.count()
    available_products = lab_products.filter(status='available').count()
    in_loan_products = lab_products.filter(status='in_loan').count()

  
    category_counts = lab_products.values('category__name').annotate(count=Count('id'))
    transfers = ProductTransfer.objects.filter(
        product__in=lab_products,
        return_product=False 
    ).order_by('product_id', '-transferred_at')  


    transferred_dict = {}
    for t in transfers:
        if t.product_id not in transferred_dict :  
            transferred_dict[t.product_id] = t

   
    return render(request, 'lab_product.html', {
        "lab_products": lab_products,
        "categories": categories,
        "total_products": total_products,
        "available_products": available_products,
        "in_loan_products": in_loan_products,
        "category_counts": category_counts,
        "selected_category": selected_category,
        "selected_status": selected_status,
        "sort_by": sort_by,
        "all_lab": all_lab,
        "selected_lab": selected_lab,
        "transferred_dict": transferred_dict,
        
    })

def product_detail(request,product_id):
    product = Product.objects.filter(id=product_id).first()
    return render(request,'product_details.html',{"product":product})

def is_connected():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=5)
        return True
    except OSError:
        return False

def send_email(subject, html_content, recipients, from_email):
    if not is_connected():
        logger.warning("No internet connection. Email not sent.")
        return  

    try:
        email = EmailMessage(
            subject=subject,
            body=html_content,
            from_email=from_email,
            to=recipients,
        )
        email.content_subtype = "html"  
        email.send(fail_silently=False)
        logger.info(f"Email sent successfully to {recipients}")
    except Exception as e:
        logger.error(f"Failed to send email to {recipients}: {e}")
        messages.error(None, "Failed to send email. Please try again later.")

def load_request(request, product_id):
    product = Product.objects.filter(id=product_id).first()
    if request.method == 'POST':
        if product.status != 'available':
            messages.error(request, "This product is not available for loan.")
            return redirect('product-detail', product_id=product.id)

        return_date_str = request.POST.get('date')
        return_date = datetime.strptime(return_date_str, "%Y-%m-%d").date()

        loan_request = LoanRequest.objects.create(
            product=product,
            request_date=timezone.now(),
            status='pending',
            requested_by=request.user,
            return_date=return_date
        )

        product.status = 'pending'
        product.in_stock = False
        product.save()

        from_email = settings.EMAIL_HOST_USER
        admin_emails = ['haquemahmudul500@gmail.com']
        user_email = request.user.email

        # Prepare detailed context for emails
        email_context = {
            'product': {
                'name': product.name,
                'description': product.description,
                'category': product.category.name,
                'lab': product.lab.name,
                'status': product.status,
                'serial_number': product.serial_number,
                'price': product.price,
                'base_price': product.base_price
            },
            'loan_request': {
                'request_date': loan_request.request_date,
                'return_date': loan_request.return_date,
                'status': loan_request.status,
                'rejection_reason': loan_request.rejection_reason
            },
            'requested_by': {
                'username': request.user.username,
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'is_student': request.user.is_student,
                'is_teacher': request.user.is_teacher,
                'is_hod': request.user.is_hod,
                'semester': request.user.semester,
                'department': request.user.department,
                'roll_number': request.user.roll_number
            }
        }

        # Admin email
        admin_html = render_to_string('emails/admin_email.html', email_context)

        # User email
        user_html = render_to_string('emails/user_email.html', email_context)

        # Send emails in background threads
        threading.Thread(target=send_email, args=(f"New Loan Request: {product.name}", admin_html, admin_emails, from_email)).start()
        threading.Thread(target=send_email, args=(f"Your Loan Request Submitted: {product.name}", user_html, [user_email], from_email)).start()

        messages.success(request, "Loan request submitted successfully! Emails sent.")
        return redirect('home')

    return render(request, 'load_request.html', {"product": product})


def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email').strip().lower() if request.POST.get('email') else None
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        role = request.POST.get('role')
        semester = request.POST.get('semester')
        department = request.POST.get('department')
        roll_number = request.POST.get('roll_number')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken")
            return redirect('register')

        if password1 != password2:
            messages.error(request, "Passwords do not match")
            return redirect('register')
        
        if email and User.objects.filter(email__iexact=email).exists():
            messages.error(request, "Email already in use")
            return redirect('register')
        if department is None or department.strip() == "":
            messages.error(request, "Department is required")
            return redirect('register')

        
        if role == 'student' and (not semester or not roll_number):
            messages.error(request, "Student must provide Semester and Roll Number")
            return redirect('register')
        

        user = User(
            username=username,
            email=email,
            department=department,
            semester=semester if role == 'student' else None,
            roll_number=roll_number if role == 'student' else None,
            password=make_password(password1)
        )

        if role == 'student':
            user.is_student = True
        elif role == 'teacher':
            user.is_teacher = True
        elif role == 'hod':
            user.is_hod = True

        user.save()
        messages.success(request, "Registration successful!")
        return redirect('login') 

    return render(request, 'register.html')


def login_view(request):
    if request.method == 'POST':
        username_or_email = request.POST.get('username_or_email')
        password = request.POST.get('password')

        user = None
        user = authenticate(request, username=username_or_email, password=password)
        if user is None:
            try:
                user_obj = User.objects.get(email__iexact=username_or_email.strip().lower())
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None

        if user is not None:
            if user.is_student and not user.second_layer_is_student:  
                messages.error(request, "Students are not driect allowed to login.")
                return redirect('login')

            auth_login(request, user)
            messages.success(request, f"Welcome {user.username}!")
            return redirect('home') 

        else:
            messages.error(request, "Invalid credentials")
            return redirect('login')

    return render(request, 'login.html')

def user_logout(request):
    logout(request)  
    return redirect('login')

def hod_required(user):
    return user.is_authenticated and user.is_hod

@user_passes_test(hod_required, login_url='login')
def loan_approve(request):
    pending_count = LoanRequest.objects.filter(status="pending").count()
    approved_count = LoanRequest.objects.filter(status="approved").count()

    load_req =  LoanRequest.objects.all().order_by('-request_date')
    return render(request,'loan_approve.html',{"load_req":load_req,"pending_count":pending_count,"approved_count":approved_count})

@user_passes_test(hod_required, login_url='login')
def approve(request, approved_loan_request_id, id):
    try:
        loan_request = LoanRequest.objects.get(id=approved_loan_request_id)
    except LoanRequest.DoesNotExist:
        messages.error(request, "Loan request not found.")
        return redirect('home')

    if id == 1:  # Approve
        loan_request.status = 'approved'
        loan_request.approved_by = request.user
        loan_request.approved_date = timezone.now()
        loan_request.product.status = 'in_loan'
        loan_request.product.save()
        loan_request.save()
        messages.success(request, "Loan request approved.")
    elif id == 2:  # Reject
        if request.method == 'POST':
            reason = request.POST.get('reason')
            loan_request.rejection_reason = reason
            loan_request.save()
        loan_request.status = 'rejected'
        loan_request.approved_by = request.user
        loan_request.approved_date = timezone.now()
        loan_request.product.status = 'available'
        loan_request.product.in_stock = True
        loan_request.product.save()
        loan_request.save()
        
        messages.success(request, "Loan request rejected.")
    else:
        messages.error(request, "Invalid action.")
    return redirect('home')

def loan_transaction(request):
    return render(request,'loan_transaction.html')

@login_required(login_url='login')
def your_loan(request):
    
    loans = LoanRequest.objects.filter(requested_by=request.user).order_by('-request_date')

    if request.method == "POST":
        loan_id = request.POST.get('id')
        loan_request = get_object_or_404(LoanRequest, id=loan_id, requested_by=request.user)

        if loan_request.status != "approved":
            messages.error(request, "This loan is not approved yet, so it cannot be returned.")
            return redirect("your_loan")

        if loan_request.return_status:
            messages.warning(request, "This loan has already been returned.")
            return redirect("your_loan")

        # Loan return process
        loan_request.return_status = True
        loan_request.return_date = timezone.now().date()

        loan_request.product.status = 'available'
        loan_request.product.in_stock = True
        loan_request.product.save()
        loan_request.save()

        messages.success(request, "Return request submitted successfully.")
        return redirect("your_loan")

    return render(request, "your_loan.html", {"return_requests": loans})





def product_transfer(request,product_id):
    if request.method == "POST":
        to_lab_id = request.POST['to_lab']
        to_lab = Lab.objects.filter(id=to_lab_id).first()
        product = Product.objects.filter(id=product_id).first()
        from_lab = product.lab
        if to_lab and product and from_lab != to_lab:
            ProductTransfer.objects.create(
                product=product,
                from_lab=from_lab,
                to_lab=to_lab,
                transferred_by=request.user,
                transferred_at=timezone.now(),
                return_product=False
            )
            product.lab = to_lab
            product.save()
            messages.success(request, f"Product '{product.name}' transferred to '{to_lab.name}' successfully.")
            return redirect('lab-product', lab_id=to_lab.id)
        else:
            messages.error(request, "Invalid lab selection or same lab selected.")
            return redirect('product-transfer', product_id=product.id)
        
    product = Product.objects.filter(id=product_id).first()
    product_lab_id = product.lab.id
    labs = Lab.objects.exclude(id=product_lab_id)
    transfers = ProductTransfer.objects.all().order_by('-transferred_at')
    return render(request, 'product_transfer.html' , {"labs":labs,"product":product})


def lab_to_lab_transfer(request):
    transfers = ProductTransfer.objects.select_related(
        'product', 'from_lab', 'to_lab', 'transferred_by'
    ).order_by('-transferred_at')  

    labs = Lab.objects.all()

    context = {
        'transfers': transfers,
        'labs': labs,
    }
    return render(request, 'lab_to_lab_transfer.html', context)




class CustomPasswordResetView(PasswordResetView):
    template_name = 'password_reset.html'
    email_template_name = 'registration/password_reset_email.txt'
    subject_template_name = 'registration/password_reset_subject.txt'
    html_email_template_name = 'registration/password_reset_email.html'

    def form_valid(self, form):
        # Save email in session so it can be resent
        email = form.cleaned_data.get("email")
        if email:
            self.request.session["reset_email"] = email
        logger.info("Password reset form is valid. Sending email...")
        return super().form_valid(form)

    def form_invalid(self, form):
        logger.error("Password reset form is invalid.")
        return super().form_invalid(form)
    
    
class ResendPasswordResetView(PasswordResetDoneView):
    def get(self, request, *args, **kwargs):
        email = request.session.get("reset_email")

        if email:
            form = PasswordResetForm({"email": email})
            if form.is_valid():
                form.save(
                    request=request,
                    use_https=request.is_secure(),
                    email_template_name="registration/password_reset_email.html",
                    subject_template_name="registration/password_reset_subject.txt",
                )
                messages.success(request, "We’ve resent the password reset email.")
            else:
                messages.error(request, "Invalid email address.")
        else:
            messages.error(request, "No email stored. Please enter your email again.")
            return redirect("password_reset")

        return redirect("password_reset_done")