import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime

def get_temp_file_path():
    save_directory = os.path.join(os.getcwd(), "Excel", "Farmacia_Cofar")
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    temp_file_name = f"Cofar_medicamento_{timestamp}.xlsx"
    temp_file_path = os.path.join(save_directory, temp_file_name)
    print(f"Ruta del archivo temporal generada: {temp_file_path}")  # Debugging
    return temp_file_path

def perform_scraping_cofar(extracted_data, categoria_url):
    data_list = extracted_data['data']
    chrome_driver_path = r'.\chromedriver\chromedriver.exe'
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-dev-shm-usage')
    ##chrome_options.add_argument('--headless')

    driver = webdriver.Chrome(service=Service(chrome_driver_path), options=chrome_options)
    driver.maximize_window()

    current_page = 1

    try:
         # Verificar si es la página de sales (ventas) o una categoría regular
        if categoria_url == 'medicamentos/cyber-monday-medicamentos':
            url = 'https://cofar.cl/medicamentos/cyber-monday-medicamentos'  # URL específica para sales
        else:
            url = f'https://cofar.cl/{categoria_url}?page={current_page}'

        driver.get(url)
        time.sleep(10)

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
            product_elements = soup.find_all("div", class_="product-card")

            if not product_elements:
                print("No se encontraron elementos de producto")
                break

            for product in product_elements:
                try:
                    product_link_element = product.find("a", href=True)
                    product_url = 'https://cofar.cl' + product_link_element['href'] if product_link_element else 'URL no disponible'
                    
                    # Extraer SKU de la URL del producto
                    sku = product_url.split('/product/')[-1].split('/')[0] if product_url != 'URL no disponible' else 'SKU no disponible'

                    product_image_element = product.find("img", class_="card-img-top")
                    product_image_url = product_image_element['src'] if product_image_element else 'URL no disponible'
                    product_name = product.find("div", class_="black-title").text.strip() if product.find("div", class_="black-title") else "Nombre no disponible"

                    # Extraer precios
                    normal_price = "0"
                    current_price = "0"

                    # Correctamente identificando precios normales y actuales
                    normal_price_element = product.find("div", class_="partner-original-price")
                    if normal_price_element:
                        normal_price = normal_price_element.find("span", class_="false line-through").text.strip()
                        normal_price = re.sub(r'[^\d]', '', normal_price)  # Eliminar todo lo que no sea dígito

                    current_price_element = product.find("div", class_="partner-price")
                    if current_price_element:
                        current_price = current_price_element.find("span", class_="value").text.strip()
                        current_price = re.sub(r'[^\d]', '', current_price)  # Eliminar todo lo que no sea dígito
                    
                    # Si no hay precio original, usar el precio actual como normal
                    if normal_price == "0" and current_price != "0":
                        normal_price = current_price
                        current_price = "0"

                    extraction_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    product_data = {
                        'SKU': sku,
                        'Nombre del producto': product_name,
                        'Precio normal': normal_price,
                        'Precio actual': current_price,
                        'URL Producto': product_url,
                        'URL Imagen': product_image_url,
                        'Fecha_Extraccion': extraction_date,
                        'Pagina_Cofar': current_page
                    }

                    data_list.append(product_data)
                    save_to_temp_excel(data_list, temp_file_path)

                except Exception as e:
                    print(f"Error al extraer producto: {e}")

            # Comprobación de si hay más páginas o si el usuario ha solicitado cancelar
            try:
                next_page_link = driver.find_element(By.XPATH, "//a[contains(@class, 'page-next')]")
                next_page_link.click()
                time.sleep(3)
                current_page += 1
                extracted_data['current_page'] = current_page
            except NoSuchElementException:
                print("No se encontró el enlace a la siguiente página. Finalizando extracción.")
                break
            except (ElementClickInterceptedException, TimeoutException) as e:
                print(f"No se pudo hacer clic en el enlace a la siguiente página: {e}")
                break

    except Exception as e:
        print(f"Error durante el proceso de extracción de datos: {e}")
    finally:
        driver.quit()
        extracted_data['extraction_complete'] = True

def save_to_temp_excel(data, temp_file_path):
    try:
        combined_df = pd.DataFrame(data)
        combined_df.drop_duplicates(subset='URL Producto', keep='first', inplace=True)
        combined_df.to_excel(temp_file_path, index=False)
        print(f"Datos guardados temporalmente en {temp_file_path}")
    except Exception as e:
        print(f"Error al guardar datos en el archivo temporal: {e}")
