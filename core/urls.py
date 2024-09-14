from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.userpanel, name='user_panel'),
    path('manager', views.adminpanel, name='manager'),
    path('register/', views.vendor_register, name='vendor_register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('place-order/', views.place_single_order, name='place_single_order'),
    path('confirm-order/<str:pk>', views.order_confirm, name='order_confirm'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('cancel/<str:pk>', views.order_cancel, name='order_cancel'),
    path('order-details/<str:pk>', views.order_details, name='order_details'),
    path('order-printed/<str:pk>', views.printed, name='printed'),
    path('order-shipped/<str:pk>', views.shipped, name='shipped'),
    path('dues', views.due_list, name='due_list'),
    path('paid/<str:pk>', views.paid, name='paid'),
    path('product-waste/<str:pk>', views.product_waste, name='product_waste'),
    path('stock-waste/<int:pk>', views.stock_waste, name='stock_waste'),
    path('ink-use/<int:pk>', views.ink_use, name='ink_use'),
    path('add-product', views.add_product, name='add_product'),
    path('confirm-order-verified/<str:pk>', views.order_verify, name='order_verify'),
    path('confirm-vendor/<str:pk>', views.confirm_vendor, name='confirm_vendor'),
    path('clear-backend', views.clear_backend, name='clear_backend'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)