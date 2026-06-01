# core/admin.py
from django.contrib import admin
from .models import Client, Order, Material, Invoice, ActivityLog

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'phone', 'company', 'is_active', 'avatar')
    search_fields = ('name', 'email', 'company')
    list_filter = ('is_active', 'company')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'client', 'created_at', 'status']
    list_filter = ['created_at', 'status']
    search_fields = ['order_id', 'client__name']

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('name', 'quantity', 'threshold', 'unit')

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'amount', 'created_at')
    search_fields = ('order__order_id',)

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('activity_type', 'description', 'user', 'created_at')
    list_filter = ('activity_type', 'created_at')
    search_fields = ('description',)