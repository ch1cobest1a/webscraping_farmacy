import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

def perform_scraping_profar(extracted_data, categoria_url):
    # Configuración del WebDriver
    chrome_driver_path = r'.\chromedriver\chromedriver.exe'  # Cambia esta ruta según tu entorno
    chrome_options = webdriver.ChromeOptions()

    # Configuración correcta del driver usando Service
    service = Service(chrome_driver_path)  # Usa Service para definir el path del driver

    # Inicializa el navegador usando Service
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.maximize_window()

    page = 1
    try:
        while True:
            # Navegar a la URL de la categoría y página
            url = f'https://www.profar.cl/{categoria_url}?page={page}'
            print(f"Navegando a la página {page}: {url}")
            driver.get(url)

            # Espera para cargar el contenido
            time.sleep(3)

            # Verificar si no hay más productos en la página
            no_products_message = driver.find_elements(By.CSS_SELECTOR, '.vtex-search-result-3-x-searchNotFoundOops')
            if no_products_message:
                print("No se han encontrado más productos. Finalizando.")
                break

            # Desplázate hacia abajo para asegurarte de que todos los productos estén visibles
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            # Extraer todos los productos
            products = driver.find_elements(By.CSS_SELECTOR, '.vtex-search-result-3-x-galleryItem')
            if not products:
                print("No se encontraron productos en esta página. Finalizando.")
                break

            # Iterar sobre los productos
            for product in products:
                try:
                    # Inicializa variables
                    product_name = ""
                    list_price = ""
                    selling_price = ""
                    product_url = ""
                    product_image_url = ""
                    sku = ""

                    # Selectores para el nombre del producto
                    name_selectors = [
                        '.vtex-product-summary-2-x-productBrand',
                        '.vtex-product-summary-2-x-nameWrapper',
                        '.vtex-product-summary-2-x-productNameContainer'
                    ]
                    for selector in name_selectors:
                        if product.find_elements(By.CSS_SELECTOR, selector):
                            product_name = product.find_element(By.CSS_SELECTOR, selector).text.strip()
                            break

                    # Extraer el precio de lista
                    try:
                        list_price_integer = product.find_element(By.CSS_SELECTOR, '.vtex-product-price-1-x-currencyInteger--vitrinaProfarTeProtege').text.strip()
                        list_price_decimal = product.find_element(By.CSS_SELECTOR, '.vtex-product-price-1-x-currencyGroup--vitrinaProfarTeProtege').text.strip()
                        list_price_cents = product.find_elements(By.CSS_SELECTOR, '.vtex-product-price-1-x-currencyInteger--vitrinaProfarTeProtege')[-1].text.strip()
                        list_price = f"{list_price_integer}{list_price_decimal}{list_price_cents}"
                    except NoSuchElementException:
                        list_price = "No disponible"

                    # Extraer el precio de oferta
                    try:
                        selling_price_integer = product.find_element(By.CSS_SELECTOR, '.vtex-product-price-1-x-sellingPriceValue--vitrinaProfarTeProtege .vtex-product-price-1-x-currencyInteger--vitrinaProfarTeProtege').text.strip()
                        selling_price_decimal = product.find_element(By.CSS_SELECTOR, '.vtex-product-price-1-x-sellingPriceValue--vitrinaProfarTeProtege .vtex-product-price-1-x-currencyGroup--vitrinaProfarTeProtege').text.strip()
                        selling_price_cents = product.find_elements(By.CSS_SELECTOR, '.vtex-product-price-1-x-sellingPriceValue--vitrinaProfarTeProtege .vtex-product-price-1-x-currencyInteger--vitrinaProfarTeProtege')[-1].text.strip()
                        selling_price = f"{selling_price_integer}{selling_price_decimal}{selling_price_cents}"
                    except NoSuchElementException:
                        selling_price = "No disponible"

                    # URL del producto
                    if product.find_elements(By.CSS_SELECTOR, 'a'):
                        product_url = product.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
                        if not product_url.startswith('https://'):
                            product_url = f'https://www.profar.cl{product_url}'

                    # Extraer la URL de la imagen usando el selector correcto
                    try:
                        image_element = product.find_element(By.CSS_SELECTOR, '.vtex-product-summary-2-x-imageNormal')
                        product_image_url = image_element.get_attribute('src')
                        # Extraer SKU desde la URL de la imagen
                        sku = product_image_url.split('/ids/')[1].split('-')[0]
                    except NoSuchElementException:
                        product_image_url = "No disponible"
                        sku = "No disponible"

                    # Si se extrajeron los datos correctamente, se almacenan
                    if product_name and list_price and selling_price and product_url:
                        extracted_data['data'].append({
                            'Nombre': product_name,
                            'Precio lista': list_price,
                            'Precio oferta': selling_price,
                            'URL': product_url,
                            'Imagen': product_image_url,
                            'SKU': sku,
                            'Programa': '',  # Campo para el programa (nurtec-45-off)
                            'Laboratorio': '',  # Campo para el laboratorio (ej. PFIZER)
                            'Categoría': categoria_url,  # Almacenar la categoría proporcionada
                            'Página': page
                        })
                        print(f"Producto extraído: {product_name}, Precio lista: {list_price}, Precio oferta: {selling_price}, URL: {product_url}, SKU: {sku}")
                    else:
                        print(f"Producto incompleto en página {page}, posibles datos faltantes.")

                except Exception as e:
                    print(f"Error al extraer producto: {e}")

            # Cambia de página
            page += 1
            time.sleep(3)

    finally:
        driver.quit()
        extracted_data['extraction_complete'] = True
