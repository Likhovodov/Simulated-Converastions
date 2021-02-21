from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser
from django.apps import apps


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ('email', 'is_active', 'is_researcher', 'is_staff')
    list_filter = ('email', 'is_active', 'is_researcher', 'is_staff')
    fieldsets = (
        (None, {
            'fields': ('first_name', 'last_name', 'email', 'password')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_researcher', 'is_staff')
        }),
    )
    add_fieldsets = ((None, {
        'classes': ('wide', ),
        'fields': ('first_name', 'last_name', 'email', 'password1', 'password2', 'is_active',
                   'is_researcher', 'is_staff')
    }), )
    search_fields = ('email', )
    ordering = ('email', )


admin.site.register(CustomUser, CustomUserAdmin)

models = apps.get_models()
for model in models:
    try:
        if str(model).find('django_apscheduler') == -1:
            admin.site.register(model)
    except admin.sites.AlreadyRegistered:
        pass
