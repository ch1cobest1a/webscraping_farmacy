from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login_view, name='login'),  # Vista de login como raíz
    path('home/', views.productos_view, name='home'),  # Vista después de login
     path('prueba/', views.prueba_view, name='prueba'),  # Vista después de login
    path('productos/', views.productos_view, name='productos'),
    path('salcobrand/', views.salcobrand_view, name='salcobrand'),
    path('cofar/', views.cofar_view, name='cofar'),  # Nueva vista para Cofar
    path('ahumada/', views.ahumada_view, name='ahumada'),  # Nueva vista para Cofar
    path('profar/', views.profar_view, name='profar'),  # Nueva vista para Cofar
    path('iniciar_extraccion/', views.iniciar_extraccion, name='iniciar_extraccion'),
    path('get_scraping_data/', views.get_scraping_data, name='get_scraping_data'),
    path('cancel_extraction/', views.cancel_extraction, name='cancel_extraction'),
    path('download_excel/', views.download_excel, name='download_excel'),
    path('save_to_mongo/', views.save_to_mongo, name='save_to_mongo'),
]