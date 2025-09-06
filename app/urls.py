from app.views import  *
from django.urls import path , include
from django.conf import settings
from django.conf.urls.static import static
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
    path("product_transfer/<int:product_id>",product_transfer,name = "product_transfer")
   
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

