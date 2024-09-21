import re
import requests
from bs4 import BeautifulSoup
import csv
import os


def extraer_datos_socios(contenido):
    # Patrón más flexible para encontrar socios con sus datos
    patron = r'(?:Socios?:?\s*)?([A-Z][A-ZÀ-ÿa-zà-ÿ]+(?:\s+[A-Z][A-ZÀ-ÿa-zà-ÿ]+){1,4})(?:[^,]*?,\s*)?(?:.*?DNI[^\d]*(\d{1,2}\.?\d{3}\.?\d{3}))(?:.*?(?:CUIT|CUIL)[^\d]*(\d{2}-\d{8}-\d))?'
    
    # Buscar todas las coincidencias
    coincidencias = re.finditer(patron, contenido, re.DOTALL | re.IGNORECASE)
    
    # Lista para almacenar los datos de los socios
    datos_socios = []
    
    for match in coincidencias:
        nombre = match.group(1).strip()
        dni = match.group(2).strip() if match.group(2) else ''
        cuit = match.group(3).strip() if match.group(3) else ''
        
        # Formatear DNI
        if dni:
            dni = dni.replace('.', '')  # Eliminar puntos
            dni = f"{int(dni):08d}"  # Asegurar que tenga 8 dígitos
        
        datos_socio = f"{nombre} DNI {dni}"
        if cuit:
            datos_socio += f" CUIT/CUIL {cuit}"
        datos_socios.append(datos_socio)
    
    return '; '.join(datos_socios)
def extraer_contenido_y_fecha(url):
    try:
        respuesta = requests.get(url)
        respuesta.raise_for_status()
        soup = BeautifulSoup(respuesta.text, 'html.parser')
        
        contenido_div = soup.find('div', id='cuerpoDetalleAviso')
        if contenido_div:
            contenido = ' '.join(line.strip() for line in contenido_div.stripped_strings)
        else:
            contenido = "Contenido no encontrado"
        
        fecha_p = soup.find('p', class_='text-muted')
        fecha = fecha_p.text.strip() if fecha_p else "Fecha no encontrada"
        
        return contenido, fecha
    except Exception as e:
        return f"Error al extraer contenido: {e}", "Fecha no encontrada"

def extraer_avisos_de_seccion(url_base):
    avisos = []
    subcategorias_deseadas = [
        "SOCIEDADES ANONIMAS - CONSTITUCION SA",
        "SOC. DE RESPONSABILIDAD LIMITADA - CONTRATO SRL",
        "SOCIEDADES POR ACCION SIMPLIFICADA - CONSTITUCION SAS"
    ]
    try:
        respuesta = requests.get(url_base)
        respuesta.raise_for_status()
        soup = BeautifulSoup(respuesta.text, 'html.parser')
        
        subcategoria_actual = ""
        extrayendo = False
        
        for elemento in soup.find_all(['h5', 'div']):
            if elemento.name == 'h5' and 'seccion-rubro' in elemento.get('class', []):
                subcategoria_actual = elemento.text.strip()
                extrayendo = subcategoria_actual in subcategorias_deseadas
            elif extrayendo and elemento.name == 'div' and 'linea-aviso' in elemento.get('class', []):
                titulo = elemento.find('p', class_='item').text.strip()
                link = elemento.find_parent('a')['href']
                url_completa = f"https://www.boletinoficial.gob.ar{link}"
                
                contenido, fecha = extraer_contenido_y_fecha(url_completa)
                datos_socios = extraer_datos_socios(contenido)
                
                avisos.append([subcategoria_actual, titulo, contenido, fecha, url_completa, datos_socios])
        
    except Exception as e:
        print(f"Error al extraer avisos: {e}")
    
    return avisos

url_base = "https://www.boletinoficial.gob.ar/seccion/segunda"
avisos_extraidos = extraer_avisos_de_seccion(url_base)

print(f"\nTotal de avisos extraídos: {len(avisos_extraidos)}")

nombre_archivo = 'avisos_extraidos.csv'

with open(nombre_archivo, 'w', newline='', encoding='utf-8-sig') as archivo_csv:
    escritor_csv = csv.writer(archivo_csv, quoting=csv.QUOTE_ALL, delimiter=';')
    
    escritor_csv.writerow(['SUBCATEGORIA', 'TITULO', 'CONTENIDO', 'FECHA', 'LINK', 'DATOS/SOCIOS'])
    for aviso in avisos_extraidos:
        escritor_csv.writerow(aviso)

print(f"Los datos han sido guardados en {os.path.abspath(nombre_archivo)}")
