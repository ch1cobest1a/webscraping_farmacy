from django.shortcuts import render
from django.http import JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
import threading
import os
from datetime import datetime

# Importar módulos de extracción de la carpeta extractors
# Salcobrand
from scraper.extractors.salcobrand import medicamentos as salcobrand_medicamentos
from scraper.extractors.salcobrand import vitaminas_suplementos as salcobrand_vitaminas_suplementos


#Profar
from scraper.extractors.profar import medicamentos as profar_medicamentos


#cofar
from scraper.extractors.cofar import medicamentos as cofar_medicamentos
from scraper.extractors.cofar import dermocosmeticos as cofar_dermocosmeticos
from scraper.extractors.cofar import vitaminas_suplementos as cofar_vitaminas_suplementos
from scraper.extractors.cofar import todo as cofar_todo


# Diccionario para almacenar datos de cada farmacia
extracted_data_global = {
    'salcobrand': {'data': [], 'extraction_complete': False, 'file_path': '', 'thread': None, 'cancel': False},
    'profar': {'data': [], 'extraction_complete': False, 'file_path': '', 'thread': None, 'cancel': False},
    'cofar': {'data': [], 'extraction_complete': False, 'file_path': '', 'thread': None, 'cancel': False}
}

# Nueva vista para la página de productos
def productos_view(request):
    return render(request, 'scraper/productos.html')

# Vista para la página de Salcobrand
def salcobrand_view(request):
    return render(request, 'scraper/salcobrand.html')

# Vista para la página de Profar
def profar_view(request):
    return render(request, 'scraper/profar.html')

# Vista para la página de cofar
def cofar_view(request):
    return render(request, 'scraper/cofar.html')



@csrf_exempt
def iniciar_extraccion(request):
    farmacia = request.GET.get('farmacia', '')
    categoria = request.GET.get('categoria', '')

    if farmacia not in extracted_data_global:
        return JsonResponse({'error': 'Farmacia no soportada'}, status=400)

    # Restablecer la cancelación
    extracted_data_global[farmacia]['cancel'] = False

    if categoria == 'medicamentos':
        if farmacia == 'salcobrand':
            thread = threading.Thread(target=salcobrand_medicamentos.perform_scraping, args=(extracted_data_global['salcobrand'], 'https://salcobrand.cl/medicamentos', 'Medicamentos'))
        elif farmacia == 'profar':
            thread = threading.Thread(target=profar_medicamentos.perform_scraping, args=(extracted_data_global['profar'], 'https://profar.cl/medicamentos', 'Medicamentos'))
        elif farmacia == 'cofar':
            thread = threading.Thread(target=cofar_medicamentos.perform_scraping, args=(extracted_data_global['cofar'], 'https://cofar.cl/medicamentos', 'Medicamentos'))
        else:
            return JsonResponse({'error': 'Categoría o farmacia no soportada'}, status=400)

    elif categoria == 'dermocosmeticos':
        if farmacia == 'cofar':
            thread = threading.Thread(target=cofar_dermocosmeticos.perform_scraping, args=(extracted_data_global['cofar'], 'https://cofar.cl/dermocosmeticos', 'Dermocosmeticos'))
        else:
            return JsonResponse({'error': 'Categoría o farmacia no soportada'}, status=400)

    elif categoria == 'vitaminas_suplementos':
        if farmacia == 'cofar':
            thread = threading.Thread(target=cofar_vitaminas_suplementos.perform_scraping, args=(extracted_data_global['cofar'], 'https://cofar.cl/vitaminas-suplementos', 'Vitaminas y Suplementos'))
        elif farmacia == 'salcobrand':
            thread = threading.Thread(target=salcobrand_vitaminas_suplementos.perform_scraping, args=(extracted_data_global['salcobrand'], 'https://salcobrand.cl/t/vitaminas-y-suplementos', 'Vitaminas y Suplementos'))
        else:
            return JsonResponse({'error': 'Categoría o farmacia no soportada'}, status=400)
        
    elif categoria == 'todo':
        if farmacia == 'cofar':
            thread = threading.Thread(target=cofar_todo.perform_scraping_todo, args=(extracted_data_global['cofar'],))
        else:
            return JsonResponse({'error': 'Categoría o farmacia no soportada'}, status=400)

    else:
        return JsonResponse({'error': 'Categoría no soportada'}, status=400)

    # Guardar el hilo para cancelación futura
    extracted_data_global[farmacia]['thread'] = thread
    thread.start()
    return JsonResponse({'status': f'Extracción iniciada para {farmacia} - {categoria}'})


def cancel_extraction(request):
    farmacia = request.GET.get('farmacia', '')

    if farmacia in extracted_data_global:
        extracted_data_global[farmacia]['cancel'] = True  # Señal para detener el proceso
        
        # Definir directorios basados en la farmacia
        if farmacia == 'salcobrand':
            save_directory = os.path.join(os.getcwd(), 'Excel', 'Farmacia_Salcobrand')
        elif farmacia == 'cofar':
            save_directory = os.path.join(os.getcwd(), 'Excel', 'Farmacia_Cofar')
        else:
            return JsonResponse({'error': 'Farmacia no soportada'}, status=400)

        # Obtener el nombre del archivo más reciente si hay múltiples archivos
        all_files = [os.path.join(save_directory, f) for f in os.listdir(save_directory) if f.endswith('.xlsx')]
        
        if all_files:
            # Ordenar los archivos por fecha de creación (modificación)
            all_files.sort(key=os.path.getmtime, reverse=True)
            temp_file_path = all_files[0]  # Obtener el archivo más reciente
        else:
            return JsonResponse({'error': 'No hay archivos disponibles para descargar'}, status=404)

        if os.path.exists(temp_file_path):
            print(f"Archivo encontrado en: {temp_file_path}")  # Debugging
            try:
                response = FileResponse(open(temp_file_path, 'rb'))
                response['Content-Disposition'] = f'attachment; filename={os.path.basename(temp_file_path)}'
                # Actualizar el estado de cancelación para evitar continuar con la extracción
                extracted_data_global[farmacia]['extraction_complete'] = True
                return response
            except Exception as e:
                print(f"Error al abrir el archivo: {e}")  # Debugging
                return JsonResponse({'error': 'No se pudo abrir el archivo para la descarga'}, status=500)
        else:
            print(f"Archivo no encontrado: {temp_file_path}")  # Debugging
            return JsonResponse({'error': 'Archivo temporal no encontrado'}, status=404)
    else:
        return JsonResponse({'error': 'Farmacia no encontrada'}, status=400)


# Endpoint para obtener datos de scraping
# Endpoint para obtener datos de scraping
# Endpoint para obtener datos de scraping
def get_scraping_data(request):
    farmacia = request.GET.get('farmacia', '')
    if farmacia in extracted_data_global:
        data = extracted_data_global[farmacia]['data']
        extraction_complete = extracted_data_global[farmacia]['extraction_complete']
        file_path = extracted_data_global[farmacia]['file_path']
        current_page = extracted_data_global[farmacia].get('current_page', 1)  # Obtener el número de página actual

        return JsonResponse({
            'data': data,
            'extraction_complete': extraction_complete,
            'file_url': file_path,
            'current_page': current_page  # Incluir número de página actual en la respuesta
        })
    else:
        return JsonResponse({'error': 'Farmacia no encontrada'}, status=400)
# Endpoint para obtener el archivo temporal
def get_temporary_file(request):
    file_name = request.GET.get('file_name', '')
    file_path = os.path.join(os.getcwd(), 'Excel', 'Farmacia_Salcobrand', file_name)
    
    if os.path.exists(file_path):
        response = FileResponse(open(file_path, 'rb'))
        response['Content-Disposition'] = f'attachment; filename={file_name}'
        return response
    else:
        return JsonResponse({'error': 'Archivo no encontrado'}, status=404)
