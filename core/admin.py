from django.contrib import admin
from .models import *

admin.site.register(Product)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'is_verified')

    def save_model(self, request, obj, form, change):
        # Only allow superadmin to create or modify Managers or Operators
        if request.user.is_superuser:
            super().save_model(request, obj, form, change)
        else:
            if obj.role not in ['manager', 'operator']:  # Non-superusers can only modify vendors
                super().save_model(request, obj, form, change)
            else:
                raise PermissionError("You do not have permission to assign this role.")

admin.site.register(Profile, ProfileAdmin)
admin.site.register(Order)
admin.site.register(Company)
admin.site.register(Other_cost)