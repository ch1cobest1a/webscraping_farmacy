// profar.js - Ejemplo de código que extrae el JSON-LD
const script = document.querySelector('script[type="application/ld+json"]');
if (script) {
    return JSON.parse(script.innerText);
} else {
    return null;
}
