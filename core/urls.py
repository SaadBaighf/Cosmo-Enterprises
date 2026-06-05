from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.admin_login, name='admin_login'),           
    path('dashboard/', views.main_dashboard, name='main_dashboard'),  
    path('client/', views.client_dashboard, name='client_dashboard'),
    path('order/', views.order_dashboard, name='order_dashboard'),      
    path('order/add/<int:client_id>/', views.add_order_for_client, name='add_order_for_client'),
    path('inventory/', views.inventory_dashboard, name='inventory_dashboard'),
    path('finance/', views.finance_dashboard, name='finance_dashboard'),
    path('batch/', views.batch_dashboard, name='batch_dashboard'),
    path('order/advance/<int:order_id>/', views.advance_order_status, name='advance_order_status'),
    path('finance/invoice/<int:invoice_id>/', views.view_invoice, name='view_invoice'),
    path('invoice/create/<int:order_id>/', views.create_invoice, name='create_invoice'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('stripe/generate/<int:invoice_id>/', views.generate_stripe_link, name='generate_stripe_link'),
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('stripe/sync/<int:invoice_id>/', views.sync_stripe_payment, name='sync_stripe_payment'),
    path('finance/invoice/<int:invoice_id>/pdf/', views.download_invoice_pdf, name='download_invoice_pdf'),
    path('api/clients/', views.client_search_api, name='client_search_api'),
    path('api/material/<int:material_id>/vendors/', views.get_material_vendors, name='material_vendors'),
    path('logout/', views.admin_logout, name='logout'),
]