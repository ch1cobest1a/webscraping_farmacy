import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime

def get_temp_file_path():
    save_directory = os.path.join(os.getcwd(), "Excel", "Farmacia_Salcobrand")
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)
    # Agregar fecha y hora actuales al nombre del archivo
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    temp_file_name = f"Salcobrand_medicamento_{timestamp}.xlsx"
    temp_file_path = os.path.join(save_directory, temp_file_name)
    print(f"Ruta del archivo temporal generada: {temp_file_path}")  # Debugging
    return temp_file_path

def perform_scraping(extracted_data):
    data_list = extracted_data['data']
    chrome_driver_path = r'.\chromedriver\chromedriver.exe'
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--headless')  # Añadir modo sin cabeza para mejorar la eficiencia

    driver = webdriver.Chrome(service=Service(chrome_driver_path), options=chrome_options)
    driver.maximize_window()

    # Inicializar la página actual en 1
    current_page = 1

    try:
        url = 'https://salcobrand.cl/t/medicamentos'
        driver.get(url)
        time.sleep(10)

        # Usar el archivo temporal existente para guardar datos
        temp_file_path = extracted_data['file_path'] = get_temp_file_path()

        if os.path.exists(temp_file_path):
            try:
                existing_data = pd.read_excel(temp_file_path).to_dict('records')
                existing_skus = {item['SKU'] for item in existing_data}
                data_list.extend(existing_data)
            except Exception as e:
                print(f"Error al leer el archivo temporal: {e}")
                existing_skus = set()
        else:
            existing_skus = set()

        while True:
            if extracted_data.get('cancel', False):
                print("Extracción cancelada por el usuario.")
                break

            html_content = driver.page_source
            soup = BeautifulSoup(html_content, 'html.parser')
            product_elements = soup.find_all('div', {'class': 'col-xs-6 col-md-6 col-lg-4 padding-adjust'})

            if not product_elements:
                print("No se encontraron elementos de producto")
                break

            for product in product_elements:
                product_link_element = product.find('div', {'class': 'product-image'}).find('a')
                product_url = 'https://salcobrand.cl' + product_link_element['href'] if product_link_element else 'URL no disponible'
                sku = product_url.split('default_sku=')[-1].split('&')[0] if product_link_element else 'SKU no disponible'

                if sku in existing_skus:
                    continue

                product_info = product.find('span', {'class': 'product-info truncate'}).text.strip()
                product_nombre = product.find('span', {'class': 'product-name truncate'}).text.strip()

                pharmacy_price_element = product.find('div', {'class': 'original-price'})
                pharmacy_price = pharmacy_price_element.span.text.strip() if pharmacy_price_element else ''
                if not pharmacy_price:
                    pharmacy_price_element = product.find('div', {'class': 'sale-price'})
                    pharmacy_price = pharmacy_price_element.text.strip() if pharmacy_price_element else ''
                pharmacy_price = re.sub(r'\D', '', pharmacy_price)

                internet_price_element = product.find('div', {'class': 'sale-price secondary-price'})
                internet_price = internet_price_element.span.text.strip() if internet_price_element else ''
                internet_price = re.sub(r'\D', '', internet_price)

                sbpay_element = product.find('div', {'class': 'internet-sale-price'})
                sbpay = sbpay_element.span.text.strip() if sbpay_element else ''
                sbpay = re.sub(r'\D', '', sbpay)

                product_image_element = product.find('img', {'class': 'img-responsive'})
                product_image_url = product_image_element['src'] if product_image_element and 'src' in product_image_element.attrs else 'URL no disponible'

                extraction_date = datetime.now().strftime('%Y-%m-%d')

                product_data = {
                    'SKU': sku,
                    'Primer_nombre': product_info,
                    'Segundo_nombre': product_nombre,
                    'Precio_Farmacia': pharmacy_price,
                    'Precio_Internet': internet_price,
                    'SBPay': sbpay,
                    'URL_Producto': product_url,
                    'URL_Imagen': product_image_url,
                    'Fecha_Extraccion': extraction_date,
                    'Pagina_Salcobrand': current_page  # Añadimos la página actual del sitio de Salcobrand
                }

                data_list.append(product_data)
                existing_skus.add(sku)

                save_to_temp_excel(data_list, temp_file_path)

                if extracted_data['cancel']:
                    print("Proceso de extracción cancelado.")
                    break

            # Incrementar la página actual y actualizar en extracted_data
            extracted_data['current_page'] = current_page
            current_page += 1

            if extracted_data.get('cancel', False):
                break

            try:
                next_page_link = driver.find_element(By.XPATH, "//nav[@class='paginator text-center']//ul[@class='pagination pagination-sm']/li/a[contains(text(), '»')]")
                driver.execute_script("arguments[0].click();", next_page_link)
                time.sleep(3)
            except (ElementClickInterceptedException, TimeoutException) as e:
                print(f"No se pudo hacer clic en el enlace a la siguiente página: {e}")
                break
            except Exception as e:
                print(f"No se pudo encontrar o hacer clic en el enlace a la página siguiente: {e}")
                break

    except Exception as e:
        print(f"Error durante el proceso de extracción de datos: {e}")
    finally:
        driver.quit()
        extracted_data['extraction_complete'] = True

def save_to_temp_excel(data, temp_file_path):
    try:
        combined_df = pd.DataFrame(data)
        combined_df.drop_duplicates(subset='SKU', keep='first', inplace=True)
        combined_df.to_excel(temp_file_path, index=False)
        print(f"Datos guardados temporalmente en {temp_file_path}")
    except Exception as e:
        print(f"Error al guardar datos en el archivo temporal: {e}")

def consolidate_to_final_excel(temp_file_path):
    final_file_path = os.path.join(os.path.dirname(temp_file_path), "medicamento_Salcobrand_final.xlsx")
    if os.path.exists(temp_file_path):
        os.rename(temp_file_path, final_file_path)
        print(f"Datos consolidados guardados en {final_file_path}")
