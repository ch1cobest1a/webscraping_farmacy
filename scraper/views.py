from django.shortcuts import render, redirect
from django.http import JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
import threading
from io import BytesIO
import pandas as pd
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from pymongo import MongoClient

# Importar las funciones de scraping para cada farmacia
from scraper.extractors.salcobrand.salcobrand import perform_scraping_salcobrand as salcobrand_scraping
from scraper.extractors.profar.profar import perform_scraping_profar as profar_scraping  # Asegúrate de tener esta función en tu archivo profar.py
from scraper.extractors.cofar.cofar import perform_scraping_cofar as cofar_scraping 

# Diccionario para almacenar datos de cada farmacia
extracted_data_global = {
    'salcobrand': {'data': [], 'extraction_complete': False, 'threads': [], 'cancel': False},
    'profar': {'data': [], 'extraction_complete': False, 'threads': [], 'cancel': False},  # Agregamos Profar
    'cofar': {'data': [], 'extraction_complete': False, 'threads': [], 'cancel': False},
}

# Diccionario con las categorías y sus respectivas funciones para cada farmacia
categorias_urls_por_farmacia = {
    'salcobrand': {
        'medicamentos': salcobrand_scraping,
        'vitaminas-y-suplementos': salcobrand_scraping,
        'dermocoaching': salcobrand_scraping,
        'cuidado-personal': salcobrand_scraping,
        'belleza': salcobrand_scraping,
        'infantil-y-mama': salcobrand_scraping,
        'cuidado-de-la-salud': salcobrand_scraping,
        'adulto-mayor': salcobrand_scraping,
        'mascotas': salcobrand_scraping,
        'marcas-exclusivas': salcobrand_scraping,
        'emprendedores': salcobrand_scraping,
        'products/sales': salcobrand_scraping,
    },
    'profar': {  # Agregamos las categorías de Profar
        'medicamentos': profar_scraping,
        'dermocosmetica': profar_scraping,
        'belleza': profar_scraping,
        'cuidado-personal': profar_scraping,
        'salud-animal': profar_scraping,
        'descuentos-imperdibles': profar_scraping,
    },
    'cofar': {  # Agregamos las categorías de Profar
        'medicamentos': cofar_scraping,
        'dermocosmeticos': cofar_scraping,
        'vitaminas-y-suplementos': cofar_scraping,
        'cyber-monday': cofar_scraping,
        'medicamentos/cyber-monday-medicamentos': cofar_scraping,
    },
}

# Vista para la página principal de productos
def productos_view(request):
    return render(request, 'scraper/home.html')

# Nueva vista para la página de Salcobrand
def salcobrand_view(request):
    return render(request, 'scraper/Farmacias/salcobrand.html')

# Vista para Profar
def profar_view(request):
    return render(request, 'scraper/Farmacias/profar.html')

def cofar_view(request):
    return render(request, 'scraper/Farmacias/cofar.html')

def ahumada_view(request):
    return render(request, 'scraper/Farmacias/ahumada.html')

def prueba_view(request):
    return render(request, 'scraper/Prueba/prueba.html')

@csrf_exempt
def iniciar_extraccion(request):
    farmacia = request.GET.get('farmacia', '')
    categorias = request.GET.getlist('categoria')  # Soporta múltiples categorías

    if farmacia not in categorias_urls_por_farmacia:
        return JsonResponse({'error': 'Farmacia no soportada'}, status=400)

    # Restablecer el estado de extracción antes de comenzar
    extracted_data_global[farmacia]['cancel'] = False
    extracted_data_global[farmacia]['extraction_complete'] = False

    # No limpiamos `extracted_data_global[farmacia]['data']` para mantener datos de extracciones previas
    if not extracted_data_global[farmacia]['data']:
        extracted_data_global[farmacia]['data'] = []

    threads = []

    # Selección de categorías y módulos de extracción para la farmacia seleccionada
    for categoria in categorias:
        if categoria in categorias_urls_por_farmacia[farmacia]:
            scraping_func = categorias_urls_por_farmacia[farmacia][categoria]
            thread = threading.Thread(target=scraping_func, args=(extracted_data_global[farmacia], categoria))
            threads.append(thread)
        else:
            return JsonResponse({'error': f'Categoría {categoria} no soportada para {farmacia}'}, status=400)

    # Iniciar todos los hilos
    for thread in threads:
        thread.start()

    # Guardar los hilos para cancelación futura
    extracted_data_global[farmacia]['threads'] = threads
    return JsonResponse({'status': f'Extracción iniciada para {farmacia} - {", ".join(categorias)}'})


def cancel_extraction(request):
    farmacia = request.GET.get('farmacia', '')

    if farmacia in extracted_data_global:
        extracted_data_global[farmacia]['cancel'] = True  # Señal para detener el proceso

        # Generar el archivo Excel con los datos extraídos hasta el momento
        data_list = extracted_data_global[farmacia]['data']
        categoria = extracted_data_global[farmacia]['category']  # Obtener la categoría seleccionada

        # Si no hay datos, no hay nada que guardar
        if not data_list:
            return JsonResponse({'error': 'No hay datos para guardar.'}, status=400)

        df = pd.DataFrame(data_list)
        output = BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)

        # Generar el nombre del archivo dinámicamente basado en la farmacia, categoría y fecha
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = generar_nombre_archivo(farmacia, categoria, timestamp)

        # Enviar el archivo como respuesta
        response = FileResponse(output, as_attachment=True, filename=filename)
        response['filename'] = filename  # Incluir el nombre del archivo en los encabezados de respuesta
        return response

    else:
        return JsonResponse({'error': 'Farmacia no encontrada'}, status=400)

# Definición de la función download_excel
def download_excel(request):
    farmacia = request.GET.get('farmacia', '')

    if farmacia in extracted_data_global:
        data_list = extracted_data_global[farmacia]['data']

        if not data_list:
            return JsonResponse({'error': 'No hay datos para descargar.'}, status=400)

        df = pd.DataFrame(data_list)
        output = BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)

        # Generar el nombre del archivo dinámicamente basado en la farmacia, la categoría y la fecha
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{farmacia.capitalize()}_{timestamp}.xlsx"

        # Enviar el archivo como respuesta
        return FileResponse(output, as_attachment=True, filename=filename)

    return JsonResponse({'error': 'Farmacia no encontrada'}, status=400)


def generar_nombre_archivo(farmacia, categoria, timestamp):
    """Genera el nombre del archivo basado en la farmacia, la categoría y la fecha."""
    return f"{farmacia.capitalize()}_{categoria.replace('_', ' ').title()}_{timestamp}.xlsx"


def get_scraping_data(request):
    farmacia = request.GET.get('farmacia', '')
    if farmacia in extracted_data_global:
        data = extracted_data_global[farmacia]['data']
        extraction_complete = extracted_data_global[farmacia]['extraction_complete']
        current_page = extracted_data_global[farmacia].get('current_page', 1)

        # Asegurarse de que los datos se están enviando correctamente
        return JsonResponse({
            'data': data,
            'extraction_complete': extraction_complete,
            'current_page': current_page
        })
    else:
        return JsonResponse({'error': 'Farmacia no encontrada'}, status=400)


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if username and password:
            if password == 'admin':  # Contraseña fija para este ejemplo
                return redirect('home')
            else:
                messages.error(request, 'Contraseña incorrecta.')
                return redirect('login')
        elif username:
            request.session['username'] = username
            messages.info(request, 'Ingrese su contraseña.')
            return redirect('login')

    return render(request, 'scraper/base.html')


# Configura la conexión a MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['farcyprice']  # Nombre de la base de datos

from datetime import datetime

@csrf_exempt
def save_to_mongo(request):
    if request.method == 'POST':
        try:
            if 'file' in request.FILES:
                file = request.FILES['file']
                data = json.load(file)  # Leer los datos del archivo
            else:
                data = json.loads(request.body)

            farmacia = data.get('farmacia')
            collection_name = farmacia
            collection = db[collection_name]

            # Filtra los datos para eliminar SKUs duplicados dentro del mismo proceso
            unique_data = []
            seen_skus = set()

            for item in data.get('data'):
                sku = item.get('SKU')
                if sku not in seen_skus:
                    item['Fecha_Extraccion'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    unique_data.append(item)
                    seen_skus.add(sku)

            # Inserta los datos únicos en MongoDB
            if unique_data:
                collection.insert_many(unique_data)

            return JsonResponse({'status': 'success', 'message': 'Datos guardados en MongoDB'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)