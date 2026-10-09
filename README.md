# ARCANA — Laboratorio web de escrituras

Prototipo ejecutable de ARCANA: una aplicación web para explorar transformaciones de texto, patrones de frecuencia y fotografías de manuscritos.

## Qué incluye esta versión
- Interfaz adaptable a móvil y escritorio.
- Entrada de texto y carga de imagen.
- Transformaciones de texto: espejo de caracteres, inversión del orden, lectura inversa por palabras, ROT13, César (0–25), Atbash y sustitución simple configurable.
- Análisis de frecuencias de caracteres y n-gramas.
- Generación de candidatos ordenados por una puntuación heurística transparente.
- API FastAPI y extracción OCR opcional con Tesseract instalado en el sistema.
- Mensajes explícitos de incertidumbre: las puntuaciones no son probabilidades de traducción.

## Requisitos
- Python 3.10+
- (Opcional para OCR real) Tesseract OCR instalado en el sistema operativo. La librería `pytesseract` no instala el motor Tesseract por sí sola.

## Ejecutar localmente
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```
Abre http://127.0.0.1:8000

Sin Tesseract instalado, el análisis de texto funciona; la aplicación informará si no puede procesar OCR.

## Publicar en internet
La carpeta incluye un `Dockerfile` para despliegue en cualquier plataforma compatible con contenedores (por ejemplo, Render, Railway, Fly.io o un VPS).
1. Sube el contenido de esta carpeta a un repositorio Git.
2. Crea un servicio web desde el repositorio y usa el Dockerfile.
3. Configura el puerto según la plataforma (la app usa `PORT` si está definido).
4. Para OCR, el Dockerfile instala Tesseract y el paquete de idioma inglés; puedes añadir paquetes de idioma cuando se necesiten.
5. Activa HTTPS en la plataforma y establece límites de carga para producción.

## Límites científicos
- Una transformación que produce texto legible no demuestra que sea la lectura correcta.
- Las escrituras no descifradas pueden no representar una lengua, pueden ser códigos o pueden necesitar contexto arqueológico.
- La OCR puede equivocarse con manuscritos, símbolos raros, texto vertical o caracteres deteriorados.
- La puntuación actual sirve para ordenar candidatos, no como confianza estadística calibrada.
- El prototipo no envía el texto a servicios externos ni guarda análisis en una base de datos.

## Próximas mejoras recomendadas
1. Procesamiento de imagen avanzado (binarización, rotación, segmentación y OCR específico).
2. Corpus verificables por lengua/escritura con fuentes y licencias.
3. Detección de escritura RTL, transliteraciones y normalización Unicode ampliada.
4. Algoritmos de búsqueda para cifrados clásicos y sustitución polialfabética.
5. Evaluación de hipótesis por modelos lingüísticos con procedencia y controles contra traducciones inventadas.
6. Autenticación, límites de uso, almacenamiento opcional y registro de auditoría antes de una publicación de alto tráfico.
