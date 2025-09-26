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
import pandas as pd
from django.http import HttpResponse
import csv
from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

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
    email_template_name = 'registration/password_reset_email.txt'   # plain text fallback
    subject_template_name = 'registration/password_reset_subject.txt'
    html_email_template_name = 'registration/password_reset_email.html'
    
class ResendPasswordResetView(PasswordResetDoneView):
    def get(self, request, *args, **kwargs):
        email = request.session.get("reset_email")

        if email:
            form = PasswordResetForm({"email": email})
            if form.is_valid():
                form.save(
                    request=request,
                    use_https=request.is_secure(),
                    email_template_name="registration/password_reset_email.txt",  # fallback
                    html_email_template_name="registration/password_reset_email.html",  # ✅ main HTML
                    subject_template_name="registration/password_reset_subject.txt",
                )
                messages.success(request, "We’ve resent the password reset email.")
            else:
                messages.error(request, "Invalid email address.")
        else:
            messages.error(request, "No email stored. Please enter your email again.")
            return redirect("password_reset")

        return redirect("password_reset_done")

def export_loans(request):
    # Fetch loan requests from the database
    loans = LoanRequest.objects.select_related('product', 'requested_by').all()

    # Prepare data for the Excel file
    data = []
    for loan in loans:
        data.append({
            'Product Name': loan.product.name,
            'Lab': loan.product.lab.name,
            'Requester': loan.requested_by.username,
            'Request Date': loan.request_date.strftime('%Y-%m-%d'),
            'Return Date': loan.return_date.strftime('%Y-%m-%d') if loan.return_date else 'N/A',
            'Status': loan.status,
            'Rejection Reason': loan.rejection_reason if loan.status == 'rejected' else 'N/A',
        })

    # Create a DataFrame using pandas
    df = pd.DataFrame(data)

    # Generate the Excel file
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="loan_requests.xlsx"'
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Loan Requests')

    return response

def export_approved_loans(request):
    # Fetch approved loan requests
    loans = LoanRequest.objects.filter(status='approved').select_related('product', 'requested_by')

    # Prepare data for the Excel file
    data = []
    for loan in loans:
        data.append({
            'Product Name': loan.product.name,
            'Lab': loan.product.lab.name,
            'Requester': loan.requested_by.username,
            'Request Date': loan.request_date.strftime('%Y-%m-%d'),
            'Return Date': loan.return_date.strftime('%Y-%m-%d') if loan.return_date else 'N/A',
            'Status': loan.status,
        })

    # Create a DataFrame using pandas
    df = pd.DataFrame(data)

    # Generate the Excel file
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="approved_loans.xlsx"'
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Approved Loans')

    return response


def export_rejected_loans(request):
    # Fetch rejected loan requests
    loans = LoanRequest.objects.filter(status='rejected').select_related('product', 'requested_by')

    # Prepare data for the Excel file
    data = []
    for loan in loans:
        data.append({
            'Product Name': loan.product.name,
            'Lab': loan.product.lab.name,
            'Requester': loan.requested_by.username,
            'Request Date': loan.request_date.strftime('%Y-%m-%d'),
            'Rejection Reason': loan.rejection_reason,
            'Status': loan.status,
        })

    # Create a DataFrame using pandas
    df = pd.DataFrame(data)

    # Generate the Excel file
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="rejected_loans.xlsx"'
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Rejected Loans')

    return response

def export_transfers(request):
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transfers.csv"'

    writer = csv.writer(response)
    # Write the header row
    writer.writerow(['Product', 'From Lab', 'To Lab', 'Quantity', 'Transferred By', 'Transferred At', 'Return Status'])

    # Write data rows
    for transfer in ProductTransfer.objects.all():
        writer.writerow([
            transfer.product.name,
            transfer.from_lab.name,
            transfer.to_lab.name,
            transfer.quantity,
            transfer.transferred_by.username,
            transfer.transferred_at.strftime('%Y-%m-%d %H:%M'),
            'Returned' if transfer.return_product else 'Transferred'
        ])

    return response





class MyPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = 'password_change/password_change.html'
    success_url = reverse_lazy('password_change_done')
    
    
from datetime import timedelta
from django.shortcuts import render
from django.urls import reverse
from django.http import JsonResponse
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone

from .models import Lab, Product, Category, LoanRequest, ProductTransfer, User


def dashboard_view(request):
    return render(request, "dashboard.html", {
        "data_url": reverse("dashboard-data")
    })


def dashboard_data_view(request):
    """
    JSON data used by dashboard.html for all charts/graphs/tables.
    Supports ?limit_products=<int> to cap the D3 graph size.
    """
    limit_products = max(50, min(int(request.GET.get("limit_products", 200)), 2000))

    now = timezone.now()
    start_date = (now - timedelta(days=29)).date()  # last 30 days inclusive

    # Aggregates
    total_products = Product.objects.count()
    total_labs = Lab.objects.count()
    total_categories = Category.objects.count()
    total_transfers = ProductTransfer.objects.count()
    active_loans_count = LoanRequest.objects.filter(status="approved").count()

    total_users = User.objects.count()
    teachers_count = User.objects.filter(is_teacher=True).count()
    students_count = User.objects.filter(is_student=True).count()
    hods_count = User.objects.filter(is_hod=True).count()

    # Labs with counts
    labs_qs = Lab.objects.annotate(
        product_count=Count('products', distinct=True),
        transfers_in_count=Count('transfers_in', distinct=True),
        transfers_out_count=Count('transfers_out', distinct=True),
        available=Count('products', filter=Q(products__status='available'), distinct=True),
        pending=Count('products', filter=Q(products__status='pending'), distinct=True),
        in_loan=Count('products', filter=Q(products__status='in_loan'), distinct=True),
        returned=Count('products', filter=Q(products__status='returned'), distinct=True),
    ).order_by('name')

    labs = [
        {
            "id": lab.id,
            "name": lab.name,
            "product_count": lab.product_count,
            "transfers_in_count": lab.transfers_in_count,
            "transfers_out_count": lab.transfers_out_count,
            "statuses": {
                "available": lab.available,
                "pending": lab.pending,
                "in_loan": lab.in_loan,
                "returned": lab.returned,
            }
        }
        for lab in labs_qs
    ]

    # Categories with counts
    categories_qs = Category.objects.annotate(
        product_count=Count('product', distinct=True)  # reverse relation 'product'
    ).order_by('name')
    categories = [
        {"id": c.id, "name": c.name, "product_count": c.product_count}
        for c in categories_qs
    ]

    # Product status counts (global)
    status_choices = [code for code, _ in Product.STATUS_CHOICES]
    status_counts_qs = Product.objects.values('status').annotate(count=Count('id'))
    product_status_counts = {code: 0 for code in status_choices}
    for row in status_counts_qs:
        product_status_counts[row['status']] = row['count']

    # Timeseries: Loans (stacked by status) over last 30 days
    loans_daily = LoanRequest.objects.filter(request_date__date__gte=start_date)\
        .annotate(day=TruncDate('request_date'))\
        .values('day', 'status')\
        .annotate(count=Count('id'))\
        .order_by('day')

    days = [start_date + timedelta(days=i) for i in range(30)]
    day_labels = [d.isoformat() for d in days]
    daily_map = {d: {"pending": 0, "approved": 0, "rejected": 0} for d in day_labels}
    for row in loans_daily:
        day_label = row['day'].isoformat()
        if day_label in daily_map:
            daily_map[day_label][row['status']] = row['count']
    loans_timeseries = {
        "dates": day_labels,
        "pending": [daily_map[d]["pending"] for d in day_labels],
        "approved": [daily_map[d]["approved"] for d in day_labels],
        "rejected": [daily_map[d]["rejected"] for d in day_labels],
    }

    # Timeseries: Transfers (per day)
    transfers_daily = ProductTransfer.objects.filter(transferred_at__date__gte=start_date)\
        .annotate(day=TruncDate('transferred_at'))\
        .values('day')\
        .annotate(count=Count('id'))\
        .order_by('day')

    transfers_map = {d: 0 for d in day_labels}
    for row in transfers_daily:
        day_label = row['day'].isoformat()
        if day_label in transfers_map:
            transfers_map[day_label] = row['count']
    transfers_timeseries = {
        "dates": day_labels,
        "counts": [transfers_map[d] for d in day_labels]
    }

    # Recent activity
    recent_loans_qs = LoanRequest.objects.select_related(
        'product', 'requested_by', 'for_student', 'approved_by'
    ).order_by('-request_date')[:10]
    recent_loans = []
    for lr in recent_loans_qs:
        recent_loans.append({
            "id": lr.id,
            "product": lr.product.name if lr.product_id else None,
            "requested_by": lr.requested_by.username if lr.requested_by_id else None,
            "for_student": lr.for_student.username if lr.for_student_id else None,
            "status": lr.status,
            "request_date": timezone.localtime(lr.request_date).isoformat() if lr.request_date else None,
            "approved_by": lr.approved_by.username if lr.approved_by_id else None,
            "approved_date": timezone.localtime(lr.approved_date).isoformat() if lr.approved_date else None,
            "return_date": lr.return_date.isoformat() if lr.return_date else None,
            "return_status": lr.return_status,
            "rejection_reason": lr.rejection_reason,
        })

    recent_transfers_qs = ProductTransfer.objects.select_related(
        'product', 'from_lab', 'to_lab', 'transferred_by'
    ).order_by('-transferred_at')[:10]
    recent_transfers = []
    for t in recent_transfers_qs:
        recent_transfers.append({
            "id": t.id,
            "product": t.product.name if t.product_id else None,
            "from_lab": t.from_lab.name if t.from_lab_id else None,
            "to_lab": t.to_lab.name if t.to_lab_id else None,
            "quantity": t.quantity,
            "return_product": t.return_product,
            "transferred_by": t.transferred_by.username if t.transferred_by_id else None,
            "transferred_at": timezone.localtime(t.transferred_at).isoformat() if t.transferred_at else None,
        })

    # D3 Graph: labs + a capped set of products
    products_for_graph_qs = Product.objects.select_related('lab', 'category')\
        .order_by('-id')[:limit_products]

    graph_nodes = []
    graph_links = []

    # labs as nodes
    for lab in labs_qs:
        graph_nodes.append({
            "id": f"lab-{lab.id}",
            "label": lab.name,
            "type": "lab",
            "size": max(10, min(40, 10 + lab.product_count // 2)),
        })

    # products as nodes + links
    for p in products_for_graph_qs:
        graph_nodes.append({
            "id": f"prod-{p.id}",
            "label": p.name,
            "type": "product",
            "status": p.status,
            "lab_id": p.lab_id,
            "category": p.category.name if p.category_id else None,
        })
        graph_links.append({
            "source": f"lab-{p.lab_id}",
            "target": f"prod-{p.id}"
        })

    data = {
        "summary": {
            "totals": {
                "products": total_products,
                "labs": total_labs,
                "categories": total_categories,
                "transfers": total_transfers,
                "users": total_users,
                "teachers": teachers_count,
                "students": students_count,
                "hods": hods_count,
                "active_loans": active_loans_count,
            }
        },
        "labs": labs,
        "categories": categories,
        "product_status_counts": product_status_counts,
        "statuses_by_lab": [
            {
                "lab_id": l["id"],
                "lab_name": l["name"],
                **l["statuses"]
            } for l in labs
        ],
        "timeseries": {
            "loans": loans_timeseries,
            "transfers": transfers_timeseries,
        },
        "recent": {
            "loans": recent_loans,
            "transfers": recent_transfers,
        },
        "graph": {
            "nodes": graph_nodes,
            "links": graph_links,
            "status_palette": {
                "available": "#3fb950",
                "pending": "#f1e05a",
                "in_loan": "#f97583",
                "returned": "#58a6ff",
            }
        },
        "meta": {
            "generated_at": now.isoformat(),
            "status_choices": status_choices,
            "limit_products": limit_products,
        }
    }
    return JsonResponse(data, safe=True)