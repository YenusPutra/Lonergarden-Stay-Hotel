from django.http import Http404
from django.shortcuts import redirect, render, get_object_or_404
from .forms import ContactForm
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from .models import Room, BookingSystem
from midtransclient import Snap
import uuid
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string


# Create your views here.

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
    return render(request, 'userinterface/contact.html', {'form': form})


def room_list(request):
    # Start with all rooms
    rooms = Room.objects.all()
    search_query = request.GET.get('search', '')
    price_range = request.GET.get('price_range', '').lower()
    guest_capacity = request.GET.get('guest_capacity')
    view_type = request.GET.get('view_type', '')
    sort_by = request.GET.get('sort_by')
    guest_capacity_str = request.GET.get('guest_capacity') # Store the string value
    offset = int(request.GET.get('offset', 0))      # Get the offset (which set of rooms to show, e.g., 0 for first 6, 6 for next 6)


    # --- Filtering ---

    #live-search filtering
    from django.db.models import Q #import OR filtering
    if search_query:
        search_terms = search_query.split()
        query = Q()
        for term in search_terms:
            term_query = Q()
            term_query |= Q(name__icontains=term)             # Basic text search
            term_query |= Q(description__icontains=term)
            feature_mapping = {             # Feature tags search
                'ocean': 'tag_ocean_view', 'garden': 'tag_garden_view', 
                'city': 'tag_city_view', 'mountain': 'tag_mountain_view',
                'pool': 'tag_pool_view', 'popular': 'tag_popular',
                'business': 'tag_business', 'family': 'tag_family_friendly',
                'friendly': 'tag_family_friendly', 'romantic': 'tag_romantic',
                'premium': 'tag_premium', 'luxury': 'tag_luxury',
            }
            for keyword, field in feature_mapping.items():            # Check feature mapping
                if keyword in term.lower():
                    term_query |= Q(**{f'{field}': True})

            amenity_mapping = {             # Amenities search
                'wifi': 'has_wifi', 'tv': 'has_tv',
                'television': 'has_tv', 'workspace': 'has_workspace',
                'work': 'has_workspace', 'desk': 'has_workspace',
                'kitchen': 'has_kitchen', 'mini': 'has_kitchen',
                'game': 'has_game_console', 'console': 'has_game_console',
                'parking': 'has_parking', 'jacuzzi': 'has_jacuzzi',
                'coffee': 'has_coffeemachine', 'machine': 'has_coffeemachine',
                'king': 'has_kingsize_bed', 'bed': 'has_kingsize_bed',
                'safe': 'has_secure', 'secure': 'has_secure', 'phone': 'has_bussinessphone',
            }
            for keyword, field in amenity_mapping.items():            # Check amenity mapping  
                if keyword in term.lower():
                    term_query |= Q(**{f'{field}': True})

            # Add view keyword search, This would catch "oceanview" but not just "view"
            if 'view' in term.lower() and len(term) > 3: 
                pass

            query |= term_query         # Combine with OR logic for each term
        
        rooms = rooms.filter(query).distinct()

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

    #room load per 6 cards
    rooms_per_page = 6
    rooms_to_display = rooms[offset:offset + rooms_per_page]    # Get only the 6 rooms we want to show
    has_more = len(rooms) > offset + rooms_per_page    # Check if there are more rooms to load

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':     # Check if this is an AJAX request (live search)
        html = render_to_string('userinterface/rooms-grid.html', {'rooms': rooms_to_display})         # Render only the rooms grid HTML with only 6 rooms
        return JsonResponse({
            'html': html,
            'has_more': has_more,
            'next_offset': offset + rooms_per_page,
            })   
     
    context = {
            'rooms': rooms_to_display,
            'has_more': has_more,
            'next_offset': offset + rooms_per_page,
            'search_query': search_query,   # Pass search query for the template
            'price_range': price_range,          # Add these
            'guest_capacity': guest_capacity_str, # Add these
            'view_type': view_type,              # Add these
            'sort_by': sort_by,
            }
    
    return render(request, 'userinterface/rooms.html', context)

    

def booking(request):
    if request.method == "POST":
        # Check if this is an AJAX request (from your JavaScript fetch)
        
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
        roomtype_price = {
            "Deluxe" : 289.00,
            "Standard" : 129.00,
            "Romantic" : 349.00,
            "Family" : 159.00,
            "Executive" : 199.00,
            "Premium" : 259.00,
            }
        from datetime import datetime
        try:
            arrival_date = datetime.strptime(arrival, "%Y-%m-%d")
            departure_date = datetime.strptime(departure, "%Y-%m-%d")
        except ValueError:
            # If dates are invalid, return error instead of crashing
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Invalid date format'}, status=400)
            else:
                messages.error(request, 'Invalid date format')
                return redirect('/booking/')  # Or wherever
        nights = (departure_date - arrival_date).days
        if nights <= 0:
            # Departure before arrival? Error!
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Departure must be after arrival'}, status=400)
            else:
                messages.error(request, 'Departure must be after arrival')
                return redirect('/booking/')
        RoomType = roomtype_price.get(accommodation_type)
        if not accommodation_type:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Please select an accommodation type'}, status=400)
            else:
                messages.error(request, 'Please select an accommodation type')
                return redirect('/booking/')
            
        total_price = int(room) * RoomType * nights

        # Generate unique order_id
        unique_order_id = f"BOOK-{uuid.uuid4().hex[:10]}"

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
            order_id=unique_order_id,
            amount=total_price
        )

        # ✅ Midtrans Snap
        snap = Snap(
            is_production=settings.MIDTRANS_IS_PRODUCTION,
            server_key=settings.MIDTRANS_SERVER_KEY
        )

        from midtransclient.error_midtrans import MidtransAPIError
        try:
            transaction = snap.create_transaction({
            "transaction_details": {
                "order_id": f"ORDER-{name}-{guest}-{unique_order_id}",
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
            "quantity": room,
            "name": f"{accommodation_type} Room"
            }],
            "arrivals": f"Arrival: {arrival}",
            "departures": f"Departure: {departure}",
            "custom_field3": f"Notes: {additional_notes or '-'}",
            "callbacks": {
            "finish": request.build_absolute_uri("/payment/finish/")
            }
            })
        except MidtransAPIError as e:
            # Handle the error nicely
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Payment setup failed, try again'}, status=500)
            else:
                messages.error(request, 'Payment setup failed, try again')
                return redirect('/booking/')

        # Save snap token
        snap_token = transaction['token']
        booking_obj.snap_token = snap_token
        booking_obj.save()

        # Check if this is an AJAX request (from JavaScript)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Return JSON for JavaScript to call snap.pay()
            return JsonResponse({'snap_token': snap_token})
        else:
            # Normal form submit: show the payment page
            return render(request, "userinterface/payment.html", {
                "snap_token": snap_token,
                "client_key": settings.MIDTRANS_CLIENT_KEY,
                "total_price": total_price
            })
    else: 
        return render(request, "userinterface/booking.html")
    
    
def payment_finish(request):
    return render(request, "userinterface/payment_success.html")


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
ALLOWED_TEMPLATES = [
    'about', 'amenities', 'booking', '404', 'contact', 'events', 'gallery',
    'index', 'location', 'offers', 'privacy', 'restaurant', 'room-details',
    'rooms', 'starter-page', 'terms',
]
def render_page_admin(request):
    return render(request, 'userinterface/admin/login.html')

def render_page(request, page):
    if page not in ALLOWED_TEMPLATES:
        raise Http404("Page not found")
    return render(request, f'userinterface/{page}.html')

def custom_404_view(request, exception=None):
    return render(request, 'userinterface/404.html', status=404)


        
    
    

