from django.contrib import admin
from .models import User, DeviceUser
from django.contrib.auth.admin import UserAdmin
from rest_framework.authtoken.models import Token, TokenProxy
from rest_framework.authtoken.admin import TokenAdmin

TokenAdmin.raw_id_fields = ['user']


class TokenInline(admin.StackedInline):
    model = Token


admin.site.unregister(TokenProxy)


class InlineUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'first_name',
                    'last_name', 'is_active', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'groups')
    search_fields = ('username', 'first_name', 'last_name')

    inlines = [
        TokenInline,
    ]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(deviceuser__isnull=True)

    def get_formsets_with_inlines(self, request, obj=None):
        for inline in self.get_inline_instances(request, obj):
            # hide Token in the add view
            if not isinstance(inline, TokenInline) or obj is not None:
                yield inline.get_formset(request, obj), inline

    def save_model(self, request, obj, form, change):
        obj.from_admin_site = True
        super().save_model(request, obj, form, change)


admin.site.register(User, InlineUserAdmin)


class DeviceUserAdmin(UserAdmin):
    list_display = ('username',)
    list_filter = ()
    search_fields = ('username',)

    inlines = [
        TokenInline,
    ]

    def get_formsets_with_inlines(self, request, obj=None):
        for inline in self.get_inline_instances(request, obj):
            # hide Token in the add view
            if not isinstance(inline, TokenInline) or obj is not None:
                yield inline.get_formset(request, obj), inline

    def save_model(self, request, obj, form, change):
        obj.from_admin_site = True
        super().save_model(request, obj, form, change)


admin.site.register(DeviceUser, DeviceUserAdmin)


# class GroupProfileInline(admin.StackedInline):
#     model = GroupProfile


# class GroupAdmin(GroupAdmin):
#     inlines = [
#         GroupProfileInline,
#     ]

#     def save_model(self, request, obj, form, change):
#         obj.from_admin_site = True
#         super().save_model(request, obj, form, change)


# admin.site.unregister(Group)
# admin.site.register(Group, GroupAdmin)
