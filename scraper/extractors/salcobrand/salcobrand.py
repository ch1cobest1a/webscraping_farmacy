import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime

# Función común para realizar scraping en cualquier categoría de Salcobrand
def perform_scraping_salcobrand(extracted_data, categoria_url):
    data_list = extracted_data['data']
    chrome_driver_path = r'.\chromedriver\chromedriver.exe'  # Cambia esta ruta al path de tu chromedriver
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--headless')  # Modo sin cabeza para mayor eficiencia

    driver = webdriver.Chrome(service=Service(chrome_driver_path), options=chrome_options)
    driver.maximize_window()

    current_page = 1

    try:
        # Verificar si es la página de sales (ventas) o una categoría regular
        if categoria_url == 'products/sales':
            url = 'https://salcobrand.cl/products/sales'  # URL específica para sales
        else:
            url = f'https://salcobrand.cl/t/{categoria_url}'  # URL para categorías regulares

        driver.get(url)
        time.sleep(10)  # Esperar a que se cargue la página

        while True:
            if extracted_data.get('cancel', False):
                print("Extracción cancelada por el usuario.")
                break

            html_content = driver.page_source
            soup = BeautifulSoup(html_content, 'html.parser')
            product_elements = soup.find_all('div', {'class': 'col-xs-6 col-md-6 col-lg-4 padding-adjust'})

            if not product_elements:
                print("No se encontraron elementos de producto.")
                break

            for product in product_elements:
                product_link_element = product.find('div', {'class': 'product-image'}).find('a')
                product_url = 'https://salcobrand.cl' + product_link_element['href'] if product_link_element else 'URL no disponible'
                sku = product_url.split('default_sku=')[-1].split('&')[0] if product_link_element else 'SKU no disponible'

                # Evitar duplicados
                if any(item['SKU'] == sku for item in data_list):
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

                extraction_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

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
                    'Pagina_Salcobrand': current_page,
                    'Categoria': categoria_url  # Agregar la categoría en el archivo Excel
                }

                data_list.append(product_data)

            extracted_data['current_page'] = current_page
            current_page += 1

            try:
                next_page_link = driver.find_element(By.XPATH, "//nav[@class='paginator text-center']//ul[@class='pagination pagination-sm']/li/a[contains(text(), '»')]")
                driver.execute_script("arguments[0].click();", next_page_link)
                time.sleep(3)
            except (ElementClickInterceptedException, TimeoutException) as e:
                print(f"No se pudo hacer clic en el enlace a la siguiente página: {e}")
                break

    except Exception as e:
        print(f"Error durante el proceso de extracción de datos: {e}")
    finally:
        driver.quit()
        extracted_data['extraction_complete'] = True
