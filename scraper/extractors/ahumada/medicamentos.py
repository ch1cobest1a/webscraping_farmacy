import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException
from bs4 import BeautifulSoup
import time
from datetime import datetime

def perform_scraping(extracted_data):
    data_list = extracted_data['data']
    chrome_driver_path = r'.\chromedriver\chromedriver.exe'  # Cambia esta ruta al path de tu chromedriver
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--headless')  # Ejecutar en modo headless para mayor eficiencia

    driver = webdriver.Chrome(service=Service(chrome_driver_path), options=chrome_options)
    driver.set_window_size(1920, 1080)

    current_page = 1

    try:
        url = 'https://www.farmaciasahumada.cl/medicamentos'
        driver.get(url)
        time.sleep(5)

        def scroll_to_bottom():
            """Función para desplazar hacia abajo lentamente para cargar elementos dinámicamente."""
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Pausa para permitir la carga de nuevos productos

        while True:
            if extracted_data.get('cancel', False):
                print("Extracción cancelada por el usuario.")
                break

            # Extraer el contenido de la página
            html_content = driver.page_source
            soup = BeautifulSoup(html_content, 'html.parser')
            product_elements = soup.find_all('div', {'class': 'product product-tile-wrapper h-100 pb-lg-4 pb-3'})

            if not product_elements:
                print("No se encontraron elementos de producto.")
                break

            for product in product_elements:
                # Extraer la URL del producto
                product_link_element = product.find('a', href=True)
                product_url = 'https://www.farmaciasahumada.cl' + product_link_element['href'] if product_link_element else 'URL no disponible'

                # Extraer SKU
                sku_element = product.get('data-pid')
                sku = sku_element.strip() if sku_element else 'SKU no disponible'

                if any(item['SKU'] == sku for item in data_list):
                    continue

                # Extraer información del producto
                second_name_element = product.find('div', {'class': 'product-tile-brand'})
                second_name = second_name_element.get_text(strip=True) if second_name_element else 'Nombre no disponible'

                first_name_element = product.find('div', {'class': 'pdp-link'})
                first_name = first_name_element.find('a', href=True).get_text(strip=True) if first_name_element else 'Nombre no disponible'

                # Extraer precios
                price_sale = '0'
                price_normal = '0'

                price_sale_element = product.find('span', {'class': 'sales'})
                if price_sale_element:
                    price_value_element = price_sale_element.find('span', {'class': 'value'})
                    if price_value_element:
                        price_sale = price_value_element.get('content', '0')

                price_normal_element = product.find('span', {'class': 'strike-through list'})
                if price_normal_element:
                    price_normal_value_element = price_normal_element.find('span', {'class': 'value'})
                    if price_normal_value_element:
                        price_normal = price_normal_value_element.get('content', '0')

                if price_normal == '0' and price_sale != '0':
                    price_normal = price_sale
                    price_sale = '0'

                # Extraer imagen del producto
                product_image_element = product.find('img', {'class': 'tile-image'})
                product_image_url = product_image_element['src'] if product_image_element else 'URL no disponible'

                # Verificar si el producto tiene el banner "Ahumada Contigo Cronicos"
                has_banner = product.find('div', {'class': 'banner-contigo-plp'}) is not None

                # Obtener la categoría del producto
                category_element = product.get('data-categories')
                category = category_element if category_element else 'Categoría no disponible'

                extraction_date = datetime.now().strftime('%Y-%m-%d')

                product_data = {
                    'SKU': sku,
                    'Primer_Nombre': first_name,
                    'Segundo_Nombre': second_name,
                    'Precio_Venta': price_sale,
                    'Precio_Normal': price_normal,
                    'URL_Producto': product_url,
                    'URL_Imagen': product_image_url,
                    'Fecha_Extraccion': extraction_date,
                    'Tiene_Banner_Ahumada_Contigo': 'Sí' if has_banner else 'No',
                    'Categoria': category
                }

                data_list.append(product_data)

            extracted_data['current_page'] = current_page
            current_page += 1

            # Intentar hacer clic en "Más Resultados" para cargar más productos
            try:
                show_more_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn.btn-primary.col-8.col-sm-4.more"))
                )
                driver.execute_script("arguments[0].click();", show_more_button)
                time.sleep(3)  # Esperar a que la página cargue más productos

                # Desplazar hacia abajo después de cargar más productos
                scroll_to_bottom()
                
            except TimeoutException:
                print("No se encontró el botón 'Más Resultados'. Se ha alcanzado el final de los productos.")
                break
            except ElementClickInterceptedException:
                print("Elemento click interceptado. Intentando de nuevo...")
                try:
                    driver.execute_script("arguments[0].click();", show_more_button)
                    time.sleep(3)
                except:
                    print("No se pudo hacer clic en el botón 'Más Resultados' después de intentar de nuevo.")
                    break
            except Exception as e:
                print(f"No se pudo hacer clic en el botón 'Más Resultados': {e}")
                break

    except Exception as e:
        print(f"Error durante el proceso de extracción de datos: {e}")
    finally:
        driver.quit()
        extracted_data['extraction_complete'] = True
