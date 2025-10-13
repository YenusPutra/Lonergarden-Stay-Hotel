from django.db import models
from django.core.exceptions import ValidationError # Import this!
from django.utils.translation import get_language

# Create your models here.

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=100)
    message = models.TextField()

class Room(models.Model):
    #roomdetails
    image = models.ImageField(upload_to='room_images/', null=True)  # Room photo
    name = models.CharField(max_length=100)  # e.g. "Deluxe Ocean Suite"
    description = models.TextField()  # Full paragraph about the room     # Will store current language's description    # Keep the original description as main field for backward compatibility
    
    # model description languages
    description_en = models.TextField("English Description")
    description_id = models.TextField("Indonesian Description", blank=True)
    description_ja = models.TextField("Japanese Description", blank=True)
    description_fr = models.TextField("French Description", blank=True)
    description_de = models.TextField("German Description", blank=True)
    description_es = models.TextField("Spanish Description", blank=True)

    # def save(self, *args, **kwargs):
    #     # Set the main description to English by default (or current language)
    #     self.description = self.description_en
    #     super().save(*args, **kwargs)

    # Tags
    tag_ocean_view = models.BooleanField(default=False)
    tag_garden_view = models.BooleanField(default=False)
    tag_city_view = models.BooleanField(default=False)
    tag_mountain_view = models.BooleanField(default=False)
    tag_pool_view = models.BooleanField(default=False)
    tag_popular = models.BooleanField(default=True)  # For "Popular" badge
    tag_business = models.BooleanField(default=False)  # For "Business" tag
    tag_family_friendly = models.BooleanField(default=False)  # For "Family Friendly" tag
    tag_romantic = models.BooleanField(default=False)
    tag_premium = models.BooleanField(default=False)
    tag_luxury = models.BooleanField(default=False)

    # Amenities
    capacity = models.IntegerField()  # e.g. 4 guests
    has_wifi = models.BooleanField(default=True)
    has_tv = models.BooleanField(default=False)
    has_workspace = models.BooleanField(default=False)
    has_kitchen = models.BooleanField(default=False)
    has_game_console = models.BooleanField(default=False)
    has_parking = models.BooleanField(default=False)
    has_jacuzzi = models.BooleanField(default=False)
    has_coffeemachine = models.BooleanField(default=False)
    has_kingsize_bed = models.BooleanField(default=False)
    has_secure = models.BooleanField(default=False)
    has_bussinessphone = models.BooleanField(default=False)

    #price
    price = models.DecimalField(max_digits=8, decimal_places=2) # e.g. 289.00  

    # Localization helpers
    def get_localized_field(self, base_name, default=''):
        lang = (get_language() or 'en').split('-')[0]
        field_name = f'{base_name}_{lang}'
        value = getattr(self, field_name, None)
        if value:
            return value
        # fallback to English then base field
        en_value = getattr(self, f'{base_name}_en', None)
        if en_value:
            return en_value
        base_value = getattr(self, base_name, None)
        return base_value or default

    @property
    def localized_description(self):
        return self.get_localized_field('description', default='')

    def __str__(self):
        return self.name
    
# mYinterface/models.py
from django.db import models

class BookingSystem(models.Model):
    # Booking details
    arrival_date = models.DateField()
    departure_date = models.DateField()
    guest_count = models.PositiveIntegerField()
    room_count = models.PositiveIntegerField()
    # Room preferences
    accommodation_type = models.CharField(
        max_length=50,
        choices=[
            ("Deluxe", "Deluxe Ocean Suite"),
            ("Standard", "Standard City Room"),
            ("Romantic", "Romantic Honeymoon Suite"),
            ("Family", "Family Garden Room"),
            ("Executive", "Executive Business Suite"),
            ("Premium", "Premium Ocean View"),
        ],
    )
    additional_notes = models.TextField(blank=True, null=True)
    # Guest info
    primary_guest = models.CharField(max_length=100)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20)
    # Payment info (from Midtrans)
    order_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("success", "Success"),
            ("failed", "Failed"),
            ("cancelled", "Cancelled"),
        ],
        default="pending"
    )
    snap_token = models.CharField(max_length=200, blank=True, null=True)
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Booking {self.order_id} - {self.primary_guest}"

