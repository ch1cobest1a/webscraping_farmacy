from flask import Flask, render_template, request
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    data = []
    if request.method == 'POST':
        url = request.form['url']
        
        # Usamos Selenium para abrir la página y extraer datos
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
        driver.get(url)

        # Ejemplo: Extraer el título de la página
        title = driver.title
        data.append({"title": title})

        driver.quit()

    return render_template('index.html', data=data)

if __name__ == '__main__':
    app.run(debug=True)
