from django.urls import path, re_path
from . import views
from django.contrib.auth import views as auth_views
from .forms import CustomAuthenticationForm

urlpatterns = [
    path("booking/", views.booking, name="booking"),
    # path('set-language/', views.set_language, name='set_language'),
    path("payment/", views.midtrans_notification, name="midtrans_notification"),
    path("payment/finish/", views.payment_finish, name="payment_finish"),
    path('', views.render_page, {'page': 'index'}, name='index'),
    path('rooms/', views.room_list, name='room_list'),
    path('contact/', views.contact, name='contact'),
    path('login/', auth_views.LoginView.as_view(
        template_name='userinterface/admin/login.html',
        redirect_authenticated_user=True,
        form_class=CustomAuthenticationForm,
        next_page='/admin/'
    ), name='login'),
    # All allowed template paths [refer to views.py]
    path('about/', views.render_page, {'page': 'about'}, name='about'),
    path('amenities/', views.render_page, {'page': 'amenities'}, name='amenities'),
    path('events/', views.render_page, {'page': 'events'}, name='events'),
    path('gallery/', views.render_page, {'page': 'gallery'}, name='gallery'),
    path('location/', views.render_page, {'page': 'location'}, name='location'),
    path('offers/', views.render_page, {'page': 'offers'}, name='offers'),
    path('privacy/', views.render_page, {'page': 'privacy'}, name='privacy'),
    path('restaurant/', views.render_page, {'page': 'restaurant'}, name='restaurant'),
    path('room-details/', views.render_page, {'page': 'room-details'}, name='room-details'),
    path('starter-page/', views.render_page, {'page': 'starter-page'}, name='starter-page'),
    path('terms/', views.render_page, {'page': 'terms'}, name='terms'),
]

from django.conf import settings
from django.conf.urls.static import static
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [
    path('<page>/', views.render_page, name='render-page'),
    # path('login', views.render_page, {'page': 'login'}, name='login'),

    # Catch-all pattern for unknown URLs (shows custom 404) !!Must at the bottom of the code!!
    # re_path(r'^.*$', views.custom_404_view),
]




