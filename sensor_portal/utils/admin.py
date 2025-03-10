from django.contrib import admin


class GenericAdmin(admin.ModelAdmin):
    readonly_fields = ['created_on', 'modified_on']


class AddOwnerAdmin(GenericAdmin):
    readonly_fields = ['owner']

    def save_model(self, request, obj, form, change):
        if obj.owner is None:
            obj.owner = request.user
        super().save_model(request, obj, form, change)
