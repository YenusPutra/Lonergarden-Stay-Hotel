from django.http import Http404
from django.shortcuts import redirect, render, get_object_or_404
from .forms import ContactForm
from django.contrib import messages
from django.core.mail import send_mail
from django.db.models import Q
from django.conf import settings
from django.urls import reverse
from .models import Room, BookingSystem
from midtransclient import Snap
import uuid
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# Create your views here.

ALLOWED_TEMPLATES = [
    'about', 'amenities', 'booking', '404', 'contact', 'events', 'gallery',
    'index', 'location', 'offers', 'privacy', 'restaurant', 'room-details',
    'rooms', 'starter-page', 'terms', 'login',
]

def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        contact_instance = form.save()
        
        subject = f"LonergardenHotel Contact: {contact_instance.name}"
        message = f"Name: {contact_instance.name}\nEmail: {contact_instance.email}\n\nMessage:\n{contact_instance.message}" #Plaintext fallback !don't delet!
        
        # HTML version with bold labels
        linebreaksconverter = contact_instance.message.replace('\n', '<br>')
        html_message = f"""
        <p><strong>Name:</strong> {contact_instance.name} / {contact_instance.email} </p>
        <p><strong>Subject:</strong> {contact_instance.subject}</p>
        <p><strong>Message:</strong><br>{linebreaksconverter}</p>
        """
        
        recipient_list = ['ypialoid@gmail.com']  # Change to your target email
        send_mail(
            subject,
            message,
            None,  # Use DEFAULT_FROM_EMAIL from settings
            recipient_list,
            fail_silently=False,
            html_message=html_message  # HTML content
        )

        messages.success(request, "Your message has been sent. Thank you!")
        return redirect('/contact/#contact-form-wrapper')  # ✅ redirect after POST
    return render(request, 'mYinterface/contact.html', {'form': form})

def room_list(request):
    # Start with all rooms
    rooms = Room.objects.all()

    price_range = request.GET.get('price_range', '').lower()
    guest_capacity = request.GET.get('guest_capacity')
    view_type = request.GET.get('view_type', '')
    sort_by = request.GET.get('sort_by')
    guest_capacity_str = request.GET.get('guest_capacity') # Store the string value

    # --- Filtering ---

    # 1. Filter by price range
    if price_range == 'low':
        # $100 - $200
        rooms = rooms.filter(price__gte=100, price__lte=200)
    elif price_range == 'medium':
        # $200 - $350
        rooms = rooms.filter(price__gt=200, price__lte=350)
    elif price_range == 'high':
        # $350+
        rooms = rooms.filter(price__gt=350)    

    # 2. Filter by guest capacity
    if guest_capacity:
        try:
          guest_capacity = int(guest_capacity_str)
          if guest_capacity == 2: # Filters for rooms with capacity >= requested capacity
            rooms = rooms.filter(capacity__lte=2) # If 1-2 Guests is selected (value='2'), filter for capacity up to 2
          elif guest_capacity == 4:            
            rooms = rooms.filter(capacity__gte=3, capacity__lte=4) # If 3-4 Guests is selected (value='4'), filter for capacity between 3 and 4
          elif guest_capacity == 5:            
            rooms = rooms.filter(capacity__gte=5) # If 5+ Guests is selected (value='5'), filter for capacity >= 5
        except ValueError:
            pass  # ignore if not a number

    # 3. Filter by view type
    if view_type == 'Ocean_View':
        rooms = rooms.filter(tag_ocean_view=True)
    elif view_type == 'City_View':
        rooms = rooms.filter(tag_city_view=True)
    elif view_type == 'Garden_View':
        rooms = rooms.filter(tag_garden_view=True)

    # --- Sorting (applied to the filtered QuerySet) ---
    if sort_by == 'price_low':
        rooms = rooms.order_by('price')
    elif sort_by == 'price_high':
        rooms = rooms.order_by('-price')
    elif sort_by == 'room_size':
        rooms = rooms.order_by('-capacity')

    return render(request, 'mYinterface/rooms.html', {'rooms': rooms})

def booking(request):
    if request.method == "POST":
        # ✅ Collect form data
        arrival = request.POST.get("arrival_date")
        departure = request.POST.get("departure_date")
        guest = int(request.POST.get("guest_count"))
        room = int(request.POST.get("room_count"))
        accommodation_type = request.POST.get("accommodation_type")
        additional_notes = request.POST.get("additional_notes")
        name = request.POST.get("primary_guest")
        email = request.POST.get("contact_email")
        phone = request.POST.get("contact_phone")


        # ✅ Example price calculation (adjust as needed)
        total_price = int(room) * 500000  # e.g., 500k per room

        # Generate unique order_id
        order_id = f"BOOK-{uuid.uuid4().hex[:10]}"

        # Save booking to DB
        booking_obj = BookingSystem.objects.create(
            arrival_date=arrival,
            departure_date=departure,
            guest_count=guest,
            room_count=room,
            accommodation_type=accommodation_type,
            additional_notes=additional_notes,
            primary_guest=name,
            contact_email=email,
            contact_phone=phone,
            order_id=order_id,
            amount=total_price
        )

        # ✅ Midtrans Snap
        snap = Snap(
            is_production=settings.MIDTRANS_IS_PRODUCTION,
            server_key=settings.MIDTRANS_SERVER_KEY
        )

        transaction = snap.create_transaction({
            "transaction_details": {
                "order_id": f"ORDER-{name}-{guest}",
                "gross_amount": total_price,
            },
            "customer_details": {
                "first_name": name,
                "email": email,
                "phone": phone,
            },
            "item_details": [{
            "id": "room-booking",
            "price": total_price,
            "quantity": 1,
            "name": f"{accommodation_type or 'Standard'} Room"
            }],
            "arrivals": f"Arrival: {arrival}",
            "departures": f"Departure: {departure}",
            "custom_field3": f"Notes: {additional_notes or '-'}",
        })
        

        # Save snap token
        snap_token = transaction['token']
        booking_obj.snap_token = snap_token
        booking_obj.save()

        return render(request, "mYinterface/payment.html", {
            "snap_token": snap_token,
            "client_key": settings.MIDTRANS_CLIENT_KEY,
            "total_price": total_price
        })

    return render(request, "mYinterface/booking.html")

@csrf_exempt  # Midtrans can't send CSRF token, so we disable it for this endpoint
def midtrans_notification(request):
    if request.method == "POST":
        try:
            notif_data = json.loads(request.body)

            order_id = notif_data.get("order_id")
            transaction_status = notif_data.get("transaction_status")
            fraud_status = notif_data.get("fraud_status")
            # Map Midtrans status to our Booking model
            status_map = {
                "capture": "success" if fraud_status == "accept" else "pending",
                "settlement": "success",
                "pending": "pending",
                "deny": "failed",
                "cancel": "cancelled",
                "expire": "failed",
                "failure": "failed",
            }
            new_status = status_map.get(transaction_status, "pending")
            try:
                booking = BookingSystem.objects.get(order_id=order_id)
                booking.payment_status = new_status
                booking.save()
                return JsonResponse({"status": "ok", "order_id": order_id, "payment_status": new_status})
            except BookingSystem.DoesNotExist:
                return JsonResponse({"status": "error", "message": "Booking not found"}, status=404)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "invalid method"}, status=405)



# Custom 404 view for catch-all pattern !!Must be put at the very last line!!
def render_page(request, page):
    if page not in ALLOWED_TEMPLATES:
        raise Http404("Page not found")
    return render(request, f'mYinterface/{page}.html')


def custom_404_view(request, exception=None):
    return render(request, 'mYinterface/404.html', status=404)


        
    
    

