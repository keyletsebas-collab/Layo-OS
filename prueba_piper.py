import os
import requests
from piper.voice import PiperVoice
import sounddevice as sd
import soundfile as sf

# Nombres de los archivos físicos del cerebro de voz
modelo_onnx = "es_ES-sharvard-medium.onnx"
modelo_json = "es_ES-sharvard-medium.onnx.json"

def descargar_archivos():
    """Descarga el modelo de voz la primera vez que se ejecuta"""
    url_base = "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/sharvard/medium/"
    
    if not os.path.exists(modelo_onnx):
        print("[Descargando cerebro vocal (Aprox 60MB)... Depende de su internet]")
        r = requests.get(url_base + modelo_onnx, allow_redirects=True)
        open(modelo_onnx, 'wb').write(r.content)
        
    if not os.path.exists(modelo_json):
        print("[Descargando configuración neuronal...]")
        r = requests.get(url_base + modelo_json, allow_redirects=True)
        open(modelo_json, 'wb').write(r.content)

print("[Inicializando Protocolo Piper...]")
descargar_archivos()

print("[Cargando modelo a la memoria RAM...]")
# Cargamos la voz en la memoria para latencia cero
voz = PiperVoice.load(modelo_onnx)

def hablar_piper(texto):
    print(f"\nLayono: {texto}")
    
    # Piper escribe el audio super rápido en un archivo temporal
    archivo_temp = "temp.wav"
    import wave
    with wave.open(archivo_temp, "wb") as f:
        voz.synthesize(texto, f)
    
    # Lo leemos y lo reproducimos al instante
    data, fs = sf.read(archivo_temp)
    sd.play(data, fs)
    sd.wait()
    
    # Limpieza del archivo
    try:
        os.remove(archivo_temp)
    except:
        pass

# Prueba de fuego táctica
hablar_piper("Señor. Motores de voz Piper en línea. Latencia minimizada.")
hablar_piper("La integración ha sido un éxito. Quedo a la espera de sus comandos.")