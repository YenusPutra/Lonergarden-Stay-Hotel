from django import forms


from .models import ContactMessage
class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage  # Replace ContactMessage with your model name
        fields = ['name', 'email', 'subject', 'message']  # Replace with your form fields

from .models import Room
class RoomForm(forms.ModelForm):
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('id', 'Indonesian'), 
        ('ja', 'Japanese'),
        ('fr', 'French'),
        ('de', 'German'),
        ('es', 'Spanish'),
    ]
    edit_language = forms.ChoiceField(
        choices=LANGUAGE_CHOICES,
        initial='en',
        label='Edit Description in'
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        label="Description",
        required=False
    )

    class Meta:
        model = Room
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Initialize with the current language's description
            # This ensures the form starts with the right language data
            current_lang = self.initial.get('edit_language', 'en')
            lang_field = f'description_{current_lang}'
            if hasattr(self.instance, lang_field):
                self.fields['description'].initial = getattr(self.instance, lang_field)
        else:
            # For new rooms, set initial language to English
            self.fields['edit_language'].initial = 'en'

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.description = instance.description_en  # The room_language_switcher.js already updated all the language fields # We just need to ensure the main description is set to English

        if commit:
            instance.save()
        return instance

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

from django.contrib.auth.forms import AuthenticationForm
class CustomAuthenticationForm(AuthenticationForm):
    error_messages = {
        'invalid_login': "❌ Wrong account, you sure you're staff :/",
        'inactive': "This account is inactive.",
    }