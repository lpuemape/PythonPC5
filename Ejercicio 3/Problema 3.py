import pandas as pd
import requests
from datetime import datetime

# Función de limpieza de nombres de columna
def limpieza_columnas(df):
    df.columns = df.columns.str.lower().str.replace(' ', '_').str.replace('ñ', 'n')
    for col in df.columns:
        if col in ['id', 'tipomoneda']:
            df.drop(col, axis=1, inplace=True)

# Función para eliminar comas en "DISPOSITIVO LEGAL"
def eliminar_comas(df):
    df['dispositivo_legal'] = df['dispositivo_legal'].str.replace(',', '')

# Función para dolarizar montos
def dolarizar_montos(df, tipo_cambio):
    df['monto_inversion_soles'] = df['monto_inversion']
    df['monto_transferencia_soles'] = df['monto_transferencia']

    df['monto_inversion_dolares'] = df['monto_inversion_soles'] / tipo_cambio
    df['monto_transferencia_dolares'] = df['monto_transferencia_soles'] / tipo_cambio

# Función para cambiar estado y puntuar
def cambiar_estado_puntuar(df):
    estado_map = {
        'En Elaboración': 'Actos Previos',
        'Asignado': 'Actos Previos',
        'Evaluación': 'Actos Previos',
        'Otorgamiento de Adenda': 'Actos Previos',
        'Otorgamiento de Conformidad': 'Concluido',
        'Ejecución de Obra': 'Ejecución',
        'Liquidación de Obra': 'Concluido',
        'Resuelto': 'Resuelto',
        'Anulado': 'Resuelto'
    }

    df['estado'] = df['estado'].map(estado_map)

    puntaje_map = {
        'Actos Previos': 1,
        'Resuelto': 0,
        'Ejecución': 2,
        'Concluido': 3
    }

    df['puntaje_estado'] = df['estado'].map(puntaje_map)

# Función para procesar datos
def procesar_datos(df):
    # Limpiar nombres de columna
    limpieza_columnas(df)

    # Eliminar comas en "DISPOSITIVO LEGAL"
    eliminar_comas(df)

    # Dolarizar montos
    tipo_cambio = obtener_tipo_cambio()
    dolarizar_montos(df, tipo_cambio)

    # Cambiar estado y puntuar
    cambiar_estado_puntuar(df)

# Función para obtener tipo de cambio actual
def obtener_tipo_cambio():
    # Simular consulta a API SUNAT
    tipo_cambio = 3.85

    return tipo_cambio

# Función para almacenar tabla de ubigeos en base de datos
def almacenar_ubigeos_bd(df):
    # Conectar a base de datos (reemplazar con su conexión real)
    conn = None

    # Crear o actualizar tabla de ubigeos
    df.drop_duplicates(['ubigeo', 'region', 'provincia', 'distrito'], inplace=True)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS ubigeos (ubigeo VARCHAR(6) PRIMARY KEY, region VARCHAR(255), provincia VARCHAR(255), distrito VARCHAR(255))')
    cursor.executemany('INSERT OR REPLACE INTO ubigeos VALUES (%s, %s, %s, %s)', df[['ubigeo', 'region', 'provincia', 'distrito']].values)
    conn.commit()
    cursor.close()

    # Cerrar conexión a base de datos
    conn.close()

# Función para generar reporte de top 5 costo inversión por región
def generar_reporte_top_inversion(df):
    for region in df['region'].unique():
        df_region = df[df['region'] == region]
        df_top_inversion = df_region[df_region['estado'].isin([1, 2, 3])].nlargest(5, 'monto_inversion_soles')

        if not df_top_inversion.empty:
            # Generar archivo Excel
            nombre_archivo = f'Top_inversion_{region}.xlsx'
            df_top_inversion.to_excel(nombre_archivo)

# Función para enviar correo electrónico
def enviar_correo(asunto, mensaje, adjuntos=[]):
