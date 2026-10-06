from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Sum, Count, ProtectedError
from django.db import IntegrityError
from django.http import HttpResponse
from .models import Employee, Asset, Assignment, Maintenance, Category
import csv


# =============================================================
# AUTH HELPERS
# =============================================================

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not username or not password:
            messages.error(request, 'Please enter both username and password.')
            return render(request, 'assets/login.html')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Block superusers / staff from AssetFlow panel — they use /admin/
            if user.is_superuser or user.is_staff:
                messages.error(
                    request,
                    'Admin accounts must use the Django Admin panel at /admin/. '
                    'Please register a normal AssetFlow account.'
                )
                return render(request, 'assets/login.html')
            login(request, user)
            next_url = request.GET.get('next')
            if next_url and next_url.startswith('/') and next_url not in ('/login/', '/'):
                return redirect(next_url)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password. If you are new, please register first.')

    return render(request, 'assets/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


def register_view(request):
    """Create a normal AssetFlow application user (non-superuser)."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()

        # Basic validation
        if not username or not password1 or not password2:
            messages.error(request, 'Username and password are required.')
            return render(request, 'assets/register.html')

        if len(username) < 3:
            messages.error(request, 'Username must be at least 3 characters long.')
            return render(request, 'assets/register.html')

        if len(password1) < 6:
            messages.error(request, 'Password must be at least 6 characters long.')
            return render(request, 'assets/register.html')

        if password1 != password2:
            messages.error(request, 'Passwords do not match. Please try again.')
            return render(request, 'assets/register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, f'Username "{username}" is already taken. Please choose another.')
            return render(request, 'assets/register.html')

        # Create a NORMAL user — is_superuser=False, is_staff=False
        User.objects.create_user(
            username=username,
            password=password1,
            first_name=first_name,
            last_name=last_name,
            is_staff=False,
            is_superuser=False,
        )

        messages.success(
            request,
            f'Account "{username}" created successfully! You can now log in.'
        )
        return redirect('login')

    return render(request, 'assets/register.html')


# =============================================================
# DASHBOARD
# =============================================================

@login_required(login_url='login')
def dashboard(request):

    total_assets = Asset.objects.count()
    total_employees = Employee.objects.count()
    total_assignments = Assignment.objects.count()
    total_maintenance = Maintenance.objects.count()

    available_assets = Asset.objects.filter(status='Available').count()
    assigned_assets = Asset.objects.filter(status='Assigned').count()
    maintenance_assets = Asset.objects.filter(status='Maintenance').count()
    retired_assets = Asset.objects.filter(status='Retired').count()

    recent_returns = Assignment.objects.filter(
        returned_date__isnull=False
    ).select_related('asset', 'employee').order_by('-returned_date')[:5]

    recent_assignments = Assignment.objects.filter(
        returned_date__isnull=True
    ).select_related('asset', 'employee').order_by('-id')[:5]

    return render(
        request,
        'assets/dashboard.html',
        {
            'total_assets': total_assets,
            'total_employees': total_employees,
            'total_assignments': total_assignments,
            'total_maintenance': total_maintenance,
            'available_assets': available_assets,
            'assigned_assets': assigned_assets,
            'maintenance_assets': maintenance_assets,
            'retired_assets': retired_assets,
            'recent_returns': recent_returns,
            'recent_assignments': recent_assignments,
        }
    )


# =============================================================
# ASSETS
# =============================================================

@login_required(login_url='login')
def assets_list(request):

    assets = Asset.objects.select_related('category').all().order_by('-id')
    categories = Category.objects.all()

    search = request.GET.get("search", "").strip()
    category = request.GET.get("category", "").strip()
    status = request.GET.get("status", "").strip()

    if search:
        assets = assets.filter(
            Q(asset_name__icontains=search) |
            Q(asset_code__icontains=search) |
            Q(brand__icontains=search)
        )

    if category:
        assets = assets.filter(category_id=category)

    if status:
        assets = assets.filter(status=status)

    return render(
        request,
        "assets/assets_list.html",
        {
            "assets": assets,
            "categories": categories,
            "search": search,
            "category": category,
            "status": status,
        }
    )


@login_required(login_url='login')
def add_asset(request):

    categories = Category.objects.all()

    if request.method == "POST":
        asset_name = request.POST.get("asset_name", "").strip()
        asset_code = request.POST.get("asset_code", "").strip()
        category_id = request.POST.get("category", "").strip()
        brand = request.POST.get("brand", "").strip()
        purchase_date = request.POST.get("purchase_date", "").strip()
        purchase_price = request.POST.get("purchase_price", "").strip()
        status = request.POST.get("status", "Available").strip()

        ctx = {"categories": categories, "form_data": request.POST}

        # Validation
        if not asset_name or not asset_code or not category_id or not brand or not purchase_date or not purchase_price:
            messages.error(request, 'All fields are required.')
            return render(request, "assets/add_asset.html", ctx)

        if Asset.objects.filter(asset_code=asset_code).exists():
            messages.error(request, f'Asset code "{asset_code}" already exists. Please use a unique code.')
            return render(request, "assets/add_asset.html", ctx)

        try:
            price = float(purchase_price)
            if price < 0:
                raise ValueError()
        except (ValueError, TypeError):
            messages.error(request, 'Purchase price must be a valid positive number.')
            return render(request, "assets/add_asset.html", ctx)

        # Validate status choices
        valid_statuses = [s[0] for s in Asset.STATUS_CHOICES]
        if status not in valid_statuses:
            status = 'Available'

        try:
            Asset.objects.create(
                asset_name=asset_name,
                asset_code=asset_code,
                category_id=category_id,
                brand=brand,
                purchase_date=purchase_date,
                purchase_price=purchase_price,
                status=status
            )
            messages.success(request, f'Asset "{asset_name}" added successfully.')
            return redirect("assets_list")
        except Exception as e:
            messages.error(request, f'Error adding asset. Please check all fields and try again.')

    return render(request, "assets/add_asset.html", {"categories": categories})


@login_required(login_url='login')
def edit_asset(request, id):

    asset = get_object_or_404(Asset, id=id)
    categories = Category.objects.all()

    if request.method == "POST":
        asset_name = request.POST.get("asset_name", "").strip()
        asset_code = request.POST.get("asset_code", "").strip()
        category_id = request.POST.get("category", "").strip()
        brand = request.POST.get("brand", "").strip()
        purchase_date = request.POST.get("purchase_date", "").strip()
        purchase_price = request.POST.get("purchase_price", "").strip()
        status = request.POST.get("status", "Available").strip()

        ctx = {"asset": asset, "categories": categories}

        if not asset_name or not asset_code or not category_id or not brand or not purchase_date or not purchase_price:
            messages.error(request, 'All fields are required.')
            return render(request, "assets/edit_asset.html", ctx)

        # Check duplicate code (excluding this asset)
        if Asset.objects.filter(asset_code=asset_code).exclude(id=id).exists():
            messages.error(request, f'Asset code "{asset_code}" is already used by another asset.')
            return render(request, "assets/edit_asset.html", ctx)

        try:
            price = float(purchase_price)
            if price < 0:
                raise ValueError()
        except (ValueError, TypeError):
            messages.error(request, 'Purchase price must be a valid positive number.')
            return render(request, "assets/edit_asset.html", ctx)

        # Lifecycle integrity checks on status change
        old_status = asset.status

        # Prevent assigning Retired status directly without a maintenance record transition
        if status == 'Retired' and old_status not in ('Retired', 'Maintenance'):
            # We allow Retired from Maintenance via maintenance flow, but direct edit is allowed by admin
            pass  # Allow direct edit (admin use case)

        # Prevent changing to Available if there's an active assignment
        if status == 'Available' and old_status == 'Assigned':
            active_assignment = Assignment.objects.filter(
                asset=asset, returned_date__isnull=True
            ).exists()
            if active_assignment:
                messages.error(
                    request,
                    f'Cannot mark asset as Available while it has an active assignment. Please return the asset first.'
                )
                return render(request, "assets/edit_asset.html", ctx)

        # Prevent changing to Available if there's an active maintenance
        if status == 'Available' and old_status == 'Maintenance':
            active_maintenance = Maintenance.objects.filter(
                asset=asset, status__in=['Open', 'In Progress']
            ).exists()
            if active_maintenance:
                messages.error(
                    request,
                    f'Cannot mark asset as Available while it has an open maintenance record. Please complete the maintenance first.'
                )
                return render(request, "assets/edit_asset.html", ctx)

        # Prevent assigning a Retired asset
        if old_status == 'Retired' and status == 'Assigned':
            messages.error(request, 'Retired assets cannot be assigned.')
            return render(request, "assets/edit_asset.html", ctx)

        asset.asset_name = asset_name
        asset.asset_code = asset_code
        asset.category_id = category_id
        asset.brand = brand
        asset.purchase_date = purchase_date
        asset.purchase_price = purchase_price
        asset.status = status
        asset.save()

        messages.success(request, f'Asset "{asset_name}" updated successfully.')
        return redirect("assets_list")

    return render(request, "assets/edit_asset.html", {
        "asset": asset,
        "categories": categories
    })


@login_required(login_url='login')
def delete_asset(request, id):

    asset = get_object_or_404(Asset, id=id)

    # Check for related records
    assignment_count = Assignment.objects.filter(asset=asset).count()
    maintenance_count = Maintenance.objects.filter(asset=asset).count()

    if request.method == "POST":
        if assignment_count > 0 or maintenance_count > 0:
            messages.error(
                request,
                f'Cannot delete asset "{asset.asset_name}" — it has {assignment_count} assignment record(s) '
                f'and {maintenance_count} maintenance record(s). '
                f'Consider retiring the asset instead to preserve historical data.'
            )
            return redirect("assets_list")
        name = asset.asset_name
        try:
            asset.delete()
            messages.success(request, f'Asset "{name}" deleted successfully.')
        except ProtectedError:
            messages.error(
                request,
                f'Cannot delete asset "{name}" — it has related records. Please retire it instead.'
            )
        return redirect("assets_list")

    return render(request, "assets/delete_asset.html", {
        "asset": asset,
        "assignment_count": assignment_count,
        "maintenance_count": maintenance_count,
        "has_records": assignment_count > 0 or maintenance_count > 0,
    })


# =============================================================
# EMPLOYEES
# =============================================================

@login_required(login_url='login')
def employees_list(request):

    employees = Employee.objects.all().order_by('-id')
    search = request.GET.get("search", "").strip()

    if search:
        employees = employees.filter(
            Q(name__icontains=search) |
            Q(email__icontains=search) |
            Q(department__icontains=search)
        )

    return render(
        request,
        "assets/employees_list.html",
        {
            "employees": employees,
            "search": search,
        }
    )


@login_required(login_url='login')
def add_employee(request):

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        department = request.POST.get("department", "").strip()
        phone = request.POST.get("phone", "").strip()
        joining_date = request.POST.get("joining_date", "").strip()

        ctx = {"form_data": request.POST}

        if not name or not email or not department or not phone or not joining_date:
            messages.error(request, 'All fields are required.')
            return render(request, "assets/add_employee.html", ctx)

        if Employee.objects.filter(email=email).exists():
            messages.error(request, f'An employee with email "{email}" already exists.')
            return render(request, "assets/add_employee.html", ctx)

        try:
            Employee.objects.create(
                name=name,
                email=email,
                department=department,
                phone=phone,
                joining_date=joining_date
            )
            messages.success(request, f'Employee "{name}" added successfully.')
            return redirect("employees_list")
        except IntegrityError:
            messages.error(request, f'An employee with email "{email}" already exists.')

    return render(request, "assets/add_employee.html")


@login_required(login_url='login')
def edit_employee(request, id):
    employee = get_object_or_404(Employee, id=id)

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        department = request.POST.get("department", "").strip()
        phone = request.POST.get("phone", "").strip()
        joining_date = request.POST.get("joining_date", "").strip()

        ctx = {"employee": employee}

        if not name or not email or not department or not phone or not joining_date:
            messages.error(request, 'All fields are required.')
            return render(request, "assets/edit_employee.html", ctx)

        if Employee.objects.filter(email=email).exclude(id=id).exists():
            messages.error(request, f'Email "{email}" is already used by another employee.')
            return render(request, "assets/edit_employee.html", ctx)

        employee.name = name
        employee.email = email
        employee.department = department
        employee.phone = phone
        employee.joining_date = joining_date
        employee.save()

        messages.success(request, f'Employee "{name}" updated successfully.')
        return redirect("employees_list")

    return render(
        request,
        "assets/edit_employee.html",
        {"employee": employee}
    )


@login_required(login_url='login')
def delete_employee(request, id):
    employee = get_object_or_404(Employee, id=id)

    assignment_count = Assignment.objects.filter(employee=employee).count()

    if request.method == "POST":
        if assignment_count > 0:
            messages.error(
                request,
                f'Cannot delete employee "{employee.name}" — they have {assignment_count} assignment record(s). '
                f'Historical data must be preserved.'
            )
            return redirect("employees_list")
        name = employee.name
        try:
            employee.delete()
            messages.success(request, f'Employee "{name}" deleted successfully.')
        except ProtectedError:
            messages.error(
                request,
                f'Cannot delete employee "{name}" — they have related assignment records.'
            )
        return redirect("employees_list")

    return render(
        request,
        "assets/delete_employee.html",
        {
            "employee": employee,
            "assignment_count": assignment_count,
            "has_records": assignment_count > 0,
        }
    )


# =============================================================
# ASSIGNMENTS
# =============================================================

@login_required(login_url='login')
def assignments_list(request):
    assignments = Assignment.objects.select_related('asset', 'employee').all().order_by('-id')

    search = request.GET.get("search", "").strip()
    status_filter = request.GET.get("status", "").strip()

    if search:
        assignments = assignments.filter(
            Q(asset__asset_name__icontains=search) |
            Q(asset__asset_code__icontains=search) |
            Q(employee__name__icontains=search) |
            Q(employee__department__icontains=search)
        )

    if status_filter == "active":
        assignments = assignments.filter(returned_date__isnull=True)
    elif status_filter == "returned":
        assignments = assignments.filter(returned_date__isnull=False)

    return render(
        request,
        "assets/assignments_list.html",
        {
            "assignments": assignments,
            "search": search,
            "status_filter": status_filter,
        }
    )


@login_required(login_url='login')
def add_assignment(request):
    assets = Asset.objects.filter(status='Available').order_by('asset_name')
    employees = Employee.objects.all().order_by('name')

    if request.method == "POST":
        asset_id = request.POST.get("asset", "").strip()
        employee_id = request.POST.get("employee", "").strip()
        assigned_date = request.POST.get("assigned_date", "").strip()
        remarks = request.POST.get("remarks", "")

        ctx = {"assets": assets, "employees": employees, "form_data": request.POST}

        if not asset_id or not employee_id or not assigned_date:
            messages.error(request, 'Asset, Employee, and Assigned Date are required.')
            return render(request, "assets/add_assignment.html", ctx)

        try:
            asset = get_object_or_404(Asset, id=int(asset_id))
        except (ValueError, Exception):
            messages.error(request, 'Invalid asset selected.')
            return render(request, "assets/add_assignment.html", ctx)

        try:
            employee = get_object_or_404(Employee, id=int(employee_id))
        except (ValueError, Exception):
            messages.error(request, 'Invalid employee selected.')
            return render(request, "assets/add_assignment.html", ctx)

        # Lifecycle validation
        if asset.status == 'Retired':
            messages.error(request, f'Asset "{asset.asset_name}" is retired and cannot be assigned.')
            return render(request, "assets/add_assignment.html", ctx)

        if asset.status == 'Maintenance':
            messages.error(request, f'Asset "{asset.asset_name}" is currently under maintenance and cannot be assigned.')
            return render(request, "assets/add_assignment.html", ctx)

        if asset.status == 'Assigned':
            messages.error(request, f'Asset "{asset.asset_name}" is already assigned. Please return it first.')
            return render(request, "assets/add_assignment.html", ctx)

        if asset.status != 'Available':
            messages.error(request, f'Asset "{asset.asset_name}" is not available for assignment.')
            return render(request, "assets/add_assignment.html", ctx)

        # Prevent duplicate active assignment
        if Assignment.objects.filter(asset=asset, returned_date__isnull=True).exists():
            messages.error(request, f'Asset "{asset.asset_name}" already has an active assignment.')
            return render(request, "assets/add_assignment.html", ctx)

        Assignment.objects.create(
            asset=asset,
            employee=employee,
            assigned_date=assigned_date,
            remarks=remarks
        )

        asset.status = "Assigned"
        asset.save()

        messages.success(request, f'Asset "{asset.asset_name}" assigned to {employee.name} successfully.')
        return redirect("assignments_list")

    return render(
        request,
        "assets/add_assignment.html",
        {
            "assets": assets,
            "employees": employees
        }
    )


@login_required(login_url='login')
def return_asset(request, id):
    assignment = get_object_or_404(Assignment, id=id)

    if assignment.returned_date is not None:
        messages.error(request, 'This asset has already been returned.')
        return redirect("assignments_list")

    if request.method == "POST":
        returned_date = request.POST.get("returned_date", "").strip()

        if not returned_date:
            messages.error(request, 'Return date is required.')
            return render(request, "assets/return_asset.html", {"assignment": assignment})

        assignment.returned_date = returned_date
        assignment.save()

        asset = assignment.asset
        asset.status = "Available"
        asset.save()

        messages.success(request, f'Asset "{asset.asset_name}" has been returned successfully.')
        return redirect("assignments_list")

    return render(
        request,
        "assets/return_asset.html",
        {"assignment": assignment}
    )


# =============================================================
# MAINTENANCE
# =============================================================

@login_required(login_url='login')
def maintenance_list(request):

    maintenance = Maintenance.objects.select_related('asset').all().order_by('-id')

    search = request.GET.get("search", "").strip()
    status = request.GET.get("status", "").strip()

    if search:
        maintenance = maintenance.filter(
            Q(asset__asset_name__icontains=search) |
            Q(asset__asset_code__icontains=search) |
            Q(issue__icontains=search)
        )

    if status:
        maintenance = maintenance.filter(status=status)

    return render(
        request,
        "assets/maintenance_list.html",
        {
            "maintenance": maintenance,
            "search": search,
            "status": status
        }
    )


@login_required(login_url='login')
def add_maintenance(request):

    # Only show assets that can enter maintenance (Available or already Maintenance)
    assets = Asset.objects.filter(
        status__in=['Available', 'Assigned']
    ).order_by('asset_name')

    if request.method == "POST":

        asset_id = request.POST.get("asset", "").strip()
        issue = request.POST.get("issue", "").strip()
        reported_date = request.POST.get("reported_date", "").strip()
        remarks = request.POST.get("remarks", "")

        ctx = {"assets": assets, "form_data": request.POST}

        if not asset_id or not issue or not reported_date:
            messages.error(request, 'Asset, Issue, and Reported Date are required.')
            return render(request, "assets/add_maintenance.html", ctx)

        try:
            asset = get_object_or_404(Asset, id=int(asset_id))
        except (ValueError, Exception):
            messages.error(request, 'Invalid asset selected.')
            return render(request, "assets/add_maintenance.html", ctx)

        # Lifecycle validation
        if asset.status == 'Retired':
            messages.error(request, f'Asset "{asset.asset_name}" is retired and cannot enter maintenance.')
            return render(request, "assets/add_maintenance.html", ctx)

        # Prevent duplicate active maintenance
        active_maintenance = Maintenance.objects.filter(
            asset=asset, status__in=['Open', 'In Progress']
        ).exists()
        if active_maintenance:
            messages.error(
                request,
                f'Asset "{asset.asset_name}" already has an active maintenance record. '
                f'Please complete the existing maintenance first.'
            )
            return render(request, "assets/add_maintenance.html", ctx)

        Maintenance.objects.create(
            asset=asset,
            issue=issue,
            reported_date=reported_date,
            remarks=remarks
        )

        asset.status = "Maintenance"
        asset.save()

        messages.success(request, f'Maintenance record created for "{asset.asset_name}".')
        return redirect("maintenance_list")

    return render(
        request,
        "assets/add_maintenance.html",
        {"assets": assets}
    )


@login_required(login_url='login')
def edit_maintenance(request, id):

    maintenance = get_object_or_404(Maintenance, id=id)

    if request.method == "POST":

        issue = request.POST.get("issue", "").strip()
        status = request.POST.get("status", "").strip()
        repair_date = request.POST.get("repair_date") or None
        repair_cost_raw = request.POST.get("repair_cost", "0")
        remarks = request.POST.get("remarks", "")

        ctx = {"maintenance": maintenance}

        if not issue or not status:
            messages.error(request, 'Issue and Status are required.')
            return render(request, "assets/edit_maintenance.html", ctx)

        # Validate status choice
        valid_statuses = [s[0] for s in Maintenance.STATUS_CHOICES]
        if status not in valid_statuses:
            messages.error(request, 'Invalid maintenance status selected.')
            return render(request, "assets/edit_maintenance.html", ctx)

        try:
            repair_cost = float(repair_cost_raw) if repair_cost_raw else 0
            if repair_cost < 0:
                raise ValueError()
        except (ValueError, TypeError):
            messages.error(request, 'Repair cost must be a valid non-negative number.')
            return render(request, "assets/edit_maintenance.html", ctx)

        old_status = maintenance.status
        maintenance.issue = issue
        maintenance.status = status
        maintenance.repair_date = repair_date
        maintenance.repair_cost = repair_cost
        maintenance.remarks = remarks
        maintenance.save()

        # Asset lifecycle updates
        asset = maintenance.asset

        if status == "Completed" and old_status != "Completed":
            asset.status = "Available"
            asset.save()
            messages.success(request, f'Maintenance completed. Asset "{asset.asset_name}" is now Available.')
        elif status == "Retired" and old_status != "Retired":
            asset.status = "Retired"
            asset.save()
            messages.success(request, f'Asset "{asset.asset_name}" has been retired.')
        else:
            messages.success(request, 'Maintenance record updated successfully.')

        return redirect("maintenance_list")

    return render(
        request,
        "assets/edit_maintenance.html",
        {"maintenance": maintenance}
    )


# =============================================================
# CATEGORY MANAGEMENT
# =============================================================

@login_required(login_url='login')
def categories_list(request):
    categories = Category.objects.annotate(
        asset_count=Count('asset')
    ).order_by('name')

    search = request.GET.get("search", "").strip()
    if search:
        categories = categories.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )

    return render(request, "assets/categories_list.html", {
        "categories": categories,
        "search": search,
    })


@login_required(login_url='login')
def add_category(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()

        ctx = {"form_data": request.POST}

        if not name:
            messages.error(request, 'Category name is required.')
            return render(request, "assets/add_category.html", ctx)

        if len(name) < 2:
            messages.error(request, 'Category name must be at least 2 characters.')
            return render(request, "assets/add_category.html", ctx)

        if Category.objects.filter(name__iexact=name).exists():
            messages.error(request, f'Category "{name}" already exists. Please use a unique name.')
            return render(request, "assets/add_category.html", ctx)

        Category.objects.create(name=name, description=description)
        messages.success(request, f'Category "{name}" created successfully.')
        return redirect("categories_list")

    return render(request, "assets/add_category.html")


@login_required(login_url='login')
def edit_category(request, id):
    category = get_object_or_404(Category, id=id)

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()

        ctx = {"category": category}

        if not name:
            messages.error(request, 'Category name is required.')
            return render(request, "assets/edit_category.html", ctx)

        if len(name) < 2:
            messages.error(request, 'Category name must be at least 2 characters.')
            return render(request, "assets/edit_category.html", ctx)

        if Category.objects.filter(name__iexact=name).exclude(id=id).exists():
            messages.error(request, f'Category "{name}" already exists. Please use a unique name.')
            return render(request, "assets/edit_category.html", ctx)

        category.name = name
        category.description = description
        category.save()

        messages.success(request, f'Category "{name}" updated successfully.')
        return redirect("categories_list")

    return render(request, "assets/edit_category.html", {"category": category})


@login_required(login_url='login')
def delete_category(request, id):
    category = get_object_or_404(Category, id=id)
    asset_count = Asset.objects.filter(category=category).count()

    if request.method == "POST":
        if asset_count > 0:
            messages.error(
                request,
                f'Cannot delete category "{category.name}" — it is used by {asset_count} asset(s). '
                f'Please reassign those assets to another category first.'
            )
            return redirect("categories_list")
        name = category.name
        try:
            category.delete()
            messages.success(request, f'Category "{name}" deleted successfully.')
        except ProtectedError:
            messages.error(
                request,
                f'Cannot delete category "{name}" — it has associated assets.'
            )
        return redirect("categories_list")

    return render(request, "assets/delete_category.html", {
        "category": category,
        "asset_count": asset_count,
        "has_assets": asset_count > 0,
    })



# =============================================================
# ASSET DETAIL (QR Scan Target - Publicly Viewable)
# =============================================================

def asset_detail(request, id):
    """
    Displays asset details after QR scan.
    Accessible without login so physical QR scans on hardware immediately show asset info.
    Handles numeric ID as well as asset_code lookups.
    Shows friendly 'Asset Not Found' if asset does not exist.
    """
    asset = None
    if str(id).isdigit():
        asset = Asset.objects.filter(id=int(id)).first()
    if not asset:
        asset = Asset.objects.filter(asset_code__iexact=str(id)).first()

    if not asset:
        return render(
            request,
            "assets/asset_detail.html",
            {
                "asset": None,
                "asset_id": id,
                "not_found": True,
            },
            status=404
        )

    assignment = Assignment.objects.filter(
        asset=asset,
        returned_date__isnull=True
    ).select_related('employee').first()

    maintenance_records = Maintenance.objects.filter(
        asset=asset
    ).order_by('-reported_date')

    return render(
        request,
        "assets/asset_detail.html",
        {
            "asset": asset,
            "assignment": assignment,
            "maintenance_records": maintenance_records,
            "not_found": False,
        }
    )


# =============================================================
# REPORTS
# =============================================================

@login_required(login_url='login')
def reports(request):
    # Overall Database Metrics (Real database data)
    total_assets = Asset.objects.count()
    available_assets = Asset.objects.filter(status='Available').count()
    assigned_assets = Asset.objects.filter(status='Assigned').count()
    maintenance_assets = Asset.objects.filter(status='Maintenance').count()
    retired_assets = Asset.objects.filter(status='Retired').count()
    total_asset_value = Asset.objects.aggregate(total=Sum('purchase_price'))['total'] or 0

    categories = Category.objects.all().order_by('name')
    assets_by_category = Category.objects.annotate(
        asset_count=Count('asset')
    ).order_by('-asset_count')

    # Employee Assignment Report
    total_employees = Employee.objects.count()
    total_assignments = Assignment.objects.count()
    active_assignments = Assignment.objects.filter(returned_date__isnull=True).count()
    returned_assignments = Assignment.objects.filter(returned_date__isnull=False).count()

    employees_with_assets = Employee.objects.annotate(
        active_count=Count('assignment', filter=Q(assignment__returned_date__isnull=True))
    ).filter(active_count__gt=0).order_by('-active_count')[:10]

    recent_assignments = Assignment.objects.select_related('asset', 'employee').order_by('-id')[:10]

    # Maintenance Report
    total_maintenance = Maintenance.objects.count()
    open_maintenance = Maintenance.objects.filter(status='Open').count()
    inprogress_maintenance = Maintenance.objects.filter(status='In Progress').count()
    completed_maintenance = Maintenance.objects.filter(status='Completed').count()
    retired_via_maintenance = Maintenance.objects.filter(status='Retired').count()
    total_repair_cost = Maintenance.objects.aggregate(total=Sum('repair_cost'))['total'] or 0

    recent_maintenance = Maintenance.objects.select_related('asset').order_by('-id')[:10]

    # Filtering for Asset Detailed Report
    status_filter = request.GET.get('status', '').strip()
    category_filter = request.GET.get('category', '').strip()
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()

    filtered_assets = Asset.objects.select_related('category').all().order_by('-id')

    if status_filter:
        filtered_assets = filtered_assets.filter(status=status_filter)
    if category_filter:
        filtered_assets = filtered_assets.filter(category_id=category_filter)
    if start_date:
        filtered_assets = filtered_assets.filter(purchase_date__gte=start_date)
    if end_date:
        filtered_assets = filtered_assets.filter(purchase_date__lte=end_date)

    filtered_count = filtered_assets.count()
    filtered_value = filtered_assets.aggregate(total=Sum('purchase_price'))['total'] or 0

    return render(
        request,
        "assets/reports.html",
        {
            # Asset Metrics
            'total_assets': total_assets,
            'available_assets': available_assets,
            'assigned_assets': assigned_assets,
            'maintenance_assets': maintenance_assets,
            'retired_assets': retired_assets,
            'total_asset_value': total_asset_value,
            'categories': categories,
            'assets_by_category': assets_by_category,

            # Filtered Asset Data & Filters
            'filtered_assets': filtered_assets,
            'filtered_count': filtered_count,
            'filtered_value': filtered_value,
            'selected_status': status_filter,
            'selected_category': category_filter,
            'start_date': start_date,
            'end_date': end_date,
            'has_filters': bool(status_filter or category_filter or start_date or end_date),

            # Employee & Assignment Metrics
            'total_employees': total_employees,
            'total_assignments': total_assignments,
            'active_assignments': active_assignments,
            'returned_assignments': returned_assignments,
            'employees_with_assets': employees_with_assets,
            'recent_assignments': recent_assignments,

            # Maintenance Metrics
            'total_maintenance': total_maintenance,
            'open_maintenance': open_maintenance,
            'inprogress_maintenance': inprogress_maintenance,
            'completed_maintenance': completed_maintenance,
            'retired_via_maintenance': retired_via_maintenance,
            'total_repair_cost': total_repair_cost,
            'recent_maintenance': recent_maintenance,
        }
    )


# =============================================================
# CSV EXPORT
# =============================================================

@login_required(login_url='login')
def export_assets_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="assets_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Asset Name', 'Asset Code', 'Category', 'Brand',
                     'Purchase Date', 'Purchase Price', 'Status'])

    assets = Asset.objects.all().select_related('category').order_by('id')

    # Apply filters if provided from Reports page
    status = request.GET.get('status', '').strip()
    category_id = request.GET.get('category', '').strip()
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()

    if status:
        assets = assets.filter(status=status)
    if category_id:
        assets = assets.filter(category_id=category_id)
    if start_date:
        assets = assets.filter(purchase_date__gte=start_date)
    if end_date:
        assets = assets.filter(purchase_date__lte=end_date)

    for asset in assets:
        writer.writerow([
            asset.id,
            asset.asset_name,
            asset.asset_code,
            asset.category.name if asset.category else 'N/A',
            asset.brand,
            asset.purchase_date,
            asset.purchase_price,
            asset.status,
        ])

    return response


@login_required(login_url='login')
def export_assignments_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="assignments_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Asset Name', 'Asset Code', 'Employee Name',
                     'Department', 'Assigned Date', 'Return Date', 'Status', 'Remarks'])

    assignments = Assignment.objects.all().select_related('asset', 'employee').order_by('id')
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()
    status_filter = request.GET.get('status', '').strip()

    if start_date:
        assignments = assignments.filter(assigned_date__gte=start_date)
    if end_date:
        assignments = assignments.filter(assigned_date__lte=end_date)
    if status_filter == 'active':
        assignments = assignments.filter(returned_date__isnull=True)
    elif status_filter == 'returned':
        assignments = assignments.filter(returned_date__isnull=False)

    for a in assignments:
        status = 'Returned' if a.returned_date else 'Active'
        writer.writerow([
            a.id,
            a.asset.asset_name if a.asset else 'N/A',
            a.asset.asset_code if a.asset else 'N/A',
            a.employee.name if a.employee else 'N/A',
            a.employee.department if a.employee else 'N/A',
            a.assigned_date,
            a.returned_date if a.returned_date else 'Not Returned',
            status,
            a.remarks,
        ])

    return response


@login_required(login_url='login')
def export_maintenance_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="maintenance_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Asset Name', 'Asset Code', 'Issue',
                     'Reported Date', 'Repair Date', 'Repair Cost', 'Status', 'Remarks'])

    maintenance = Maintenance.objects.all().select_related('asset').order_by('id')
    status = request.GET.get('status', '').strip()
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()

    if status:
        maintenance = maintenance.filter(status=status)
    if start_date:
        maintenance = maintenance.filter(reported_date__gte=start_date)
    if end_date:
        maintenance = maintenance.filter(reported_date__lte=end_date)

    for m in maintenance:
        writer.writerow([
            m.id,
            m.asset.asset_name if m.asset else 'N/A',
            m.asset.asset_code if m.asset else 'N/A',
            m.issue,
            m.reported_date,
            m.repair_date if m.repair_date else 'N/A',
            m.repair_cost,
            m.status,
            m.remarks,
        ])

    return response