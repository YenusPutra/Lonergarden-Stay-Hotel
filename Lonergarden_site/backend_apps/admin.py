from django.contrib import admin
from Lonergarden_site.backend_apps.models import Room, ContactMessage

# Register your models here.

# Create our custom admin site
class CustomAdminSite(admin.AdminSite):
    login_template = 'admin/login.html'     # Tell Django to use your custom login template

custom_admin_site = CustomAdminSite(name='custom_login')     # Create an instance of our custom admin

from django.contrib.auth.models import User, Group
custom_admin_site.register(User)
custom_admin_site.register(Group)


from Lonergarden_site.backend_apps.forms import RoomForm
class RoomAdmin(admin.ModelAdmin):
    form = RoomForm  # ✅ use the custom form

    fieldsets = (
        ('Room Details', {
            'fields': ('name', 'price', 'capacity', 'image', 'description')
        }),
        ('Tags (Max 2 Recommended)', {
            'fields': (
                ('tag_ocean_view', 'tag_garden_view'),
                ('tag_city_view', 'tag_mountain_view', 'tag_pool_view'),
                ('tag_popular', 'tag_business', 'tag_family_friendly'),
                ('tag_romantic', 'tag_premium', 'tag_luxury'),
            ),
        }),
        ('Amenities (Max 2 Recommended)', {
            'fields': (
                ('has_wifi', 'has_tv', 'has_workspace'),
                ('has_kitchen', 'has_game_console', 'has_parking'),
                ('has_jacuzzi', 'has_coffeemachine', 'has_kingsize_bed'),
                ('has_secure', 'has_bussinessphone'),
            ),
        }),
    )

custom_admin_site.register(Room, RoomAdmin) # Use the custom RoomAdmin here
custom_admin_site.register(ContactMessage)
admin.site.register(Room, RoomAdmin) # Use the custom RoomAdmin here
admin.site.register(ContactMessage)