from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Client, Invoice, Order, Material, ActivityLog
from .forms import ClientForm, OrderForm
from  django.http import JsonResponse
from django.urls import reverse
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count, Sum , F , DecimalField
from core.models import Material
import json
from datetime import datetime
from django.utils import timezone
from decimal import Decimal, InvalidOperation
from django.http import HttpResponse , Http404
import random
from django.template.loader import render_to_string
import os
import tempfile
import subprocess
from django.conf import settings
from django.db.models.functions import Coalesce
from django.db import models
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required


BANKS = [
    "Global Trust Bank",
    "Penta Financial Services",
    "Horizon Capital Bank",
    "Summit National Bank",
    "Vertex Banking, Ltd."
]

IBANS = [
    "DE89370400440532013000",
    "FR1420041010050500013M02606",
    "GB29NWBK60161331926819",
    "IT60X0542811101000000123456",
    "ES9121000418450200051332"
]

def get_bank_details(invoice_id):
    """Return consistent bank name and IBAN for a given invoice ID."""
    index = invoice_id % len(BANKS)  
    return BANKS[index], IBANS[index]

# models.py

@csrf_protect
def admin_logout(request):
    """Custom logout view with CSRF protection"""
    if request.method == 'POST':
        # Get the next page parameter
        next_page = request.GET.get('next', 'admin_login')
        # Log out the user
        from django.contrib.auth import logout
        logout(request)
        # Redirect to login page
        return redirect(next_page)
    else:
        # If not POST, show confirmation page
        return render(request, 'logout_confirm.html')

@login_required
def main_dashboard(request):
    # Calculate stats
    total_clients = Client.objects.count()
    total_orders = Order.objects.count()
    total_materials = Material.objects.count()
    low_stock_materials = Material.objects.filter(quantity__lte=F('threshold')).count()
    out_of_stock_materials = Material.objects.filter(quantity__lte=0).count()
    
    # Calculate finance stats
    orders_with_payments = Order.objects.prefetch_related('invoices').all()
    total_invoices = orders_with_payments.count()
    unpaid_invoices = 0
    
    for order in orders_with_payments:
        total_paid = sum(invoice.amount for invoice in order.invoices.all())
        remaining = order.payment - total_paid
        if remaining > 0:
            unpaid_invoices += 1
    
    # ✅ GET RECENT ACTIVITIES FROM ACTIVITY LOG - WITH COMPLETE ICON MAPPING
    recent_activities = []
    activity_logs = ActivityLog.objects.order_by('-created_at')[:8]
    
    for log in activity_logs:
        # Map activity types to icons and colors
        if log.activity_type == 'client_created':
            icon = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>'
            color = 'rgba(14, 116, 144, 0.2)'
        elif log.activity_type == 'client_updated':
            icon = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>'
            color = 'rgba(14, 116, 144, 0.2)'
        elif log.activity_type == 'client_deleted':
            icon = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><line x1="3" y1="20" x2="21" y2="20"></line></svg>'
            color = 'rgba(239, 68, 68, 0.2)'
        elif log.activity_type == 'order_created':
            icon = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path></svg>'
            color = 'rgba(59, 130, 246, 0.2)'
        elif log.activity_type == 'order_updated':
            icon = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>'
            color = 'rgba(59, 130, 246, 0.2)'
        elif log.activity_type == 'order_deleted':
            icon = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><line x1="3" y1="20" x2="21" y2="20"></line></svg>'
            color = 'rgba(239, 68, 68, 0.2)'
        elif log.activity_type == 'payment_recorded':
            icon = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="5" width="20" height="14" rx="2"></rect><line x1="6" y1="12" x2="6" y2="12"></line><line x1="10" y1="12" x2="14" y2="12"></line><line x1="18" y1="12" x2="18" y2="12"></line></svg>'
            color = 'rgba(16, 185, 129, 0.2)'
        elif log.activity_type == 'material_created':
            icon = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path></svg>'
            color = 'rgba(245, 158, 11, 0.2)'
        elif log.activity_type == 'material_updated':
            icon = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path><line x1="12" y1="6" x2="12" y2="12"></line></svg>'
            color = 'rgba(245, 158, 11, 0.2)'
        elif log.activity_type == 'material_deleted':
            icon = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path><line x1="3" y1="20" x2="21" y2="20"></line></svg>'
            color = 'rgba(239, 68, 68, 0.2)'
        else:
            # Default icon for other activities
            icon = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle></svg>'
            color = 'rgba(107, 114, 128, 0.2)'
        
        recent_activities.append({
            'description': log.description,
            'timestamp': log.created_at.strftime('%b %d'),
            'icon': icon,
            'icon_color': color,
            'category': log.activity_type.split('_')[0]
        })
    
    context = {
        'total_clients': total_clients,
        'total_orders': total_orders,
        'total_materials': total_materials,
        'low_stock_materials': low_stock_materials,
        'out_of_stock_materials': out_of_stock_materials,
        'total_invoices': total_invoices,
        'unpaid_invoices': unpaid_invoices,
        'recent_activities': recent_activities,
    }
    
    return render(request, 'main.html', context)

def client_detail(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    orders = Order.objects.filter(client=client)
    return render(request, 'client.html', {
        'client': client,
        'orders': orders
    })

def order_list(request):
    orders = Order.objects.all()
    completed_orders = [o for o in orders if o.status == 'completed']
    pending_orders = [o for o in orders if o.status != 'completed']
    return render(request, 'orders.html', {
        'orders': orders,
        'completed_orders': completed_orders,
        'pending_orders': pending_orders
    })

def inventory_view(request):
    materials = Material.objects.all()
    low_stock = [m for m in materials if m.current_stock < m.threshold_amount]
    return render(request, 'inventory.html', {
        'materials': materials,
        'low_stock': low_stock
    })

@login_required
def finance_view(request):
    # For now, use mock data (replace with real models later)
    client_invoices = [
        {'client': 'Ali Khan', 'amount': 5000, 'due_date': '2025-12-31', 'status': 'paid'},
        {'client': 'Sara Ahmed', 'amount': 3000, 'due_date': '2025-12-15', 'status': 'unpaid'}
    ]
    vendor_bills = [
        {'vendor': 'Polymer Co', 'amount': 2000, 'due_date': '2025-12-20', 'status': 'unpaid'},
        {'vendor': 'Chemical Ltd', 'amount': 1500, 'due_date': '2025-12-10', 'status': 'paid'}
    ]
    return render(request, 'finance.html', {
        'client_invoices': client_invoices,
        'vendor_bills': vendor_bills
    })


def home(request):
    return render(request, 'main.html')  # or whatever template you want

@login_required
def client_dashboard(request):
    # === CALCULATE STATS ===
    total_clients = Client.objects.count()
    active_clients = Client.objects.filter(is_active=True).count()
    inactive_clients = Client.objects.filter(is_active=False).count()

    # Clients created this month
    now = datetime.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_month_clients = Client.objects.filter(created_at__gte=start_of_month).count()
    
    # return render(request, 'client.html', {
    #     'clients': clients,
    #     'form': form,
    #     'all_clients_json': all_clients_json,
    #     'total_clients': total_clients,
    #     'active_clients': active_clients,
    #     'inactive_clients': inactive_clients,
    #     'this_month_clients': this_month_clients,
    # })
    
    # Handle DELETE
    if request.method == "POST" and "delete_client" in request.POST:
        client_id = request.POST.get("client_id")
        client = get_object_or_404(Client, id=client_id)
        client_name = client.name
        client.delete()
        
        # activity log
        ActivityLog.objects.create(
            activity_type = 'client_deleted',
            description = f'Client deleted : {client_name}',
            user = request.user,
            client_id = client.id
        )
        
        messages.success(request, f"Client '{client_name}' deleted successfully.")
        return redirect('client_dashboard')

    # Handle CREATE/UPDATE (POST)
    if request.method == "POST":
        client_id = request.POST.get("client_id")
        if client_id:
            client = get_object_or_404(Client, id=client_id)
            form = ClientForm(request.POST, request.FILES, instance=client)
        else:
            form = ClientForm(request.POST, request.FILES)

        if form.is_valid():
            client = form.save()
            action = "updated" if client_id else "added"
            
            #activity log
            if action == "added":
                ActivityLog.objects.create(
                    activity_type = 'client_created',
                    description = f'New client created : {client.name}',
                        user = request.user,
                        client_id = client.id
                )
            
            else:
                ActivityLog.objects.create(
                    activity_type = 'client_updated',
                    description =  f'Client Updated : {client.name}',
                    user = request.user,
                    client_id = client.id
                )
            
            messages.success(request, f"Client {action} successfully.")
            return redirect('client_dashboard')
    else:
        form = ClientForm()

        # === FILTER & SEARCH LOGIC ===
    clients = Client.objects.all()
    search = request.GET.get('search')
    status = request.GET.get('status')

    # === FILTER & SEARCH LOGIC ===
    clients = Client.objects.all()
    search = request.GET.get('search')
    status = request.GET.get('status')

    # === SEARCH LOGIC ===
    if search:
        # Logic:
        # 1. Name starts with 'search' (e.g., "a" finds "Ahmed")
        # 2. Name contains " search" (e.g., " Baig" finds "Saad Baig")
        # 3. Company starts with 'search' (e.g., "Ham" finds "Hamdard")
        query_filter = (
            Q(name__istartswith=search) | 
            Q(name__icontains=" " + search) | 
            Q(company__istartswith=search)
        )
        
        # If search is a number (e.g., "31"), also check Client ID
        if search.isdigit():
            query_filter |= Q(id=int(search))
            
        clients = clients.filter(query_filter)

    # === STATUS FILTER LOGIC ===
    if status == 'active':
        clients = clients.filter(is_active=True)
    elif status == 'inactive':
        clients = clients.filter(is_active=False)
        
    return render(request, 'client.html', {
        'clients': clients,
        'form': form,
        'total_clients': total_clients,
        'active_clients': active_clients,
        'inactive_clients': inactive_clients,
        'this_month_clients': this_month_clients,
    })
    
    
@login_required
def order_dashboard(request):
    orders = Order.objects.select_related('client').all()  # Efficient query

    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
    # ====================================
    # === SEARCH LOGIC ===
    search_query = request.GET.get('search', '')
    if search_query:
        # Search ONLY in Order ID and Fabric Type (Quantity handled below)
        query_filter = (
            Q(order_id__icontains=search_query) |
            Q(fabric_type__istartswith=search_query) 
            # REMOVED: Q(client__name__icontains=search_query) to prevent false matches
        )
        
        # If the user types numbers, also check Quantity AND Client ID
        if search_query.isdigit():
            query_filter |= Q(quantity=int(search_query)) | Q(client__id=int(search_query))
            
        orders = orders.filter(query_filter)
    
    #Handles delete
    if request.method == "POST" and "delete_order" in request.POST:
        order_id = request.POST.get("order_id")
        order = get_object_or_404(Order, id=order_id)
        order_id_str = order.order_id
        order.delete()
        
        # ✅ ADD ACTIVITY LOG FOR ORDER DELETION
        ActivityLog.objects.create(
            activity_type='order_deleted',
            description=f'Order deleted: #{order_id_str}',
            user=request.user,
            order_id=order_id
        )
        
        messages.success(request, f"Order {order_id_str} deleted successfully.")
        return redirect('order_dashboard')
    
    # Handle EDIT (Update)
    if request.method == "POST" and "edit_order" in request.POST:
        order_id = request.POST.get("order_id")
        order = get_object_or_404(Order, id=order_id)
        # Bind the form to the existing order instance
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            
            # ✅ ADD ACTIVITY LOG FOR ORDER UPDATE
            ActivityLog.objects.create(
                activity_type='order_updated',
                description=f'Order updated: #{order.order_id} status changed to {order.status}',
                user=request.user,
                order_id=order.id
            )
            
            messages.success(request, f"Order {order.order_id} updated successfully.")
            return redirect('order_dashboard')
    
    else:
        form = OrderForm() # Empty form for the modal
    
       # === REAL-TIME STATS ===
    
    # 1. Total Orders: Count everything
    total_orders = Order.objects.all().count()
    
    # 2. Pending: Count ALL orders EXCEPT 'completed'
    # This includes: Sample Preparing, Production Starts, Quality Checking, Ready for Shipment, and Shipped
    pending = Order.objects.exclude(status='completed').count()
    
    # 3. Shipped: Count orders with specific status 'shipped'
    shipped = Order.objects.filter(status='shipped').count()
    
    # 4. Completed: Count orders with specific status 'completed'
    completed = Order.objects.filter(status='completed').count()

    return render(request, 'orders.html', {
        'orders': orders,
        'form': form,
        'total_orders': total_orders,
        'pending': pending,
        'shipped': shipped,
        'completed': completed,
    })
    
def add_order_for_client(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    
    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            print("Form errors:", form.errors)  # 👈 Add this
            order = form.save(commit=False)
            order.client = client  # Link to client
            order.save()
            
            # ✅ ADD ACTIVITY LOG FOR NEW ORDER
            ActivityLog.objects.create(
                activity_type='order_created',
                description=f'New order created: #{order.order_id} for {client.name}',
                user=request.user,
                order_id=order.id
            )
            
            print("✅ Order saved:", order.order_id)
            messages.success(request, f"Order {order.order_id} added successfully for {client.name}!")
            return redirect('order_dashboard')
    else:
        form = OrderForm()

    return render(request, 'add_order.html', {
        'form': form,
        'client': client
    })
from django.shortcuts import render

@login_required
def inventory_dashboard(request):
    if request.method == 'POST':
        # --- DELETE ---
        if 'delete_material' in request.POST:
            material_id = request.POST.get('material_id')
            try:
                Material.objects.filter(id=material_id).delete()
                
                #Activity
                ActivityLog.objects.create(
                    activity_type = 'material_deleted',
                    description = f'Material deleted : {material.name}',
                    user = request.user,
                    material_id = material.id
                    
                )
                
                messages.success(request, "Material deleted successfully.")
            except Exception as e:
                messages.error(request, "Failed to delete material.")

        # --- EDIT ---
        elif 'edit_material' in request.POST:
            material_id = request.POST.get('material_id')
            try:
                material = Material.objects.get(id=material_id)
                material.name = request.POST['name'].strip()
                material.quantity = Decimal(request.POST['quantity'])
                material.unit = request.POST['unit']
                material.max_quantity = Decimal(request.POST['max_quantity'])
                material.threshold = Decimal(request.POST['threshold'])
                material.save()
                
                #ACTIvity
                ActivityLog.objects.create(
                    activity_type = 'material_updated',
                    description = f'Material Updated : {material.name}',
                    user = request.user,
                    material_id = material.id
                )
                
                messages.success(request, "Material updated successfully.")
            except Material.DoesNotExist:
                messages.error(request, "Material not found.")
            except (InvalidOperation, ValueError):
                messages.error(request, "Invalid number format in quantity fields.")
            except Exception as e:
                messages.error(request, f"Error updating material: {str(e)}")

        # --- ADD (only if NOT edit/delete) ---
        elif 'name' in request.POST and 'quantity' in request.POST:
            try:
                material = Material(
                    name=request.POST['name'].strip(),
                    quantity=Decimal(request.POST['quantity']),
                    unit=request.POST['unit'],
                    max_quantity=Decimal(request.POST['max_quantity']),
                    threshold=Decimal(request.POST['threshold'])
                )
                material.save()
                
                #Activity
                ActivityLog.objects.create(
                    activity_type = 'material_record',
                    description = f'New Material added : {material.name}',
                    user = request.user,
                    material_id = material.id
                )
                
                messages.success(request, f"Material '{material.name}' added successfully.")
            except (InvalidOperation, ValueError):
                messages.error(request, "Invalid number format in quantity fields.")
            except Exception as e:
                messages.error(request, f"Failed to add material: {str(e)}")

        return redirect('inventory_dashboard')
    
    # ... GET logic ...

        # === HANDLE GET: FILTERING & SEARCH ===
    materials = Material.objects.all()
    search_query = request.GET.get('search')
    status_filter = request.GET.get('status')

    # Apply search
    if search_query:
        materials = materials.filter(name__icontains=search_query)

    # Apply status filter
    if status_filter == 'out_of_stock':
        materials = materials.filter(quantity=0)
    elif status_filter == 'low_stock':
        materials = materials.filter(quantity__gt=0, quantity__lt=F('threshold'))
    elif status_filter == 'in_stock':
        materials = materials.filter(quantity__gt=0)

    # Compute stats based on **filtered** materials (optional)
    # Or keep stats for ALL materials — your choice
    all_materials = Material.objects.all()
    total_materials = all_materials.count()
    out_of_stock = all_materials.filter(quantity=0).count()
    # In Stock = everything with quantity > 0
    in_stock = all_materials.filter(quantity__gt=0).count()
    # Low Stock = subset of in_stock
    low_stock = all_materials.filter(quantity__gt=0, quantity__lt=F('threshold')).count()

    # Add computed fields for each material (for cards)
    for mat in materials:
        q = mat.quantity
        t = mat.threshold
        if q <= 0:
            mat.status = 'danger'
        elif q <= t:
            mat.status = 'danger'  # or 'warning' if you prefer
        elif q < t * Decimal('1.5'):
            mat.status = 'warning'
        else:
            mat.status = 'fill'

        max_q = max(mat.max_quantity, Decimal('1'))
        mat.bar_width = min(100, int((q / max_q) * 100))
        mat.bar_class = mat.status
        mat.show_warning = q < t

    context = {
        'materials': materials,
        'total_materials': total_materials,
        'in_stock': in_stock,
        'low_stock': low_stock,
        'out_of_stock': out_of_stock,
    }
    return render(request, 'inventory.html', context)

@login_required
def finance_dashboard(request):
    if request.method == 'POST':
        
         # ✅ Handle Edit Invoice
        if 'edit_invoice' in request.POST:
            try:
                invoice_id = request.POST.get('invoice_id')
                amount = Decimal(request.POST.get('amount'))
                payment_method = request.POST.get('payment_method', '').strip()
                if payment_method not in ['cash', 'bank_transfer', 'credit_card', 'upi', 'other']:
                    payment_method = 'cash'

                invoice = Invoice.objects.get(id=invoice_id)
                invoice.amount = amount
                invoice.payment_method = payment_method
                invoice.save()
                messages.success(request, "Invoice updated successfully.")
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")
            return redirect('finance_dashboard')

        # ✅ Handle Delete Invoice
        elif 'delete_invoice' in request.POST:
            try:
                invoice_id = request.POST.get('invoice_id')
                invoice = Invoice.objects.get(id=invoice_id)
                invoice.delete()
                messages.success(request, "Invoice deleted successfully.")
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")
            return redirect('finance_dashboard')

        # ✅ Handle Record Payment (your existing logic)
        
        elif 'record_payment' in request.POST:
            try:
                order_id = request.POST.get('order_id')
                new_total_paid = Decimal(request.POST.get('paid_amount', '0'))

                order = Order.objects.get(id=order_id)

                if new_total_paid < 0:
                    messages.error(request, "Paid amount cannot be negative.")
                elif new_total_paid > order.payment:
                    messages.error(request, f"Paid amount cannot exceed total invoice amount (${order.payment}).")
                else:
                    # ✅ DELETE all existing invoices
                    Invoice.objects.filter(order=order).delete()

                    # ✅ ALWAYS create a new invoice — even if $0
                    Invoice.objects.create(
                        order=order,
                        amount=new_total_paid,
                        payment_method='cash'  # or omit if you remove payment_method
                    )
                    
                    # ✅ ADD ACTIVITY LOG
                    ActivityLog.objects.create(
                        activity_type='payment_recorded',
                        description=f'Payment recorded: ${new_total_paid} for order #{order.order_id}',
                        user=request.user,
                        order_id=order.id
                    )

                    messages.success(request, "Payment updated successfully.")
            except (Order.DoesNotExist, ValueError, Exception) as e:
                messages.error(request, f"Error: {str(e)}")
    
            return redirect('finance_dashboard')
    
    search_query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
        
    
    client_invoices = Order.objects.select_related('client').prefetch_related('invoices').annotate(
        total_paid=Coalesce(Sum('invoices__amount'), 0, output_field=DecimalField()),
        db_remaining=F('payment') - Coalesce(Sum('invoices__amount'), 0, output_field=DecimalField())
    )
    
    # Apply search filter
    if search_query:
        client_invoices = client_invoices.filter(
            Q(client__name__icontains=search_query) |
            Q(client__id__icontains=search_query) |
            Q(order_id__icontains=search_query)
        )
    
    # Apply status filter
    if status_filter:
        if status_filter == 'paid':
            client_invoices = client_invoices.filter(db_remaining__lte=0)
        elif status_filter == 'partial':
            client_invoices = client_invoices.filter(db_remaining__gt=0, total_paid__gt=0)
        elif status_filter == 'pending':
            client_invoices = client_invoices.filter(total_paid=0)

    # ✅ Calculate stats AFTER client_invoices is defined
    # Calculate stats
    total_invoices = client_invoices.count()
    paid_invoices = client_invoices.filter(db_remaining__lte=0).count()
    unpaid_invoices = total_invoices - paid_invoices

    context = {
    'client_invoices': client_invoices,
    'vendor_bills': [],
    'total_invoices': total_invoices,
    'paid_invoices': paid_invoices,
    'unpaid_invoices': unpaid_invoices,
}
    return render(request, 'finance.html', context)
        
            # try:
            #     order_id = request.POST.get('order_id') 
            #     amount = Decimal(request.POST.get('paid_amount'))
            #     # ✅ Fixed: clean and validate
            #     payment_method = request.POST.get('payment_method', '').strip()
            #     if payment_method not in ['cash', 'bank_transfer', 'credit_card', 'upi', 'other']:
            #         payment_method = 'cash'  # fallback
                
            #     print(">>> SAVING PAYMENT METHOD:", repr(payment_method))

            #     order = Order.objects.get(id=order_id)
            #     total_paid = order.invoices.aggregate(total=Sum('amount'))['total'] or 0
            #     remaining = order.payment - total_paid

            #     if amount <= 0:
            #         messages.error(request, "Amount must be greater than zero.")
            #     elif amount > remaining:
            #         messages.error(request, f"Amount exceeds remaining balance (₹{remaining}).")
            #     else:
            #         Invoice.objects.create(
            #             order=order,
            #             amount=amount,
            #             payment_method=payment_method
            #         )
            #         messages.success(request, "Payment recorded and invoice created.")
            # except Exception as e:
            #     messages.error(request, f"Error: {str(e)}")
            
            # # ✅ ALWAYS return after POST
            # return redirect('finance_dashboard')

       

    # ✅ Use a DIFFERENT name for the annotation
    client_invoices = Order.objects.select_related('client').prefetch_related('invoices').annotate(
        total_paid=Coalesce(Sum('invoices__amount'), 0, output_field=DecimalField()),
        db_remaining=F('payment') - Coalesce(Sum('invoices__amount'), 0, output_field=DecimalField())
    )
    context = {
        'client_invoices': client_invoices,
        'vendor_bills': [],
    }
    return render(request, 'finance.html', context)

def client_search_api(request):
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse([], safe=False)
    
    clients = Client.objects.filter(
        Q(name__icontains=query) | Q(email__icontains=query)
    )[:10]  # Limit to 10 results

    results = [
        {
            'id': client.id,
            'display': f"CL-{client.id} – {client.name}",
            'name': client.name,
            'email': client.email,
        }
        for client in clients
    ]
    return JsonResponse(results, safe=False)

@require_http_methods(["GET"])
def get_material_vendors(request, material_id):
    try:
        material = Material.objects.get(id=material_id)
        vendors = list(material.vendors.values('id', 'name'))
        return JsonResponse({'vendors': vendors})
    except Material.DoesNotExist:
        return JsonResponse({'error': 'Material not found'}, status=404)


# views.py
def view_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    order = invoice.order  # ✅ Get related order

    # ✅ Calculate total paid and remaining
    total_paid = order.invoices.aggregate(total=models.Sum('amount'))['total'] or 0
    remaining = order.payment - total_paid
    
    bank_name , iban = get_bank_details(invoice_id)

    # ✅ Generate random bank + IBAN
    # banks = [
    #     "Global Trust Bank",
    #     "Penta Financial Services",
    #     "Horizon Capital Bank",
    #     "Summit National Bank",
    #     "Vertex Banking Group"
    # ]
    # ibans = [
    #     "DE89370400440532013000",
    #     "FR1420041010050500013M02606",
    #     "GB29NWBK60161331926819",
    #     "IT60X0542811101000000123456",
    #     "ES9121000418450200051332"
    # ]
    # bank_name = random.choice(banks)
    # iban = random.choice(ibans)

    # ✅ PASS ALL REQUIRED VARIABLES TO TEMPLATE
    context = {
        'invoice': invoice,
        'order': order,  # ✅ Needed for client/order info
        'paid_amount': total_paid,  # ✅ For Payment Summary
        'remaining_amount': remaining,  # ✅ For Remaining & Due Amount
        'bank_name': bank_name,  # ✅ For Bank Details
        'iban': iban,  # ✅ For Bank Details
    }

    return render(request, 'invoice_detail.html', context)

def download_invoice_pdf(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    order = invoice.order

    # ✅ Calculate paid & remaining (same as view_invoice)
    total_paid = order.invoices.aggregate(total=models.Sum('amount'))['total'] or 0
    remaining = order.payment - total_paid
    
    bank_name , iban = get_bank_details(invoice_id)
    
    # # ✅ Generate bank + IBAN (same as view_invoice)
    # banks = [
    #     "Global Trust Bank",
    #     "Penta Financial Services",
    #     "Horizon Capital Bank",
    #     "Summit National Bank",
    #     "Vertex Banking, Ltd."
    # ]
    # ibans = [
    #     "DE89370400440532013000",
    #     "FR1420041010050500013M02606",
    #     "GB29NWBK60161331926819",
    #     "IT60X0542811101000000123456",
    #     "ES9121000418450200051332"
    # ]
    # bank_name = random.choice(banks)
    # iban = random.choice(ibans)

    # ✅ PASS FULL CONTEXT (critical!)
    context = {
        'invoice': invoice,
        'order': order,
        'paid_amount': total_paid,
        'remaining_amount': remaining,
        'bank_name': bank_name,
        'iban': iban,
    }

    # 🔸 Use the SAME template as your web view!
    # If your web uses 'invoice_detail.html', use that — NOT 'invoice_pdf.html'
    html_content = render_to_string('invoice_detail.html', context)

    # Rest of your WeasyPrint logic (unchanged)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as html_file:
        html_file.write(html_content)
        html_path = html_file.name

    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as pdf_file:
        pdf_path = pdf_file.name

    try:
        WEASYPRINT_PATH = r"D:\project1\weasyprint-windows\dist\weasyprint.exe"
        result = subprocess.run(
            [WEASYPRINT_PATH, html_path, pdf_path],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            print("WeasyPrint Error:", result.stderr)
            messages.error(request, "Failed to generate PDF.")
            return redirect('finance_dashboard')

        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()

        response = HttpResponse(pdf_data, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Invoice_INV-{invoice.id}.pdf"'
        return response

    except subprocess.TimeoutExpired:
        messages.error(request, "PDF generation timed out.")
        return redirect('finance_dashboard')
    except FileNotFoundError:
        messages.error(request, "WeasyPrint executable not found.")
        return redirect('finance_dashboard')
    finally:
        for path in [html_path, pdf_path]:
            if os.path.exists(path):
                os.remove(path)

def admin_login(request):
    """
    Admin login view with custom template
    """
    # If user is already logged in, redirect to dashboard
    if request.user.is_authenticated:
        return redirect('main_dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Debug: Print credentials to console (remove in production)
        print(f"Login attempt - Username: {username}, Password: {'*' * len(password)}")
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_staff:  # Ensure only staff/admin users can login
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect('main_dashboard')  # Make sure this URL name matches your main dashboard
            else:
                messages.error(request, "Access denied. Admin privileges required.")
        else:
            messages.error(request, "Invalid username or password.")
    
    return render(request, 'admin_login.html')