from django.urls import path, re_path
from . import views

urlpatterns = [
    path("booking/", views.booking, name="booking"),
    path("payment/", views.midtrans_notification, name="midtrans_notification"),
    path("payment/finish/", views.payment_finish, name="payment_finish"),
    path('', views.render_page, {'page': 'index'}, name='index'),
    path('rooms/', views.room_list, name='room_list'),
    path('contact/', views.contact, name='contact'),
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




