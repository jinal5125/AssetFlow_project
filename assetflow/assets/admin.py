from django.contrib import admin
from .models import Employee, Category, Asset, Assignment, Maintenance


admin.site.register(Employee)
admin.site.register(Category)
admin.site.register(Asset)
admin.site.register(Assignment)
admin.site.register(Maintenance)