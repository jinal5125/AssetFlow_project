from django.urls import path
from . import views

urlpatterns = [

    # Auth & Root
    path('', views.login_view, name='login_root'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Assets
    path('assets/', views.assets_list, name='assets_list'),
    path('assets/add/', views.add_asset, name='add_asset'),
    path('assets/edit/<int:id>/', views.edit_asset, name='edit_asset'),
    path('assets/delete/<int:id>/', views.delete_asset, name='delete_asset'),
    path('assets/detail/<str:id>/', views.asset_detail, name='asset_detail'),

    # Employees
    path('employees/', views.employees_list, name='employees_list'),
    path('employees/add/', views.add_employee, name='add_employee'),
    path('employees/edit/<int:id>/', views.edit_employee, name='edit_employee'),
    path('employees/delete/<int:id>/', views.delete_employee, name='delete_employee'),

    # Assignments
    path('assignments/', views.assignments_list, name='assignments_list'),
    path('assignments/add/', views.add_assignment, name='add_assignment'),
    path('assignments/return/<int:id>/', views.return_asset, name='return_asset'),

    # Maintenance
    path('maintenance/', views.maintenance_list, name='maintenance_list'),
    path('maintenance/add/', views.add_maintenance, name='add_maintenance'),
    path('maintenance/edit/<int:id>/', views.edit_maintenance, name='edit_maintenance'),

    # Categories
    path('categories/', views.categories_list, name='categories_list'),
    path('categories/add/', views.add_category, name='add_category'),
    path('categories/edit/<int:id>/', views.edit_category, name='edit_category'),
    path('categories/delete/<int:id>/', views.delete_category, name='delete_category'),

    # Reports
    path('reports/', views.reports, name='reports'),

    # CSV Export
    path('export/assets/', views.export_assets_csv, name='export_assets_csv'),
    path('export/assignments/', views.export_assignments_csv, name='export_assignments_csv'),
    path('export/maintenance/', views.export_maintenance_csv, name='export_maintenance_csv'),

]