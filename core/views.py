from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Client, Invoice, Order, Material, ActivityLog, Batch
from .forms import ClientForm, OrderForm
from  django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Sum, F, Q 
from django.db.models import F
from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Invoice, ActivityLog, Order 
from django.contrib.auth.decorators import login_required
from .models import Material, ActivityLog
from .models import Client, Order, Material, Invoice
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
    
    # ✅ NEW: Calculate production stats
    in_production = Order.objects.filter(status__in=['production_starts', 'quality_checking']).count()
    
    # ✅ NEW: Calculate total revenue
    from django.db.models import Sum
    total_revenue_data = Order.objects.aggregate(total=Sum('payment'))
    total_revenue = int(total_revenue_data['total'] or 0)
    
    # ✅ NEW: Get recent orders for the table
    recent_orders = Order.objects.select_related('client').order_by('-created_at')[:5]
    
    # ✅ GET RECENT ACTIVITIES FROM ACTIVITY LOG - WITH COMPLETE ICON MAPPING
    recent_activities = []
    activity_logs = ActivityLog.objects.order_by('-created_at')[:8]
    
    for log in activity_logs:
        # Map activity types to icons and colors
        # Map activity types to icons and colors (OPTIMIZED FOR DARK MODE)
        if log.activity_type in ['client_created', 'client_updated']:
            icon = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>'
            color = 'rgba(56, 189, 248, 0.25)' # Bright Sky Blue
        elif log.activity_type == 'client_deleted':
            icon = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><line x1="3" y1="20" x2="21" y2="20"></line></svg>'
            color = 'rgba(248, 113, 113, 0.25)' # Bright Red
        elif log.activity_type in ['order_created', 'order_updated']:
            icon = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path></svg>'
            color = 'rgba(129, 140, 248, 0.25)' # Bright Indigo
        elif log.activity_type == 'order_deleted':
            icon = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><line x1="3" y1="20" x2="21" y2="20"></line></svg>'
            color = 'rgba(248, 113, 113, 0.25)' # Bright Red
        elif log.activity_type == 'payment_recorded':
            icon = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="5" width="20" height="14" rx="2"></rect><line x1="6" y1="12" x2="6" y2="12"></line><line x1="10" y1="12" x2="14" y2="12"></line><line x1="18" y1="12" x2="18" y2="12"></line></svg>'
            color = 'rgba(52, 211, 153, 0.25)' # Bright Emerald
        elif log.activity_type in ['material_created', 'material_updated']:
            icon = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path></svg>'
            color = 'rgba(251, 191, 36, 0.25)' # Bright Amber
        elif log.activity_type == 'material_deleted':
            icon = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path><line x1="3" y1="20" x2="21" y2="20"></line></svg>'
            color = 'rgba(248, 113, 113, 0.25)' # Bright Red
        elif log.activity_type == 'batch_created':
            icon = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path></svg>'
            color = 'rgba(167, 139, 250, 0.25)' # Bright Violet
        elif log.activity_type == 'batch_completed':
            icon = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>'
            color = 'rgba(52, 211, 153, 0.25)' # Bright Emerald
        else:
            icon = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle></svg>'
            color = 'rgba(148, 163, 184, 0.25)' # Bright Slate
        
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
        'in_production': in_production,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
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
    
    # Handle DELETE
    if request.method == "POST" and "delete_client" in request.POST:
        client_id = request.POST.get("client_id")
        client = get_object_or_404(Client, id=client_id)
        client_name = client.name
        client.delete()
        
        # activity log
        ActivityLog.objects.create(
            activity_type='client_deleted',
            description=f'Client deleted : {client_name}',
            user=request.user,
            client_id=client.id
        )
        
        messages.success(request, f"Client '{client_name}' deleted successfully.")
        return redirect('client_dashboard')

    # Handle CREATE/UPDATE (POST) - ONLY if not a delete
    if request.method == "POST" and "delete_client" not in request.POST:
        client_id = request.POST.get("client_id")
        if client_id:
            client = get_object_or_404(Client, id=client_id)
            form = ClientForm(request.POST, request.FILES, instance=client)
        else:
            form = ClientForm(request.POST, request.FILES)

        if form.is_valid():
            client = form.save()
            action = "updated" if client_id else "added"
            
            # activity log
            if action == "added":
                ActivityLog.objects.create(
                    activity_type='client_created',
                    description=f'New client created : {client.name}',
                    user=request.user,
                    client_id=client.id
                )
            else:
                ActivityLog.objects.create(
                    activity_type='client_updated',
                    description=f'Client Updated : {client.name}',
                    user=request.user,
                    client_id=client.id
                )
            
            messages.success(request, f"Client {action} successfully.")
            return redirect('client_dashboard')
        # If form is invalid, it will fall through to render below
    else:
        form = ClientForm()

    # === FILTER & SEARCH LOGIC ===
    clients = Client.objects.all()
    search = request.GET.get('search')
    status = request.GET.get('status')

    # === SEARCH LOGIC ===
    if search:
        query_filter = (
            Q(name__istartswith=search) | 
            Q(name__icontains=" " + search) | 
            Q(company__istartswith=search)
        )
        
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
            # Use commit=False so we can set the status before saving to DB
            order = form.save(commit=False)
            order.client = client
            order.status = 'sample_preparing'
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

from django.db.models import F
from decimal import Decimal, InvalidOperation
from django.db.models import F
from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Material, ActivityLog

@login_required
def inventory_dashboard(request):
    if request.method == 'POST':
        
        #  DELETE
        if 'delete_material' in request.POST:
            material_id = request.POST.get('material_id')
            try:
                material = Material.objects.get(id=material_id)
                material_name = material.name
                material.delete()
                
                ActivityLog.objects.create(
                    activity_type='material_deleted',
                    description=f'Material deleted: {material_name}',
                    user=request.user,
                    material_id=material_id
                )
                messages.success(request, "Material deleted successfully.")
            except Exception as e:
                messages.error(request, f"Failed to delete: {str(e)}")
            return redirect('inventory_dashboard')

        #  EDIT OR ADD - Check if material_id exists
        material_id = request.POST.get('material_id', '').strip()
        
        if material_id:
            # --- EDIT EXISTING MATERIAL ---
            try:
                # Prepare update data
                name = request.POST.get('name', '').strip()
                quantity = Decimal(request.POST.get('quantity', 0))
                unit = request.POST.get('unit', '')
                max_quantity = Decimal(request.POST.get('max_quantity', 0))
                threshold = Decimal(request.POST.get('threshold', 0))
                description = request.POST.get('description', '').strip()
                
                # Use update() to avoid field conflicts
                Material.objects.filter(id=material_id).update(
                    name=name,
                    quantity=quantity,
                    unit=unit,
                    max_quantity=max_quantity,
                    threshold=threshold,
                    description=description
                )
                
                # Get the updated material for logging
                material = Material.objects.get(id=material_id)
                
                ActivityLog.objects.create(
                    activity_type='material_updated',
                    description=f'Material updated: {material.name}',
                    user=request.user,
                    material_id=material.id
                )
                messages.success(request, f" Successfully updated {material.name}!")
                
            except Exception as e:
                messages.error(request, f"Failed to update: {str(e)}")
        else:
            # --- ADD NEW MATERIAL ---
            try:
                material = Material(
                    name=request.POST.get('name', '').strip(),
                    quantity=Decimal(request.POST.get('quantity')),
                    unit=request.POST.get('unit', ''),
                    max_quantity=Decimal(request.POST.get('max_quantity', 0)),
                    threshold=Decimal(request.POST.get('threshold', 0))
                )
                
                # Only add description if field exists
                try:
                    material.description = request.POST.get('description', '').strip()
                except AttributeError:
                    pass
                
                material.save()
                
                ActivityLog.objects.create(
                    activity_type='material_created',
                    description=f'New material added: {material.name}',
                    user=request.user,
                    material_id=material.id
                )
                messages.success(request, f"✅ Material '{material.name}' added successfully!")
                
            except Exception as e:
                messages.error(request, f"Failed to add: {str(e)}")

        return redirect('inventory_dashboard')
    
    # === GET REQUEST ===
    materials = Material.objects.all()
    search_query = request.GET.get('search')
    status_filter = request.GET.get('stock_status')

    if search_query:
        materials = materials.filter(name__icontains=search_query)

    if status_filter == 'out_of_stock':
        materials = materials.filter(quantity=0)
    elif status_filter == 'low_stock':
        materials = materials.filter(quantity__gt=0, quantity__lt=F('threshold'))
    elif status_filter == 'in_stock':
        materials = materials.filter(quantity__gt=0)

    all_materials = Material.objects.all()
    total_materials = all_materials.count()
    out_of_stock = all_materials.filter(quantity=0).count()
    in_stock = all_materials.filter(quantity__gt=0).count()
    low_stock = all_materials.filter(quantity__gt=0, quantity__lt=F('threshold')).count()

    context = {
        'materials': materials,
        'total_materials': total_materials,
        'in_stock': in_stock,
        'low_stock_materials': low_stock,
        'out_of_stock_materials': out_of_stock,
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


def view_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    order = invoice.order  

    # Calculate total paid and remaining
    total_paid = order.invoices.aggregate(total=models.Sum('amount'))['total'] or 0
    remaining = order.payment - total_paid
    
    # BANK DETAILS FOR COSMO ENTERPRISES
    # 
    bank_name = "Cosmo Enterprises Official Account"
    iban = "PK36 SCBL 0000 0011 2345 6702"  #     IBAN
    account_no = "1123456702"                #     Account No
    branch = "Main Corporate Branch"         #     Branch

    context = {
        'invoice': invoice,
        'order': order,  
        'paid_amount': total_paid,  
        'remaining_amount': remaining,  
        'bank_name': bank_name,  
        'iban': iban,  
        'account_no': account_no,
        'branch': branch,
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

@login_required
def batch_dashboard(request):
    # 1. Handle POST requests (Create, Update, Delete)
    if request.method == 'POST':
        
        # --- CREATE NEW BATCH ---
        if 'create_batch' in request.POST:
            order_id = request.POST.get('order_id')
            operator = request.POST.get('operator', '').strip()
            
            try:
                order = Order.objects.get(id=order_id)
                # Prevent creating multiple batches for the same order
                if hasattr(order, 'batch'):
                    messages.error(request, f"Order {order.order_id} already has an active batch.")
                elif not operator:
                    messages.error(request, "Operator name is required.")
                else:
                    Batch.objects.create(order=order, operator=operator)
                    
                    # 🪄 MAGIC: Automatically update Order Status to Production
                    order.status = 'production_starts'
                    order.save()
                    
                    messages.success(request, f"Batch started successfully for {order.order_id}.")
            except Order.DoesNotExist:
                messages.error(request, "Order not found.")
            return redirect('batch_dashboard')

        # --- UPDATE BATCH STATUS (Complete / Fail) ---
        elif 'update_status' in request.POST:
            batch_id = request.POST.get('batch_id')
            new_status = request.POST.get('status')
            notes = request.POST.get('notes', '')
            
            try:
                batch = Batch.objects.get(id=batch_id)
                batch.status = new_status
                batch.notes = notes
                
                # If completed or failed, record the end time and update Order
                if new_status in ['completed', 'failed']:
                    batch.end_time = timezone.now()
                    
                    # 🪄 MAGIC: Automatically update Order Status based on Batch result
                    if new_status == 'completed':
                        batch.order.status = 'quality_checking'
                        batch.order.save()
                    elif new_status == 'failed':
                        batch.order.status = 'sample_preparing' # Revert for rework
                        batch.order.save()
                
                batch.save()
                messages.success(request, f"Batch {batch.batch_number} marked as {new_status}.")
            except Batch.DoesNotExist:
                messages.error(request, "Batch not found.")
            return redirect('batch_dashboard')

                # --- 🏆 RETRY FAILED BATCH ---
        elif 'retry_batch' in request.POST:
            batch_id = request.POST.get('batch_id')
            try:
                batch = Batch.objects.get(id=batch_id)
                
                # Ensure we only retry if it's actually failed
                if batch.status == 'failed':
                    # 1. Reset the Batch back to In Progress
                    batch.status = 'in_progress'
                    batch.end_time = None  # Clear the end time
                    batch.notes = "Retried: " + (batch.notes or "") # Keep history of why it failed
                    batch.save()
                    
                    # 🪄 MAGIC: Revert the Order Status back to Production Starts
                    batch.order.status = 'production_starts'
                    batch.order.save()
                    
                    messages.success(request, f"Batch {batch.batch_number} has been reset to In Progress. Production resumed.")
                else:
                    messages.error(request, "Only failed batches can be retried.")
                    
            except Batch.DoesNotExist:
                messages.error(request, "Batch not found.")
            return redirect('batch_dashboard')
        
        # --- DELETE BATCH ---
        elif 'delete_batch' in request.POST:
            batch_id = request.POST.get('batch_id')
            try:
                Batch.objects.filter(id=batch_id).delete()
                messages.success(request, "Batch deleted successfully.")
            except Exception as e:
                messages.error(request, "Failed to delete batch.")
            return redirect('batch_dashboard')

    # 2. Handle GET requests (Display Data)
    
    # Base query: Get all batches and pull related Order & Client data efficiently
    batches = Batch.objects.select_related('order', 'order__client').all()
    
    # --- SEARCH & FILTER LOGIC ---
    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '').strip()

    if search_query:
        batches = batches.filter(
            Q(batch_number__icontains=search_query) |
            Q(order__order_id__icontains=search_query) |
            Q(operator__icontains=search_query)
        )

    if status_filter:
        batches = batches.filter(status=status_filter)

    # --- CALCULATE STATS (Based on ALL batches, not just filtered) ---
    all_batches = Batch.objects.all()
    total_batches = all_batches.count()
    in_progress = all_batches.filter(status='in_progress').count()
    completed = all_batches.filter(status='completed').count()
    failed = all_batches.filter(status='failed').count()

    # --- GET AVAILABLE ORDERS FOR "START BATCH" MODAL ---
    # Only show orders that are in production and DON'T have a batch yet
    available_orders = Order.objects.filter(
        status__in=['sample_preparing', 'production_starts', 'quality_checking']
    ).exclude(batch__isnull=False)

    context = {
        'batches': batches,
        'total_batches': total_batches,
        'in_progress': in_progress,
        'completed': completed,
        'failed': failed,
        'available_orders': available_orders,
    }

    return render(request, 'batch.html', context)


@login_required
def advance_order_status(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        
        # Define the logical progression
        status_flow = {
            'quality_checking': 'ready_for_shipment',
            'ready_for_shipment': 'shipped',
            'shipped': 'completed'
        }
        
        next_status = status_flow.get(order.status)
        if next_status:
            order.status = next_status
            order.save()
            messages.success(request, f"Order {order.order_id} advanced to {next_status.replace('_', ' ').title()}.")
        else:
            messages.error(request, "Cannot advance this order further.")
            
    return redirect('order_dashboard')


import stripe
import json
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.utils import timezone

# ==========================================
# STRIPE ADMIN VIEWS
# ==========================================

# Set your Stripe API key
stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
def generate_stripe_link(request, invoice_id):
    """Admin generates a Stripe Payment Link to share with the client"""
    invoice = get_object_or_404(Invoice, id=invoice_id)
    order = invoice.order
    
    try:
        # Create a Stripe Payment Link with custom fields for tracking
        payment_link = stripe.PaymentLink.create(
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f'Order #{order.order_id} - {order.fabric_type}',
                        'description': f'Invoice #{invoice.invoice_id} for {order.client.name}',
                    },
                    'unit_amount': int(invoice.amount * 100), # Stripe uses cents
                },
                'quantity': 1,
            }],
            metadata={
                'invoice_id': str(invoice.id),
                'invoice_number': invoice.invoice_id,
                'order_id': str(order.id),
                'client_name': order.client.name,
            },
            # Custom fields to appear on the payment page
            after_completion={
                'type': 'redirect',
                'redirect': {
                    'url': request.build_absolute_uri('/finance/')
                }
            }
        )
        
        # Save the link to the database
        invoice.stripe_payment_link = payment_link.url
        invoice.save()
        
        ActivityLog.objects.create(
            activity_type='payment_link_generated',
            description=f'Payment link generated for Invoice #{invoice.invoice_id} - Amount: ${invoice.amount}',
            user=request.user,
            order_id=order.id
        )
        
        messages.success(request, "✅ Payment link generated successfully! Share this link with the client.")
        
    except Exception as e:
        messages.error(request, f"Stripe Error: {str(e)}")
        
    return redirect('finance_dashboard')

@csrf_exempt
def stripe_webhook(request):
    """Stripe calls this automatically when the client pays"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)

    # Handle checkout.session.completed (Payment Link completion)
    if event['type'] == 'checkout.session.completed':
        try:
            session = event['data']['object']
            metadata = session.get('metadata', {})
            invoice_id = metadata.get('invoice_id')
            
            if invoice_id:
                try:
                    invoice = Invoice.objects.get(id=invoice_id)
                    invoice.stripe_payment_status = 'paid'
                    invoice.save()
                    
                    # Create activity log
                    ActivityLog.objects.create(
                        activity_type='payment_recorded',
                        description=f'Stripe payment received for Invoice #{invoice.invoice_id}',
                        user=None,
                        order_id=invoice.order.id if invoice.order else None
                    )
                except Invoice.DoesNotExist:
                    pass
                except Exception as log_error:
                    pass
                    
        except Exception as e:
            pass

    # Handle payment_intent.succeeded (Alternative Payment Link event)
    elif event['type'] == 'payment_intent.succeeded':
        try:
            payment_intent = event['data']['object']
            metadata = payment_intent.get('metadata', {})
            invoice_id = metadata.get('invoice_id')
            
            if invoice_id:
                try:
                    invoice = Invoice.objects.get(id=invoice_id)
                    invoice.stripe_payment_status = 'paid'
                    invoice.save()
                    
                    # Create activity log
                    ActivityLog.objects.create(
                        activity_type='payment_recorded',
                        description=f'Stripe payment received for Invoice #{invoice.invoice_id}',
                        user=None,
                        order_id=invoice.order.id if invoice.order else None
                    )
                except Invoice.DoesNotExist:
                    pass
                except Exception as log_error:
                    pass
                    
        except Exception as e:
            pass

    return HttpResponse(status=200)


@login_required
def sync_stripe_payment(request, invoice_id):
    """Manual endpoint to check and sync Stripe payment status"""
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    try:
        # Query checkout sessions (Payment Links create checkout sessions)
        sessions = stripe.checkout.Session.list(limit=100)
        payment_found = False
        
        # Search through checkout sessions
        for session in sessions:
            try:
                # Get metadata from session (it's a Stripe object, not a dict)
                session_metadata = session.metadata
                
                # Access metadata as object attributes, not dictionary
                found_invoice_id = getattr(session_metadata, 'invoice_id', None) if session_metadata else None
                
                if found_invoice_id == str(invoice_id):
                    # If payment was successful
                    if session.payment_status == 'paid':
                        invoice.stripe_payment_status = 'paid'
                        invoice.save()
                        
                        ActivityLog.objects.create(
                            activity_type='payment_recorded',
                            description=f'Stripe payment verified for Invoice #{invoice.invoice_id}',
                            user=request.user,
                            order_id=invoice.order.id if invoice.order else None
                        )
                        
                        messages.success(request, " Payment confirmed! Invoice marked as paid.")
                        payment_found = True
                        break
                    elif session.payment_status == 'unpaid':
                        messages.warning(request, " Payment not yet received. Please check with customer.")
                        payment_found = True
                        break
            except Exception:
                continue
        
        # If no checkout session found, also check payment intents as fallback
        if not payment_found:
            payment_intents = stripe.PaymentIntent.list(limit=100)
            
            for pi in payment_intents:
                try:
                    # Access metadata as object attributes, not dictionary
                    pi_metadata = pi.metadata
                    found_invoice_id = getattr(pi_metadata, 'invoice_id', None) if pi_metadata else None
                    
                    if found_invoice_id == str(invoice_id):
                        if pi.status == 'succeeded':
                            invoice.stripe_payment_status = 'paid'
                            invoice.save()
                            
                            ActivityLog.objects.create(
                                activity_type='payment_recorded',
                                description=f'Stripe payment verified for Invoice #{invoice.invoice_id}',
                                user=request.user,
                                order_id=invoice.order.id if invoice.order else None
                            )
                            
                            messages.success(request, " Payment confirmed! Invoice marked as paid.")
                            payment_found = True
                            break
                except Exception:
                    continue
        
        if not payment_found:
            messages.warning(request, " No payment activity found. Verify that payment was completed on Stripe checkout page.")
            
    except Exception as e:
        messages.error(request, f"Error checking payment: {str(e)}")
    
    return redirect('finance_dashboard')