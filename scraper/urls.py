from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.productos_view, name='home'),  # Nueva vista para la raíz
    path('productos/', views.productos_view, name='productos'),
    path('salcobrand/', views.salcobrand_view, name='salcobrand'),
    path('cofar/', views.cofar_view, name='cofar'),
    path('profar/', views.profar_view, name='profar'),
    path('iniciar_extraccion/', views.iniciar_extraccion, name='iniciar_extraccion'),
    path('get_scraping_data/', views.get_scraping_data, name='get_scraping_data'),
    path('cancel_extraction/', views.cancel_extraction, name='cancel_extraction'),  # Agregar esta línea
    path('get_temporary_file/', views.get_temporary_file, name='get_temporary_file'),  # Agregar esta línea
]
