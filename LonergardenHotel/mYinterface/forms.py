from django import forms


from .models import ContactMessage
class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage  # Replace ContactMessage with your model name
        fields = ['name', 'email', 'subject', 'message']  # Replace with your form fields

from .models import Room
class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()

        # Validate Tags
        tag_fields = [
            'tag_ocean_view', 'tag_garden_view', 'tag_city_view', 
            'tag_mountain_view', 'tag_pool_view', 'tag_popular', 
            'tag_business', 'tag_family_friendly', 'tag_romantic', 
            'tag_premium', 'tag_luxury'
        ]
        checked_tags = sum(cleaned_data.get(f) for f in tag_fields)
        if checked_tags > 2:
            self.add_error(None, "❌ Tags: You can select a maximum of 2 tags.")

        # Validate Amenities
        amenity_fields = [
            'has_wifi', 'has_tv', 'has_workspace', 'has_kitchen', 
            'has_game_console', 'has_parking', 'has_jacuzzi', 
            'has_coffeemachine', 'has_kingsize_bed', 'has_secure', 
            'has_bussinessphone'
        ]
        checked_amenities = sum(cleaned_data.get(f) for f in amenity_fields)
        if checked_amenities > 2:
            self.add_error(None, "❌ Amenities: You can select a maximum of 2 amenities.")

        return cleaned_data
