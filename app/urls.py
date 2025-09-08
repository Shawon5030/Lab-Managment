from app.views import  *
from django.urls import path , include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('',home , name = 'home'),
    path('lab-product/<int:lab_id>',lab_product,name = 'lab-product'),
    path('product_detail/<int:product_id>',product_detail,name = 'product-detail'),
    path('load_request/<int:product_id>',load_request,name = 'load_request'),
    path('loan_transaction/',loan_transaction,name = 'loan_transaction'),
    path('approve/loan/',loan_approve,name = 'approve_page'),
    path("approve/<int:approved_loan_request_id>/xyz/<int:id>",approve,name="approve"),
    path('register/',register,name = 'register'),
    path('login/',login_view,name = 'login'),
    path('logout/', user_logout, name='logout'),
    path('your-loan/654xy/loan',your_loan,name = "your_loan"),
    path("product_transfer/<int:product_id>",product_transfer,name = "product_transfer"),
    path('lab/to/lab/',lab_to_lab_transfer,name="lab_to_lab_transfer"),
    path('export-transfers/', export_transfers, name='export_transfers'),
    
    path('password_reset/',  CustomPasswordResetView.as_view(),  name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
     path("password_reset/resend/", ResendPasswordResetView.as_view(), name="password_reset_resend"),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),
   
]  + static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)