from django.contrib import admin
from .models import Room, ContactMessage

# Register your models here.

from .forms import RoomForm
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

admin.site.register(Room, RoomAdmin) # Use the custom RoomAdmin here
admin.site.register(ContactMessage)