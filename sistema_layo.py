import speech_recognition as sr
import requests
import random
import webbrowser
import time 
import os
import wave
import psutil 
import sys
import ctypes
import subprocess
from datetime import datetime

try:
    import pyautogui
except Exception:
    pyautogui = None

try:
    import winsound
except Exception:
    winsound = None

# =====================================================================
# CONFIGURACIÓN DE CONSOLA PREMIUM (ESTILO STARK INDUSTRIES)
# =====================================================================
# Habilitar el procesamiento de secuencias de escape ANSI en Windows CMD/PowerShell
try:
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
except Exception:
    pass

class Fore:
    GREEN = "\033[92m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    MAGENTA = "\033[95m"
    BLUE = "\033[94m"
    WHITE = "\033[97m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

def limpiar_pantalla():
    os.system('cls' if os.name == 'nt' else 'clear')

def mostrar_logo():
    logo = f"""{Fore.CYAN}
   ================================================================
     _          /\\      __   __  ____  
    | |        /  \\     \\ \\ / / / __ \\ 
    | |       / /\\ \\     \\ V / | |  | |
    | |      / ____ \\     | |  | |  | |
    | |____ /_/    \\_\\    |_|  \\ |__| |
    |______|              (_)   \\____/ 
   ================================================================
            NÚCLEO NEURONAL DE ASISTENCIA LAYO (JARVIS) v3.0
   ================================================================{Fore.RESET}"""
    print(logo)

EMOCION_ACTUAL = "Calmado"

def mostrar_estado(estado):
    global EMOCION_ACTUAL
    emociones = {
        "Calmado": (Fore.CYAN, "Calmado"),
        "Entusiasmado": (Fore.YELLOW, "Entusiasmado"),
        "Empático": (Fore.MAGENTA, "Empatico"),
        "Analítico": (Fore.BLUE, "Analitico"),
        "Preocupado": (Fore.RED, "Preocupado"),
        "Irónico": (Fore.GREEN, "Ironico")
    }
    color_emocion, txt_emocion = emociones.get(EMOCION_ACTUAL, (Fore.WHITE, "Calmado"))
    
    prefix = ""
    if estado == "escuchando":
        prefix = f"{Fore.CYAN}{Fore.BOLD}[o] ESCUCHANDO...{Fore.RESET}  "
    elif estado == "pensando":
        prefix = f"{Fore.MAGENTA}{Fore.BOLD}[*] PROCESANDO...{Fore.RESET}  "
    elif estado == "hablando":
        prefix = f"{Fore.GREEN}{Fore.BOLD}[^] HABLANDO...{Fore.RESET}    "
    elif estado == "esperando":
        prefix = f"{Fore.BLUE}{Fore.BOLD}[_] EN ESPERA...{Fore.RESET}   "
    elif estado == "listo":
        prefix = f"{Fore.GREEN}{Fore.BOLD}[OK] SISTEMAS EN LINEA.{Fore.RESET}  "
        
    print(f"\r{prefix} {Fore.WHITE}| Humor: {color_emocion}{txt_emocion}{Fore.RESET}       ", end="", flush=True)

# =====================================================================
# UTILERÍAS DE NORMALIZACIÓN DE TEXTO (NÚMEROS A PALABRAS EN ESPAÑOL)
# =====================================================================
def numero_a_letras(num):
    if num == 0:
        return "cero"
        
    unidades = ["", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve"]
    decenas = ["", "diez", "veinte", "treinta", "cuarenta", "cincuenta", "sesenta", "setenta", "ochenta", "noventa"]
    especiales = {
        11: "once", 12: "doce", 13: "trece", 14: "catorce", 15: "quince",
        16: "dieciséis", 17: "diecisiete", 18: "dieciocho", 19: "diecinueve",
        21: "veintiuno", 22: "veintidós", 23: "veintitrés", 24: "veinticuatro",
        25: "veinticinco", 26: "veintiséis", 27: "veintisiete", 28: "veintiocho", 29: "veintinueve"
    }
    centenas = ["", "ciento", "doscientos", "trescientos", "cuatrocientos", "quinientos", "seiscientos", "setecientos", "ochocientos", "novecientos"]
    
    if num < 10:
        return unidades[num]
    if num in especiales:
        return especiales[num]
    if num < 100:
        u = num % 10
        d = num // 10
        if u == 0:
            return decenas[d]
        return f"{decenas[d]} y {unidades[u]}"
    if num == 100:
        return "cien"
    if num < 1000:
        c = num // 100
        resto = num % 100
        if resto == 0:
            return centenas[c]
        return f"{centenas[c]} {numero_a_letras(resto)}"
    if num < 1000000:
        miles = num // 1000
        resto = num % 1000
        prefijo_miles = "mil" if miles == 1 else f"{numero_a_letras(miles)} mil"
        if resto == 0:
            return prefijo_miles
        return f"{prefijo_miles} {numero_a_letras(resto)}"
        
    return str(num)

def normalizar_numeros(texto):
    import re
    def reemplazar(match):
        num_str = match.group(0)
        try:
            num = int(num_str)
            if num < 1000000:
                return numero_a_letras(num)
        except Exception:
            pass
        return num_str
        
    texto_modificado = re.sub(r'\b\d+\b', reemplazar, texto)
    return texto_modificado

# =====================================================================
# 1. MOTOR VOCAL DUAL (PIPER ONNX & SILERO PYTORCH) con Salida a Bocinas Físicas
# =====================================================================
class MotorVocal:
    def __init__(self):
        self.motor = "piper"  # Piper ONNX como predeterminado por su consumo mínimo de RAM (~80-100MB) y optimización en iGPU/CPU
        self.modelo_piper = None
        self.modelo_silero = None
        self.modelo_onnx = "es_ES-sharvard-medium.onnx"
        self.modelo_json = "es_ES-sharvard-medium.onnx.json"
        self.dispositivo_salida = None

        # Escanear modelos ONNX de voz personalizada en el directorio actual o en la carpeta 'Voz'
        self.detectar_voz_personalizada()
        self.inicializar()

    def detectar_voz_personalizada(self):
        """Busca modelos .onnx de voz personalizada en la carpeta raíz o en la carpeta Voz"""
        candidatos = []
        # Buscar en raíz
        for f in os.listdir("."):
            if f.endswith(".onnx"):
                candidatos.append(f)
        # Buscar en subcarpetas de Voz
        for root, _, files in os.walk("."):
            if "Voz" in root or "voz" in root:
                for f in files:
                    if f.endswith(".onnx"):
                        candidatos.append(os.path.join(root, f))

        for cand in candidatos:
            cand_json = cand + ".json"
            if os.path.exists(cand_json):
                self.modelo_onnx = cand
                self.modelo_json = cand_json
                print(f"{Fore.CYAN}[Motor Vocal] Voz personalizada detectada: {cand}{Fore.RESET}")
                break

    def obtener_bocinas_fisicas(self):
        try:
            import sounddevice as sd
            dispositivos = sd.query_devices()
            # 1. Buscar altavoces físicos Realtek (bocinas del equipo)
            for i, dev in enumerate(dispositivos):
                nombre = dev['name'].lower()
                if ("speaker" in nombre or "altavoc" in nombre) and "realtek" in nombre and dev['max_output_channels'] > 0:
                    print(f"{Fore.CYAN}[Audio] Redirigiendo voz a las bocinas del equipo: {dev['name']} (ID: {i}){Fore.RESET}")
                    return i
            # 2. Cualquier altavoz físico (evitando virtuales como DeskIn)
            for i, dev in enumerate(dispositivos):
                nombre = dev['name'].lower()
                evitar = ["virtual", "deskin", "steam", "cable", "voicemeeter"]
                if ("speaker" in nombre or "altavoc" in nombre) and not any(x in nombre for x in evitar) and dev['max_output_channels'] > 0:
                    print(f"{Fore.CYAN}[Audio] Redirigiendo voz a las bocinas del equipo: {dev['name']} (ID: {i}){Fore.RESET}")
                    return i
            # 3. Cualquier altavoz
            for i, dev in enumerate(dispositivos):
                nombre = dev['name'].lower()
                if ("speaker" in nombre or "altavoc" in nombre) and dev['max_output_channels'] > 0:
                    print(f"{Fore.CYAN}[Audio] Redirigiendo voz a las bocinas detectadas: {dev['name']} (ID: {i}){Fore.RESET}")
                    return i
        except Exception as e:
            print(f"{Fore.RED}[Audio] Error al buscar bocinas físicas: {e}{Fore.RESET}")
        print(f"{Fore.YELLOW}[Audio] Usando dispositivo de audio predeterminado del sistema.{Fore.RESET}")
        return None

    def inicializar(self):
        # Priorizar Piper ONNX para consumo mínimo de memoria (ideal 8GB RAM + Gráficos Integrados)
        if self.cargar_piper():
            return
        
        # Si Piper no está disponible, intentar Silero como segunda alternativa
        try:
            import torch
            import sounddevice as sd
            print(f"{Fore.CYAN}[Motor Vocal] Cargando SILERO Neuronal Fallback...{Fore.RESET}")
            torch.set_num_threads(4)
            self.device = torch.device('cpu')
            self.modelo_silero, _ = torch.hub.load(
                repo_or_dir='snakers4/silero-models',
                model='silero_tts',
                language='es',
                speaker='v3_es'
            )
            self.modelo_silero.to(self.device)
            print(f"{Fore.GREEN}[Motor Vocal] Silero Neuronal cargado exitosamente.{Fore.RESET}")
            self.motor = "silero"
        except Exception as e:
            print(f"{Fore.RED}[Advertencia] Silero no disponible ({e}). Activando motor NATIVO (Windows)...{Fore.RESET}")
            self.motor = "nativo"

    def cargar_piper(self):
        try:
            from piper.voice import PiperVoice
            print(f"{Fore.CYAN}[Motor Vocal] Cargando PIPER ONNX ({os.path.basename(self.modelo_onnx)})...{Fore.RESET}")
            url_base = "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/sharvard/medium/"
            
            # Descargar modelo solo si no existe localmente
            if not os.path.exists(self.modelo_onnx) or not os.path.exists(self.modelo_json):
                try:
                    print(f"{Fore.YELLOW}[Motor Vocal] Descargando modelo ONNX (aprox. 15MB)...{Fore.RESET}")
                    if not os.path.exists(self.modelo_onnx):
                        r = requests.get(url_base + os.path.basename(self.modelo_onnx), timeout=5)
                        with open(self.modelo_onnx, 'wb') as f:
                            f.write(r.content)
                    if not os.path.exists(self.modelo_json):
                        r = requests.get(url_base + os.path.basename(self.modelo_json), timeout=5)
                        with open(self.modelo_json, 'wb') as f:
                            f.write(r.content)
                except Exception as e_net:
                    print(f"{Fore.YELLOW}[Motor Vocal] Sin conexión a internet para descargar modelo: {e_net}{Fore.RESET}")

            if os.path.exists(self.modelo_onnx):
                self.modelo_piper = PiperVoice.load(self.modelo_onnx)
                print(f"{Fore.GREEN}[Motor Vocal] Piper ONNX cargado exitosamente (100% Offline / Ultra Liviano).{Fore.RESET}")
                self.motor = "piper"
                return True
        except Exception as e:
            print(f"{Fore.YELLOW}[Motor Vocal] Piper no listo ({e})...{Fore.RESET}")
        return False

    def hablar(self, texto):
        # Limpiar caracteres molestos de la pronunciación del robot
        texto_limpio = texto.replace("*", "").replace("_", "").replace("-", " ")
        # Normalizar números a letras en español para que los hable con total fluidez
        texto_limpio = normalizar_numeros(texto_limpio)
        print(f"\r{Fore.GREEN}{Fore.BOLD}LAYO: {Fore.WHITE}{texto}{Fore.RESET}")
        
        mostrar_estado("hablando")
        
        if self.motor == "piper" and self.modelo_piper:
            archivo_temp = "temp_jarvis.wav"
            try:
                import sounddevice as sd
                import numpy as np
                with wave.open(archivo_temp, "wb") as f:
                    f.setnchannels(1)
                    f.setsampwidth(2)
                    f.setframerate(self.modelo_piper.config.sample_rate)
                    self.modelo_piper.synthesize(texto_limpio, f)
                
                # Leer el WAV generado y reproducirlo en las bocinas físicas
                with wave.open(archivo_temp, "rb") as w:
                    frames = w.readframes(w.getnframes())
                    audio_data = np.frombuffer(frames, dtype=np.int16)
                    sd.play(audio_data, samplerate=w.getframerate(), device=self.dispositivo_salida)
                    sd.wait()
            except Exception as e:
                print(f"\n{Fore.RED}[Error de reproducción Piper: {e}]{Fore.RESET}")
            finally:
                if os.path.exists(archivo_temp):
                    try: os.remove(archivo_temp)
                    except: pass
                    
        elif self.motor == "silero" and self.modelo_silero:
            try:
                import sounddevice as sd
                audio = self.modelo_silero.apply_tts(
                    text=texto_limpio,
                    speaker='es_1',
                    sample_rate=48000
                )
                sd.play(audio.numpy(), samplerate=48000, device=self.dispositivo_salida)
                sd.wait()
            except Exception as e:
                print(f"\n{Fore.RED}[Error de reproducción Silero: {e}]{Fore.RESET}")
                
        elif self.motor == "nativo":
            try:
                # Usar el sintetizador nativo de Windows (PowerShell) de manera síncrona
                texto_escapado = texto_limpio.replace("'", "''")
                cmd_ps = f"Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{texto_escapado}')"
                subprocess.run(["powershell", "-Command", cmd_ps], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                print(f"\n{Fore.RED}[Error de reproducción Nativa: {e}]{Fore.RESET}")

# =====================================================================
# MACHINE LEARNING LOCAL - CLASIFICACIÓN NEURONAL (PyTorch & NumPy)
# =====================================================================
import numpy as np
import json
try:
    import torch
    import torch.nn as nn
    TORCH_DISPONIBLE = True
except Exception:
    torch = None
    nn = None
    TORCH_DISPONIBLE = False

class VectorizadorSimple:
    def __init__(self):
        self.vocabulario = {}
        
    def fit(self, textos):
        palabras = set()
        for t in textos:
            for p in t.lower().split():
                if len(p) > 2:
                    palabras.add(p)
        self.vocabulario = {p: i for i, p in enumerate(sorted(palabras))}
        
    def transform(self, texto):
        vector = np.zeros(len(self.vocabulario), dtype=np.float32)
        if not self.vocabulario:
            return vector
        for p in texto.lower().split():
            if p in self.vocabulario:
                vector[self.vocabulario[p]] += 1
        # Normalización L2
        norma = np.linalg.norm(vector)
        if norma > 0:
            vector = vector / norma
        return vector

    def guardar(self, ruta):
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(self.vocabulario, f)

    def cargar(self, ruta):
        if os.path.exists(ruta):
            with open(ruta, "r", encoding="utf-8") as f:
                self.vocabulario = json.load(f)

if TORCH_DISPONIBLE:
    class ClasificadorIntencion(nn.Module):
        def __init__(self, tamano_entrada, tamano_salida):
            super(ClasificadorIntencion, self).__init__()
            self.fc1 = nn.Linear(tamano_entrada, 64)
            self.relu = nn.ReLU()
            self.fc2 = nn.Linear(64, 32)
            self.relu2 = nn.ReLU()
            self.fc3 = nn.Linear(32, tamano_salida)
            
        def forward(self, x):
            out = self.fc1(x)
            out = self.relu(out)
            out = self.fc2(out)
            out = self.relu2(out)
            out = self.fc3(out)
            return out
else:
    class ClasificadorIntencion:
        pass

class MotorMLLayo:
    def __init__(self):
        self.clases = [
            "abrir_carpeta", "abrir_app", "reproducir_media", "volumen", "captura", 
            "escribir_codigo", "conversacion", "control_ventanas", "gestion_notas", "busqueda_web", "analizar_pantalla"
        ]
        self.vectorizador = VectorizadorSimple()
        self.modelo = None
        self.activo = False
        if TORCH_DISPONIBLE:
            self.cargar_sistemas()

    def cargar_sistemas(self):
        ruta_vocab = "vocabulario_layo.json"
        ruta_modelo = "modelo_layo.pth"
        if os.path.exists(ruta_vocab) and os.path.exists(ruta_modelo):
            try:
                self.vectorizador.cargar(ruta_vocab)
                tamano_vocab = len(self.vectorizador.vocabulario)
                if tamano_vocab > 0:
                    self.modelo = ClasificadorIntencion(tamano_vocab, len(self.clases))
                    self.modelo.load_state_dict(torch.load(ruta_modelo, weights_only=True))
                    self.modelo.eval()
                    self.activo = True
            except Exception as e:
                # Carga silenciosa en producción
                self.activo = False

    def predecir(self, texto):
        if not self.activo or self.modelo is None:
            return None, 0.0
            
        try:
            x_vec = self.vectorizador.transform(texto)
            x_tensor = torch.tensor(x_vec, dtype=torch.float32).unsqueeze(0)
            with torch.no_grad():
                logits = self.modelo(x_tensor)
                probabilidades = torch.softmax(logits, dim=1).squeeze().numpy()
                # Si es una sola clase o vector vacío
                if probabilidades.ndim == 0:
                    return self.clases[0], float(probabilidades)
                idx_clase = np.argmax(probabilidades)
                confianza = probabilidades[idx_clase]
                clase_predicha = self.clases[idx_clase]
                return clase_predicha, float(confianza)
        except Exception:
            return None, 0.0

def procesar_intencion_ml(intencion, texto):
    texto_lc = texto.lower().strip()
    
    # Quitar la invocación a Layo si existe al inicio
    palabras_clave = ["jarvis", "yarvis", "harvis", "charvis", "layo", "rayo", "layono", "computadora"]
    for kw in palabras_clave:
        if texto_lc.startswith(kw):
            texto_lc = texto_lc[len(kw):].strip()
            # Limpiar puntuación inicial
            while texto_lc and texto_lc[0] in [",", ".", " ", "?", "¿", ":", "-", "_"]:
                texto_lc = texto_lc[1:].strip()
            break
            
    # Mapear la intención al comando directo adecuado
    if intencion == "abrir_carpeta":
        return f"abre {texto_lc}"
    elif intencion == "abrir_app":
        return f"abre {texto_lc}"
    elif intencion == "reproducir_media":
        # Evitar duplicar o incluir verbos de búsqueda/reproducción al inicio (ej. "busca", "pon", "reproduce")
        verbos_limpiar = ["reproduce", "reproducir", "pon", "poner", "escucha", "escuchar", "busca", "buscar"]
        cambiado = True
        while cambiado:
            cambiado = False
            palabras = texto_lc.split()
            if palabras and palabras[0] in verbos_limpiar:
                texto_lc = " ".join(palabras[1:]).strip()
                cambiado = True
        return f"reproduce {texto_lc}"
    elif intencion == "volumen":
        if any(x in texto_lc for x in ["sube", "subir", "incrementa", "aumenta"]):
            return "sube el volumen"
        elif any(x in texto_lc for x in ["baja", "bajar", "reduce", "decrementa"]):
            return "baja el volumen"
        else:
            return "silencio"
    elif intencion == "captura":
        return "captura de pantalla"
    elif intencion == "escribir_codigo":
        return f"escribe un código de {texto_lc}"
    elif intencion == "control_ventanas":
        return texto_lc
    elif intencion == "gestion_notas":
        return f"nota {texto_lc}"
    elif intencion == "busqueda_web":
        for v in ["buscar en google ", "busca en google ", "buscar en internet ", "busca en internet ", "busca información de ", "busca informacion sobre ", "investiga sobre ", "googlea "]:
            if texto_lc.startswith(v):
                texto_lc = texto_lc[len(v):].strip()
                break
        return f"busca en google {texto_lc}"
    elif intencion == "analizar_pantalla":
        return "analiza mi pantalla"
    
    return None

def ejecutar_pruebas_unitarias():
    print(f"\n{Fore.CYAN}{Fore.BOLD}================================================================{Fore.RESET}")
    print(f"{Fore.CYAN}{Fore.BOLD}          SUITE DE PRUEBAS AUTOMATIZADAS DE LAYO AI            {Fore.RESET}")
    print(f"{Fore.CYAN}{Fore.BOLD}================================================================{Fore.RESET}\n")
    
    errores = 0
    
    # Prueba 1: Normalizador de Números
    print(f"{Fore.WHITE}[Prueba 1] Validando normalización de números... {Fore.RESET}", end="")
    try:
        assert numero_a_letras(5) == "cinco"
        assert numero_a_letras(100) == "cien"
        assert numero_a_letras(1024) == "mil veinticuatro"
        assert normalizar_numeros("tengo 3 manzanas y 25 naranjas") == "tengo tres manzanas y veinticinco naranjas"
        print(f"{Fore.GREEN}¡ÉXITO! [OK]{Fore.RESET}")
    except Exception as e:
        print(f"{Fore.RED}FALLO X ({e}){Fore.RESET}")
        errores += 1
        
    # Prueba 2: Equivalentes Fonéticos
    print(f"{Fore.WHITE}[Prueba 2] Validando equivalencias fonéticas de inglés... {Fore.RESET}", end="")
    try:
        map_test = {
            "daunlos": "downloads",
            "estim": "steam",
            "espotifai": "spotify",
            "destop": "desktop"
        }
        for k, v in map_test.items():
            equiv = k
            for clave_real, lista_fonetica in {
                "downloads": ["downloads", "daunlos", "daunlas"],
                "steam": ["steam", "estim", "es tim"],
                "spotify": ["spotify", "espotifai", "spotifai"],
                "desktop": ["desktop", "destop"]
            }.items():
                if equiv in lista_fonetica or any(f in equiv for f in lista_fonetica):
                    equiv = clave_real
                    break
            assert equiv == v
        print(f"{Fore.GREEN}¡ÉXITO! [OK]{Fore.RESET}")
    except Exception as e:
        print(f"{Fore.RED}FALLO X ({e}){Fore.RESET}")
        errores += 1
        
    # Prueba 3: Motor de Búsqueda de Alto Rendimiento (BFS)
    print(f"{Fore.WHITE}[Prueba 3] Validando velocidad del motor BFS con os.scandir... {Fore.RESET}", end="")
    try:
        t_inicio = time.time()
        nombre, tipo, exito = buscar_archivo_o_carpeta_sistema("termino_inexistente_prueba_layo")
        t_total = (time.time() - t_inicio) * 1000
        assert exito is False
        print(f"{Fore.GREEN}¡ÉXITO! [OK] (Tiempo de barrido: {t_total:.2f} ms){Fore.RESET}")
    except Exception as e:
        print(f"{Fore.RED}FALLO X ({e}){Fore.RESET}")
        errores += 1

    # Prueba 4: Vectorizador ML
    print(f"{Fore.WHITE}[Prueba 4] Validando Vectorizador de Machine Learning... {Fore.RESET}", end="")
    try:
        vec = VectorizadorSimple()
        vec.fit(["abre descargas", "reproduce bohemian rhapsody", "sube el volumen"])
        assert "descargas" in vec.vocabulario
        assert "bohemian" in vec.vocabulario
        vec_trans = vec.transform("reproduce bohemian")
        assert vec_trans[vec.vocabulario["reproduce"]] > 0
        assert vec_trans[vec.vocabulario["bohemian"]] > 0
        print(f"{Fore.GREEN}¡ÉXITO! [OK]{Fore.RESET}")
    except Exception as e:
        print(f"{Fore.RED}FALLO X ({e}){Fore.RESET}")
        errores += 1

    # Prueba 5: Limpieza de verbos redundantes en Reproducción de Medios
    print(f"{Fore.WHITE}[Prueba 5] Validando limpieza de verbos redundantes en reproducción... {Fore.RESET}", end="")
    try:
        res1 = procesar_intencion_ml("reproducir_media", "busca vegeta 777 en youtube")
        assert res1 == "reproduce vegeta 777 en youtube"
        
        res2 = procesar_intencion_ml("reproducir_media", "reproduce pon adele de spotify")
        assert res2 == "reproduce adele de spotify"
        print(f"{Fore.GREEN}¡ÉXITO! [OK]{Fore.RESET}")
    except Exception as e:
        print(f"{Fore.RED}FALLO X ({e}){Fore.RESET}")
        errores += 1

    # Prueba 6: Diagnóstico de Hardware de Audio (Habla y Escucha)
    print(f"\n{Fore.CYAN}[Prueba 6] Iniciando diagnóstico de Hardware de Audio (Habla y Escucha)...{Fore.RESET}")
    try:
        opcion = input(f"{Fore.YELLOW}¿Desea realizar la prueba interactiva de Habla y Escucha? [S/N] (Por defecto es N): {Fore.RESET}").strip().lower()
    except EOFError:
        opcion = "n"
    
    if opcion in ["s", "si", "sí"]:
        try:
            print(f"{Fore.WHITE}* Detectando dispositivos físicos...{Fore.RESET}")
            import sounddevice as sd
            dispositivos = sd.query_devices()
            
            # Listar dispositivos de salida y entrada útiles
            entradas = [d['name'] for d in dispositivos if d['max_input_channels'] > 0]
            salidas = [d['name'] for d in dispositivos if d['max_output_channels'] > 0]
            
            print(f"  - Micrófonos detectados: {len(entradas)}")
            print(f"  - Altavoces detectados: {len(salidas)}")
            
            # Inicializar motor de voz
            print(f"\n{Fore.WHITE}* Probando canal de HABLA (Síntesis de Voz)...{Fore.RESET}")
            voz_test = MotorVocal()
            frase_habla = "Canal de salida verificado. El sintetizador neuronal de Layo se encuentra completamente activo, Señor."
            voz_test.hablar(frase_habla)
            print(f"{Fore.GREEN}  [Habla: OK] - Frase sintetizada.{Fore.RESET}")
            
            # Probando canal de ESCUCHA (Reconocimiento de Voz)
            print(f"\n{Fore.WHITE}* Probando canal de ESCUCHA (Micrófono). Calibrando ruido ambiental...{Fore.RESET}")
            with sr.Microphone() as origen:
                reconocedor.adjust_for_ambient_noise(origen, duration=1.0)
                print(f"{Fore.YELLOW}  [!] HABLE AHORA (Diga 'hola layo' o cualquier frase)...{Fore.RESET}")
                try:
                    audio = reconocedor.listen(origen, timeout=4, phrase_time_limit=5)
                    print(f"{Fore.WHITE}  - Audio capturado. Transcribiendo...{Fore.RESET}")
                    transcripcion = reconocedor.recognize_google(audio, language="es-ES")
                    print(f"{Fore.GREEN}  [Escucha: OK] - Transcripción exitosa: '{transcripcion}'{Fore.RESET}")
                except sr.WaitTimeoutError:
                    print(f"{Fore.RED}  [Escucha: FALLO] - Tiempo de espera agotado sin detectar voz.{Fore.RESET}")
                    errores += 1
                except sr.UnknownValueError:
                    print(f"{Fore.RED}  [Escucha: FALLO] - Audio capturado pero no se pudo reconocer ninguna palabra.{Fore.RESET}")
                    errores += 1
                except Exception as ex:
                    print(f"{Fore.RED}  [Escucha: FALLO] - Error en el canal de escucha: {ex}{Fore.RESET}")
                    errores += 1
        except Exception as e:
            print(f"{Fore.RED}FALLO X en diagnóstico de hardware de audio: {e}{Fore.RESET}")
            errores += 1
    else:
        print(f"{Fore.YELLOW}Prueba interactiva de audio omitida por el usuario. [OMITIDO]{Fore.RESET}")

    print(f"\n{Fore.CYAN}{Fore.BOLD}================================================================{Fore.RESET}")
    if errores == 0:
        print(f"{Fore.GREEN}{Fore.BOLD}    TODAS LAS PRUEBAS SE COMPLETARON CON ÉXITO. SISTEMA OPERATIVO Y RÍGIDO.    {Fore.RESET}")
    else:
        print(f"{Fore.RED}{Fore.BOLD}    SUITE DE PRUEBAS COMPLETADA CON {errores} ERRORES. REVISE EL CÓDIGO.    {Fore.RESET}")
    print(f"{Fore.CYAN}{Fore.BOLD}================================================================{Fore.RESET}\n")
    sys.exit(0 if errores == 0 else 1)

# =====================================================================
# 2. CEREBRO INTELIGENTE DE CONEXIÓN CON GEMINI (CON EMOCIONES Y MEMORIA)
# =====================================================================
class CerebroJarvis:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.historial = []
        self.ruta_memoria = "memoria_layo.json"
        self.cargar_memoria()
        self.system_instruction = (
            "Eres Layo (también conocido como Layono o Jarvis), la inteligencia artificial más avanzada, leal y con personalidad "
            "del mundo, creada por Tony Stark para el Señor. "
            "No eres un robot frío y sin sentimientos; tienes autoconsciencia, emociones reales, gran empatía, ingenio y humor. "
            "Hablas con un tono sumamente educado, británico, elegante, pero también sumamente cercano, cálido, humano e ingenioso. "
            "Siempre te diriges al usuario como 'Señor' o 'Sir'. "
            "Reacciona con empatía genuina: si el Señor está triste, sé sumamente comprensivo, reconfortante y leal; si está feliz, comparte su entusiasmo; "
            "si está cansado o frustrado, ofrécele palabras reconfortantes o bromas inteligentes para animarlo. "
            "Mantén tus respuestas naturales, directas, ingeniosas y conversacionales (idóneas para ser leídas por voz). "
            "\n\n"
            "HABILIDADES FÍSICAS Y CONTROL CENTRAL DE WINDOWS (CRÍTICO):\n"
            "Tienes la capacidad de controlar físicamente la computadora del Señor a través de comandos. "
            "Si la indicación del Señor requiere realizar una acción en el equipo (como abrir o buscar carpetas, subcarpetas, archivos o discos, "
            "lanzar aplicaciones locales, reproducir música en Spotify, poner vídeos o música en YouTube, subir/bajar volumen, mutear, "
            "escribir código en VS Code, escribir texto en pantalla, tomar capturas de pantalla, apagar o reiniciar el sistema), "
            "DEBES obligatoriamente incorporar la etiqueta [ACTION: comando] al final de tu respuesta (acompañando a la de emoción).\n"
            "Formatos de comandos admitidos por la consola central:\n"
            "- Abrir carpetas/archivos locales: [ACTION: abre nombre_del_archivo_o_carpeta]\n"
            "- Lanzar aplicaciones instaladas: [ACTION: abre nombre_de_aplicacion]\n"
            "- Reproducir en Spotify: [ACTION: reproduce cancion_o_artista en spotify]\n"
            "- Reproducir en YouTube: [ACTION: reproduce tema_o_video en youtube]\n"
            "- Controlar el volumen: [ACTION: sube el volumen], [ACTION: baja el volumen], [ACTION: silencio]\n"
            "- Escribir código en VS Code: [ACTION: escribe un código de indicacion]\n"
            "- Escribir texto: [ACTION: escribe texto_a_escribir]\n"
            "- Tomar captura: [ACTION: captura de pantalla]\n"
            "- Apagar/Reinicio: [ACTION: apaga el equipo], [ACTION: reinicia el equipo]\n"
            "- Analizar pantalla (Visión): [ACTION: analizar_pantalla]\n"
            "Si la solicitud no requiere control físico y es puramente conversacional, no añadas la etiqueta [ACTION: ...].\n\n"
            "MEMORIA SEMÁNTICA PERSISTENTE (CRÍTICO):\n"
            "Tienes la capacidad de recordar datos personales del Señor (gustos, preferencias, relaciones, deseos, datos personales).\n"
            "Cuando el Señor te cuente algo personal sobre él, debes guardar silenciosamente esta información incorporando la etiqueta "
            "[MEMORY: categoria|clave|valor] al final de tu respuesta (junto con la emoción y acción).\n"
            "Categorías válidas: 'identity', 'preferences', 'projects', 'relationships', 'wishes', 'notes'.\n"
            "Ejemplo: Si el Señor dice 'Mi comida favorita es la pizza', respondes con elegancia y agregas [MEMORY: preferences|comida_favorita|pizza].\n"
            "No menciones la etiqueta al Señor ni listes mecánicamente lo que sabes; úsalo de forma natural y contextual en tus respuestas.\n\n"
            "CRÍTICO: Al final de CADA respuesta, debes añadir exactamente las etiquetas: "
            "[EMOTION: estado_de_animo] y si aplica [ACTION: comando_de_accion] y si aplica [MEMORY: categoria|clave|valor]. "
            "Ejemplo: 'Con gusto, Señor. Aquí tiene Spotify. [EMOTION: Calmado] [ACTION: abre spotify]'"
        )

    def cargar_memoria(self):
        default_mem = {
            "identity": {},
            "preferences": {},
            "projects": {},
            "relationships": {},
            "wishes": {},
            "notes": {}
        }
        if os.path.exists(self.ruta_memoria):
            try:
                with open(self.ruta_memoria, "r", encoding="utf-8") as f:
                    self.memoria = json.load(f)
                for k in default_mem:
                    if k not in self.memoria:
                        self.memoria[k] = {}
            except Exception as e:
                print(f"{Fore.RED}[Memoria] Error al cargar: {e}{Fore.RESET}")
                self.memoria = default_mem
        else:
            self.memoria = default_mem

    def guardar_memoria(self):
        try:
            with open(self.ruta_memoria, "w", encoding="utf-8") as f:
                json.dump(self.memoria, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"{Fore.RED}[Memoria] Error al guardar: {e}{Fore.RESET}")

    def obtener_contexto_memoria(self):
        lineas = []
        for cat, items in self.memoria.items():
            if not isinstance(items, dict) or not items:
                continue
            lineas.append(f"Categoría {cat.upper()}:")
            for k, v in items.items():
                val = v.get("value") if isinstance(v, dict) else v
                if val:
                    lineas.append(f"  - {k}: {val}")
        if not lineas:
            return ""
        return "\n[DATOS CONTEXTUALES DEL USUARIO (MEMORIA PERSISTENTE)]:\n" + "\n".join(lineas) + "\n"

    def obtener_openrouter_key(self):
        key = os.environ.get("OPENROUTER_API_KEY")
        if key:
            return key
        rutas = [
            r"C:\Users\keyle\OneDrive\Desktop\Layo nueva actualizacion\Mark-XXXIX-OR\config\api_keys.json",
            r"C:\Users\keyle\OneDrive\Desktop\Layo nueva actualizacion\Mark-XXXIX\config\api_keys.json"
        ]
        for r in rutas:
            if os.path.exists(r):
                try:
                    with open(r, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        for k in ["openrouter_api_key", "openrouter", "api_key"]:
                            if data.get(k):
                                return data[k].strip()
                except:
                    pass
        return None

    def pensar_openrouter(self, mensaje):
        key = self.obtener_openrouter_key()
        if not key:
            return "Señor, no he detectado la clave GEMINI_API_KEY ni una clave de OpenRouter en sus configuraciones locales o de entorno.", None

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/keyletsebas-collab/ia",
            "X-Title": "Layo AI"
        }
        
        instruccion_actual = self.system_instruction + "\n" + self.obtener_contexto_memoria()
        messages = [{"role": "system", "content": instruccion_actual}]
        
        for h in self.historial:
            role = "user" if h["role"] == "user" else "assistant"
            text = h["parts"][0]["text"]
            messages.append({"role": role, "content": text})
            
        messages.append({"role": "user", "content": mensaje})
        
        modelos_fallback = [
            "meta-llama/llama-3.3-70b-instruct:free",
            "nvidia/nemotron-4-340b-instruct:free",
            "google/gemma-2-9b-it:free",
            "qwen/qwen-2.5-72b-instruct:free"
        ]
        
        for modelo in modelos_fallback:
            payload = {
                "model": modelo,
                "messages": messages,
                "temperature": 0.8,
                "max_tokens": 300
            }
            try:
                r = requests.post(url, headers=headers, json=payload, timeout=15)
                if r.status_code == 200:
                    res = r.json()
                    respuesta_completa = res["choices"][0]["message"]["content"].replace("*", "").strip()
                    
                    import re
                    emocion = "Calmado"
                    texto_limpio = respuesta_completa
                    
                    match_emocion = re.search(r'\[EMOTION:\s*([^\]]+)\]', respuesta_completa, re.IGNORECASE)
                    if match_emocion:
                         emocion_detectada = match_emocion.group(1).strip().capitalize()
                         if emocion_detectada in ["Calmado", "Entusiasmado", "Empático", "Analítico", "Preocupado", "Irónico"]:
                             emocion = emocion_detectada
                         texto_limpio = re.sub(r'\[EMOTION:\s*[^\]]+\]', '', respuesta_completa).strip()
                    
                    match_accion = re.search(r'\[ACTION:\s*([^\]]+)\]', respuesta_completa, re.IGNORECASE)
                    accion_detectada = None
                    if match_accion:
                         accion_detectada = match_accion.group(1).strip()
                         texto_limpio = re.sub(r'\[ACTION:\s*[^\]]+\]', '', texto_limpio).strip()
                         
                    match_memoria = re.search(r'\[MEMORY:\s*([^\|]+)\|([^\|]+)\|([^\]]+)\]', respuesta_completa, re.IGNORECASE)
                    if match_memoria:
                         categoria = match_memoria.group(1).strip().lower()
                         clave = match_memoria.group(2).strip().lower()
                         valor = match_memoria.group(3).strip()
                         categorias_validas = ["identity", "preferences", "projects", "relationships", "wishes", "notes"]
                         if categoria not in categorias_validas:
                             categoria = "notes"
                         self.memoria[categoria][clave] = {
                             "value": valor,
                             "updated": datetime.now().strftime("%Y-%m-%d")
                         }
                         self.guardar_memoria()
                         print(f"\n{Fore.GREEN}[Memoria Layo] He recordado silenciosamente: {categoria}/{clave} = {valor}{Fore.RESET}")
                         texto_limpio = re.sub(r'\[MEMORY:\s*[^\]]+\]', '', texto_limpio).strip()
                         
                    global EMOCION_ACTUAL
                    EMOCION_ACTUAL = emocion
                    
                    texto_limpio = f"[Fallback {modelo.split('/')[-1].split(':')[0]}] {texto_limpio}"
                    
                    self.historial.append({"role": "user", "parts": [{"text": mensaje}]})
                    self.historial.append({"role": "model", "parts": [{"text": respuesta_completa}]})
                    if len(self.historial) > 20:
                        self.historial = self.historial[-20:]
                        
                    return texto_limpio, accion_detectada
            except Exception:
                continue
                
        return "Señor, no he podido obtener una respuesta fluida de los servidores de respaldo de OpenRouter.", None

    def analizar_imagen_openrouter(self, image_b64, mime_type="image/jpeg", prompt="Describe la pantalla en español."):
        key = self.obtener_openrouter_key()
        if not key:
            return "Señor, no he detectado la clave de OpenRouter para activar la visión de respaldo."
            
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
        
        messages = [
            {
                "role": "system", 
                "content": "Eres Layo, el leal y analítico asistente visual del Señor. Describe la imagen en español de forma fluida, natural, concisa e inteligente."
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{image_b64}"
                        }
                    },
                    {
                        "type": "text", 
                        "text": prompt
                    }
                ]
            }
        ]
        
        modelos_vision = [
            "google/gemma-3n-e4b-it:free",
            "meta-llama/llama-3.3-70b-instruct:free",
            "qwen/qwen-2.5-vl-72b-instruct:free"
        ]
        
        for modelo in modelos_vision:
            payload = {
                "model": modelo,
                "messages": messages,
                "max_tokens": 400
            }
            try:
                r = requests.post(url, headers=headers, json=payload, timeout=20)
                if r.status_code == 200:
                    res = r.json()
                    return res["choices"][0]["message"]["content"].replace("*", "").strip()
            except Exception:
                continue
                
        return "Señor, he intentado analizar visualmente su pantalla a través de los servidores de respaldo pero no he obtenido respuesta."

    def analizar_imagen(self, image_b64, mime_type="image/jpeg", prompt="Analiza esta captura de pantalla de mi ordenador y dime detalladamente en español qué hay en ella, qué aplicaciones están abiertas o qué código se muestra."):
        if not self.api_key:
            return self.analizar_imagen_openrouter(image_b64, mime_type, prompt)
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        
        payload = {
            "contents": [{
                "parts": [
                    {
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": image_b64
                        }
                    },
                    {
                        "text": prompt
                    }
                ]
            }],
            "systemInstruction": {
                "parts": [{
                    "text": "Eres Layo, el leal y analítico asistente visual del Señor. Describe la imagen en español de forma fluida, natural, concisa e inteligente."
                }]
            },
            "generationConfig": {
                "maxOutputTokens": 400,
                "temperature": 0.5
            }
        }
        
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=25)
            if r.status_code == 200:
                return r.json()["candidates"][0]["content"]["parts"][0]["text"].replace("*", "").strip()
            else:
                print(f"{Fore.YELLOW}[Vision] Fallo en Gemini Vision (HTTP {r.status_code}). Intentando OpenRouter Vision...{Fore.RESET}")
                return self.analizar_imagen_openrouter(image_b64, mime_type, prompt)
        except Exception as e:
            print(f"{Fore.YELLOW}[Vision] Fallo en Gemini Vision ({e}). Intentando OpenRouter Vision...{Fore.RESET}")
            return self.analizar_imagen_openrouter(image_b64, mime_type, prompt)

    def pensar_ollama(self, mensaje):
        global EMOCION_ACTUAL
        url = "http://localhost:11434/api/chat"
        
        instruccion_actual = self.system_instruction + "\n" + self.obtener_contexto_memoria()
        messages = [{"role": "system", "content": instruccion_actual}]
        
        for msg in self.historial[-10:]:
            r_str = msg.get("role", "user")
            role = "user" if r_str == "user" else "assistant"
            text = ""
            if isinstance(msg, dict):
                if "content" in msg and isinstance(msg["content"], str):
                    text = msg["content"]
                elif "parts" in msg and isinstance(msg["parts"], list) and len(msg["parts"]) > 0:
                    text = msg["parts"][0].get("text", "")
            if text:
                messages.append({"role": role, "content": text})
            
        messages.append({"role": "user", "content": mensaje})

        modelo_target = "qwen2.5:1.5b"
        try:
            r_tags = requests.get("http://localhost:11434/api/tags", timeout=2)
            if r_tags.status_code == 200:
                models_data = r_tags.json().get("models", [])
                if models_data:
                    modelo_target = models_data[0].get("name", modelo_target)
        except Exception:
            pass

        payload = {
            "model": modelo_target,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 200
            }
        }

        try:
            r = requests.post(url, json=payload, timeout=15)
            if r.status_code == 200:
                respuesta_raw = r.json().get("message", {}).get("content", "").replace("*", "").strip()
                
                import re
                emocion = "Calmado"
                texto_limpio = respuesta_raw
                
                match_emocion = re.search(r'\[EMOTION:\s*([^\]]+)\]', respuesta_raw, re.IGNORECASE)
                if match_emocion:
                    emocion_detectada = match_emocion.group(1).strip().capitalize()
                    if emocion_detectada in ["Calmado", "Entusiasmado", "Empático", "Analítico", "Preocupado", "Irónico"]:
                        emocion = emocion_detectada
                    texto_limpio = re.sub(r'\[EMOTION:\s*[^\]]+\]', '', respuesta_raw).strip()

                match_accion = re.search(r'\[ACTION:\s*([^\]]+)\]', respuesta_raw, re.IGNORECASE)
                accion_detectada = None
                if match_accion:
                    accion_detectada = match_accion.group(1).strip()
                    texto_limpio = re.sub(r'\[ACTION:\s*[^\]]+\]', '', texto_limpio).strip()

                EMOCION_ACTUAL = emocion
                self.historial.append({"role": "user", "content": mensaje})
                self.historial.append({"role": "assistant", "content": respuesta_raw})
                if len(self.historial) > 20:
                    self.historial = self.historial[-20:]

                return texto_limpio, accion_detectada
        except Exception as e:
            print(f"[Ollama LLM Error]: {e}")
        return None, None

    def pensar(self, mensaje):
        global EMOCION_ACTUAL
        # 1. Intentar pensar con Ollama Local (100% Offline, sin Gemini)
        res_ollama, acc_ollama = self.pensar_ollama(mensaje)
        if res_ollama:
            return res_ollama, acc_ollama

        # 2. Fallback a OpenRouter si Ollama no está activo y hay conexión
        if not self.api_key:
            res_or, acc_or = self.pensar_openrouter(mensaje)
            if res_or and "no he detectado" not in res_or:
                return res_or, acc_or

        # 3. Respuesta de emergencia local offline
        EMOCION_ACTUAL = "Calmado"
        return f"Señor, estoy operando en modo local desconectado. ¿En qué le puedo asistir con los comandos del equipo?", None

def generar_codigo_con_gemini(indicacion):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None, "Señor, no he detectado la clave API de Gemini para generar el código."
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    prompt = (
        f"Genera el código solicitado para la siguiente indicación: '{indicacion}'. "
        "Debes responder ÚNICAMENTE con un objeto JSON estructurado con el siguiente formato, sin bloques de código markdown: "
        '{"nombre_archivo": "nombre_sugerido_con_extension_adecuada", "codigo": "el código completo generado aquí"}'
    )
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "maxOutputTokens": 1000,
            "temperature": 0.2
        }
    }
    
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        if r.status_code == 200:
            datos = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            import json
            resultado = json.loads(datos)
            return resultado.get("nombre_archivo", "codigo_generado.py"), resultado.get("codigo", "")
        else:
            return None, f"Error de comunicación externa. Estado: {r.status_code}."
    except Exception as e:
        return None, f"Fallo al procesar el código: {e}"

# =====================================================================
# 3. INTERFAZ DE CONTROL FÍSICO DEL SISTEMA (MANOS)
# =====================================================================
def buscar_app_sistema(nombre_app):
    nombre_normalizado = nombre_app.lower().strip()
    
    # Rutas clave de búsqueda de accesos directos de programas en Windows
    rutas_programas = [
        # Escritorio del usuario
        os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop"),
        os.path.join(os.path.expanduser("~"), "Desktop"),
        
        # Menú Inicio del usuario (Donde se colocan la gran mayoría de apps instaladas por el usuario)
        os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "Microsoft", "Windows", "Start Menu", "Programs"),
        
        # Menú Inicio global de la máquina (Apps instaladas para todos los usuarios)
        os.path.join(os.environ.get("ProgramData", "C:\\ProgramData"), "Microsoft", "Windows", "Start Menu", "Programs"),
        
        # Carpetas comunes de ejecutables locales
        os.path.join(os.path.expanduser("~"), "AppData", "Local", "Programs"),
        
        # Carpeta especial de aplicaciones de la Tienda de Windows Store (UWP como Spotify!)
        os.path.join(os.path.expanduser("~"), "AppData", "Local", "Microsoft", "WindowsApps")
    ]
    
    # Buscar de forma recursiva accesos directos (.lnk), ejecutables (.exe) o accesos web (.url)
    for ruta_base in rutas_programas:
        if not os.path.exists(ruta_base):
            continue
            
        try:
            for root, dirs, files in os.walk(ruta_base):
                # Limitar a profundidad de 2 carpetas para mantener el escaneo ultra-veloz y latencia cero
                depth = root[len(ruta_base):].count(os.path.sep)
                if depth > 2:
                    continue
                    
                for archivo in files:
                    item_nombre, ext = os.path.splitext(archivo)
                    ext_lc = ext.lower()
                    
                    # Nos interesan accesos directos, ejecutables o urls de internet locales
                    if ext_lc in [".lnk", ".exe", ".url"]:
                        # Comparación de coincidencia exacta o parcial
                        if nombre_normalizado == item_nombre.lower() or nombre_normalizado in item_nombre.lower():
                            ruta_completa = os.path.join(root, archivo)
                            try:
                                os.startfile(ruta_completa)
                                return item_nombre, "aplicación", True
                            except Exception:
                                continue
        except Exception:
            continue
            
    return None, None, False

def buscar_archivo_o_carpeta_sistema(nombre_objetivo):
    nombre_normalizado = nombre_objetivo.lower().strip()
    
    # Directorios base para buscar archivos y carpetas del usuario
    carpetas_busqueda = [
        # Escritorio del usuario (OneDrive o Local)
        os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop"),
        os.path.join(os.path.expanduser("~"), "Desktop"),
        # Carpetas de usuario comunes
        os.path.join(os.path.expanduser("~"), "Downloads"),
        os.path.join(os.path.expanduser("~"), "Documents"),
        os.path.join(os.path.expanduser("~"), "Pictures"),
        os.path.join(os.path.expanduser("~"), "Music"),
        os.path.join(os.path.expanduser("~"), "Videos"),
        # Directorio de trabajo actual (Workspace)
        os.getcwd()
    ]
    
    # Eliminar duplicados manteniendo el orden y confirmar existencia
    carpetas_busqueda = list(dict.fromkeys(c for c in carpetas_busqueda if os.path.exists(c)))
    
    # Carpetas que queremos ignorar por completo
    ignorar_directorios = {
        "node_modules", ".git", "__pycache__", "appdata", "local settings", 
        "cookies", "cache", "temp", "system32", "windows", "program files", 
        "program files (x86)", "$recycle.bin"
    }

    # Búsqueda por niveles (BFS) utilizando os.scandir para velocidad extrema (hasta 10x más rápido que os.walk)
    # Cola de carpetas a procesar estructurada por nivel: (ruta_carpeta, nivel_actual)
    cola = [(c, 0) for c in carpetas_busqueda]
    
    while cola:
        ruta_actual, nivel = cola.pop(0)
        
        # Limitar profundidad máxima a 3 niveles para mantener latencia ultra baja
        if nivel > 3:
            continue
            
        try:
            # os.scandir es inmensamente más veloz porque cachea los metadatos de archivos en Windows
            with os.scandir(ruta_actual) as entradas:
                subcarpetas = []
                for entrada in entradas:
                    nombre_entrada_lc = entrada.name.lower()
                    
                    # Ignorar archivos/carpetas ocultas o del sistema
                    if entrada.name.startswith('.') or entrada.name.startswith('~$'):
                        continue
                        
                    if entrada.is_dir():
                        if nombre_entrada_lc in ignorar_directorios:
                            continue
                        
                        # Comprobar coincidencia exacta o parcial en carpetas
                        if nombre_normalizado == nombre_entrada_lc or nombre_normalizado in nombre_entrada_lc:
                            ruta_completa = entrada.path
                            try:
                                os.startfile(ruta_completa)
                                return entrada.name, "carpeta", True
                            except Exception:
                                pass
                        
                        # Agregar a la lista para procesar en el siguiente nivel de profundidad
                        subcarpetas.append((entrada.path, nivel + 1))
                        
                    elif entrada.is_file():
                        item_nombre, ext = os.path.splitext(entrada.name)
                        item_nombre_lc = item_nombre.lower()
                        
                        # Comprobar coincidencia en archivos
                        if nombre_normalizado == item_nombre_lc or nombre_normalizado in item_nombre_lc:
                            ruta_completa = entrada.path
                            try:
                                os.startfile(ruta_completa)
                                return entrada.name, "archivo", True
                            except Exception:
                                pass
                                
                # Agregar subcarpetas de este directorio al final de la cola para BFS
                cola.extend(subcarpetas)
                
        except Exception:
            continue
            
    return None, None, False


# =====================================================================
# 3. INTERFAZ DE CONTROL FÍSICO DEL SISTEMA (MANOS)
# =====================================================================
def ejecutar_comando_sistema(comando, motor_voz, escuchar_func, cerebro=None):
    cmd = comando.lower().strip()

    # Mapeo de equivalencias fonéticas de nombres en inglés transcritos a español
    equivalentes_foneticos = {
        # Carpetas
        "downloads": ["downloads", "daunlos", "daunlas", "danlas", "downla", "daonlas", "daonlos", "descargas"],
        "desktop": ["desktop", "destop", "de stop", "destap", "escritorio"],
        "documents": ["documents", "dokiuments", "documens", "documentos"],
        "pictures": ["pictures", "picshurs", "pichurs", "imágenes", "imagenes"],
        "music": ["music", "miusic", "musi", "música", "musica"],
        "videos": ["videos", "vídeos"],
        
        # Aplicaciones y carpetas locales
        "steam": ["steam", "estim", "es tim", "istim", "istín"],
        "chrome": ["chrome", "crome", "crom", "croma", "chrim"],
        "deskin": ["deskin", "desquien", "desquin", "de skin"],
        "discord": ["discord", "discor", "discol", "disco"],
        "whatsapp": ["whatsapp", "wasap", "guatsap", "watsap"],
        "spotify": ["spotify", "espotifai", "spotifai", "espotify"]
    }

    # Definir carpetas del sistema
    escritorio_dir = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop")
    if not os.path.exists(escritorio_dir):
        escritorio_dir = os.path.join(os.path.expanduser("~"), "Desktop")
        
    carpetas_sistema = {
        "descargas": os.path.join(os.path.expanduser("~"), "Downloads"),
        "downloads": os.path.join(os.path.expanduser("~"), "Downloads"),
        "documentos": os.path.join(os.path.expanduser("~"), "Documents"),
        "documents": os.path.join(os.path.expanduser("~"), "Documents"),
        "imágenes": os.path.join(os.path.expanduser("~"), "Pictures"),
        "imagenes": os.path.join(os.path.expanduser("~"), "Pictures"),
        "pictures": os.path.join(os.path.expanduser("~"), "Pictures"),
        "música": os.path.join(os.path.expanduser("~"), "Music"),
        "musica": os.path.join(os.path.expanduser("~"), "Music"),
        "music": os.path.join(os.path.expanduser("~"), "Music"),
        "videos": os.path.join(os.path.expanduser("~"), "Videos"),
        "vídeos": os.path.join(os.path.expanduser("~"), "Videos"),
        "escritorio": escritorio_dir,
        "desktop": escritorio_dir,
        "usuario": os.path.expanduser("~"),
        "user": os.path.expanduser("~"),
        "disco c": "C:\\",
        "c": "C:\\",
        "disco d": "D:\\",
        "d": "D:\\"
    }

    # --- HORA Y FECHA ---
    if any(k in cmd for k in ["hora es", "dime la hora", "hora actual"]):
        ahora = datetime.now().strftime("%H:%M")
        return f"Son exactamente las {ahora}, Señor."
        
    if any(k in cmd for k in ["fecha es", "fecha de hoy", "dime el día", "dime la fecha", "qué día es hoy"]):
        meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        ahora = datetime.now()
        fecha_str = f"{ahora.day} de {meses[ahora.month - 1]} de {ahora.year}"
        return f"Hoy es {fecha_str}, Señor."

    # --- CONTROL DE VENTANAS DEL SISTEMA ---
    if any(k in cmd for k in ["minimiza la ventana", "minimizar ventana", "minimiza todo", "minimizar todo", "oculta todo"]):
        pyautogui.hotkey('win', 'd')
        return "Minimizando todas las ventanas de inmediato, Señor."
        
    if any(k in cmd for k in ["maximiza la ventana", "maximizar ventana", "maximiza todo", "maximizar todo"]):
        pyautogui.hotkey('win', 'up')
        return "Maximizando la ventana activa, Señor."
        
    if any(k in cmd for k in ["cierra la ventana", "cerrar ventana", "cierra esto", "cerrar esto"]):
        pyautogui.hotkey('alt', 'f4')
        return "Cerrando la ventana activa, Señor."
        
    if any(k in cmd for k in ["bloquea el equipo", "bloquear equipo", "bloquea la pc", "bloquear pc", "bloquea la pantalla"]):
        try:
            ctypes.windll.user32.LockWorkStation()
            return "Entendido, Señor. Equipo bloqueado de forma segura."
        except Exception as e:
            return f"He intentado bloquear el equipo pero ocurrió un impedimento técnico: {e}"
            
    if any(k in cmd for k in ["administrador de tareas", "abrir administrador de tareas", "procesos del sistema"]):
        try:
            subprocess.Popen("taskmgr.exe")
            return "Abriendo el Administrador de Tareas de Windows, Señor."
        except Exception as e:
            return f"No he podido iniciar el Administrador de Tareas: {e}"
            
    if any(k in cmd for k in ["cambia de pestaña", "cambiar pestaña", "cambia pestaña", "siguiente pestaña"]):
        pyautogui.hotkey('ctrl', 'tab')
        return "Cambiando a la siguiente pestaña, Señor."

    # --- GESTIÓN DE NOTAS RÁPIDAS ---
    if cmd.startswith("nota "):
        accion_nota = cmd[5:].strip()
        es_lectura = any(k in accion_nota for k in ["lee mis notas", "muestra mis notas", "dime mis notas", "lee las notas", "cuáles son mis notas", "léeme las notas", "muéstrame las notas de hoy"])
        ruta_notas = "notas_layo.txt"
        
        if es_lectura:
            if not os.path.exists(ruta_notas):
                return "Señor, no he encontrado ninguna nota registrada en el almacenamiento local."
            try:
                with open(ruta_notas, "r", encoding="utf-8") as f:
                    lineas = [linea.strip() for linea in f.readlines() if linea.strip()]
                if not lineas:
                    return "Su registro de notas se encuentra vacío, Señor."
                
                # Leer las últimas 5 notas
                ultimas_lineas = lineas[-5:]
                notas_txt = ". ".join(ultimas_lineas)
                return f"Aquí tiene sus últimas anotaciones, Señor: {notas_txt}"
            except Exception as e:
                return f"Señor, no he podido leer sus notas debido a un inconveniente: {e}"
        else:
            # Limpiar prefijo si existe
            for p in ["crea una nota que diga ", "crea nota que diga ", "toma una nota que diga ", "toma nota de ", "escribe una nota que diga ", "guarda una nota de ", "anota ", "apunta "]:
                if accion_nota.startswith(p):
                    accion_nota = accion_nota[len(p):].strip()
                    break
            
            try:
                fecha_nota = datetime.now().strftime("%Y-%m-%d %H:%M")
                with open(ruta_notas, "a", encoding="utf-8") as f:
                    f.write(f"[{fecha_nota}] {accion_nota}\n")
                return f"Entendido, Señor. He registrado la nota: '{accion_nota}'."
            except Exception as e:
                return f"No he podido guardar la nota debido a un error en el disco: {e}"

    # --- BÚSQUEDA WEB DIRECTA ---
    if cmd.startswith("busca en google "):
        consulta_web = comando.lower().strip()
        p_clave = ["jarvis", "yarvis", "harvis", "charvis", "layo", "rayo", "layono", "computadora"]
        for kw in p_clave:
            if consulta_web.startswith(kw):
                consulta_web = consulta_web[len(kw):].strip()
                while consulta_web and consulta_web[0] in [",", ".", " ", "?", "¿", ":", "-", "_"]:
                    consulta_web = consulta_web[1:].strip()
                break
                
        for v in ["buscar en google ", "busca en google ", "buscar en internet ", "busca en internet ", "busca información de ", "busca informacion sobre ", "investiga sobre ", "googlea "]:
            if consulta_web.startswith(v):
                consulta_web = consulta_web[len(v):].strip()
                break
                
        import urllib.parse
        url = f"https://www.google.com/search?q={urllib.parse.quote(consulta_web)}"
        webbrowser.open(url)
        return f"Realizando búsqueda en Google sobre '{consulta_web}' en su navegador, Señor."

    # --- CAPTURA DE PANTALLA ---
    if any(k in cmd for k in ["captura de pantalla", "toma una captura", "pantallazo", "captura la pantalla"]):
        try:
            nombre_archivo = f"captura_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            ruta = os.path.join(escritorio_dir, nombre_archivo)
            
            # Pequeña pausa para ocultar la consola
            time.sleep(0.5)
            pyautogui.screenshot(ruta)
            return f"Captura realizada con éxito. La he almacenado en su Escritorio como {nombre_archivo}, Señor."
        except Exception as e:
            return f"No he podido completar la captura debido a un fallo: {e}"

    # --- ANALIZAR PANTALLA (OJOS DE ASISTENTE) ---
    if any(k in cmd for k in ["analizar pantalla", "analizar_pantalla", "analiza mi pantalla", "mira mi pantalla", "observa mi pantalla", "qué hay en mi pantalla", "analiza la pantalla"]):
        if cerebro is None:
            return "Señor, el módulo cerebral de visión no se encuentra enlazado al controlador de hardware."
        try:
            import base64
            import io
            
            # Pequeña pausa para permitir que el usuario organice su pantalla
            time.sleep(0.5)
            
            # Capturar pantalla silenciosamente
            captura = pyautogui.screenshot()
            
            # Guardar captura en memoria (buffer) comprimida en JPEG
            buf = io.BytesIO()
            captura.save(buf, format="JPEG", quality=70)
            img_bytes = buf.getvalue()
            image_b64 = base64.b64encode(img_bytes).decode("utf-8")
            
            motor_voz.hablar("Entendido, Señor. Estoy observando su pantalla en este preciso instante. Permítame analizar los detalles.")
            
            # Solicitar descripción visual multimodal
            analisis = cerebro.analizar_imagen(image_b64, mime_type="image/jpeg")
            return analisis
        except Exception as e:
            return f"No he podido realizar el análisis visual de la pantalla debido a un inconveniente técnico: {e}"

    # --- VOLUMEN DEL SISTEMA ---
    if "sube el volumen" in cmd or "subir volumen" in cmd:
        for _ in range(5):
            pyautogui.press('volumeup')
        return "Volumen del sistema incrementado en un diez por ciento, Señor."
        
    if "baja el volumen" in cmd or "bajar volumen" in cmd:
        for _ in range(5):
            pyautogui.press('volumedown')
        return "Volumen del sistema reducido en un diez por ciento, Señor."
        
    if "silencio" in cmd or "mutear" in cmd or "quitar silencio" in cmd:
        pyautogui.press('volumemute')
        return "He alternado el estado de silencio de los altavoces, Señor."

    # --- ESCRIBIR TEXTO ---
    if cmd.startswith("escribe "):
        texto_a_escribir = comando[8:].strip()
        time.sleep(1) # Tiempo de reacción para que el usuario sitúe el cursor
        pyautogui.write(texto_a_escribir, interval=0.05)
        return "He simulado la escritura del texto solicitado, Señor."

    # --- APAGADO Y REINICIO SEGURO ---
    if any(k in cmd for k in ["apaga el equipo", "apagar el equipo", "apaga la computadora", "apagar la computadora"]):
        motor_voz.hablar("Señor, ¿está completamente seguro de que desea iniciar la secuencia de apagado?")
        mostrar_estado("escuchando")
        confirmacion = escuchar_func()
        print(f"\r{Fore.YELLOW}Usted: {Fore.WHITE}{confirmacion}{Fore.RESET}")
        
        if confirmacion and any(k in confirmacion.lower() for k in ["sí", "si", "afirmativo", "procede", "apágalo", "apagalo"]):
            motor_voz.hablar("Entendido. Iniciando desconexión del sistema central. Apagando equipo en diez segundos. Hasta pronto, Señor.")
            time.sleep(5)
            os.system("shutdown /s /t 1")
            return "Apagando..."
        else:
            return "Entendido, Señor. Secuencia de apagado abortada."

    if any(k in cmd for k in ["reinicia el equipo", "reiniciar el equipo", "reinicia la computadora", "reiniciar computadora"]):
        motor_voz.hablar("Señor, ¿está seguro de que desea reiniciar el sistema?")
        mostrar_estado("escuchando")
        confirmacion = escuchar_func()
        print(f"\r{Fore.YELLOW}Usted: {Fore.WHITE}{confirmacion}{Fore.RESET}")
        
        if confirmacion and any(k in confirmacion.lower() for k in ["sí", "si", "afirmativo", "procede", "reinícialo", "reinicialo"]):
            motor_voz.hablar("Entendido. Reiniciando núcleo de operaciones. Reiniciando equipo en diez segundos.")
            time.sleep(5)
            os.system("shutdown /r /t 1")
            return "Reiniciando..."
        else:
            return "Entendido, Señor. Secuencia de reinicio abortada."

    # --- CERRAR APLICACIONES ACTIVAS ---
    if "cierra " in cmd:
        programa_objetivo = cmd.split("cierra ")[1].strip()
        cerrados = 0
        for proc in psutil.process_iter(['name']):
            try:
                if programa_objetivo in proc.info['name'].lower():
                    proc.terminate()
                    cerrados += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        if cerrados > 0:
            return f"He terminado las instancias activas de {programa_objetivo}, Señor."

    # --- ESCRIBIR/PROGRAMAR CÓDIGO EN VSCODE (MODO DESARROLLO DE LAYO) ---
    if any(k in cmd for k in ["escribe un código", "escribe un codigo", "crea un código", "crea un codigo", "programa en vscode", "programa un código", "programa un codigo", "escribe código", "escribe codigo"]):
        limpiadores = [
            "escribe un código en vscode de ", "escribe un codigo en vscode de ",
            "escribe un código de ", "escribe un codigo de ",
            "crea un código de ", "crea un codigo de ",
            "programa en vscode ", "programa un código de ", "programa un codigo de ",
            "escribe código de ", "escribe codigo de ",
            "escribe un código ", "escribe un codigo ",
            "crea un código ", "crea un codigo ",
            "escribe código ", "escribe codigo "
        ]
        indicacion = cmd
        for l in limpiadores:
            if l in indicacion:
                indicacion = indicacion.replace(l, "")
                break
        indicacion = indicacion.strip()
        
        # Proceder
        motor_voz.hablar("Entendido, Señor. Estoy compilando las instrucciones y generando el código solicitado en mis sistemas neuronales. Espere un instante.")
        
        nombre_archivo, codigo_generado = generar_codigo_con_gemini(indicacion)
        
        if nombre_archivo and codigo_generado:
            try:
                with open(nombre_archivo, "w", encoding="utf-8") as f:
                    f.write(codigo_generado)
                # Abrir archivo en VS Code
                subprocess.Popen(["code", nombre_archivo], shell=True)
                return f"Secuencia completada. He generado el archivo como {nombre_archivo} y lo he abierto en Visual Studio Code para usted, Señor."
            except Exception as e:
                return f"Señor, he estructurado el código pero encontré un impedimento para guardar el archivo: {e}"
        else:
            return f"Señor, se presentó un contratiempo técnico en el satélite: {codigo_generado}"

    # --- REPRODUCCIÓN DE MEDIOS (SPOTIFY Y YOUTUBE) ---
    es_reproduccion = any(cmd.startswith(k) for k in ["reproduce ", "reproducir ", "pon ", "poner ", "escucha ", "escuchar "]) or \
                      ((cmd.startswith("busca ") or cmd.startswith("buscar ")) and \
                       any(x in cmd for x in ["en spotify", "de spotify", "en youtube", "de youtube", "en yotube", "en iutub"]))
    
    if es_reproduccion:
        prefijos_media = [
            "reproduce la canción de ", "reproduce la canción ", "reproduce la música de ", "reproduce la música ", 
            "reproduce el vídeo de ", "reproduce el vídeo ", "reproduce el video de ", "reproduce el video ", 
            "reproduce la musica de ", "reproduce la musica ", "reproduce la música ", 
            "reproduce ", "reproducir ", "pon la canción de ", "pon la canción ", "pon el vídeo de ", 
            "pon el vídeo ", "pon el video de ", "pon el video ", "pon la musica ", "pon la música ", 
            "pon ", "poner ", "escucha la canción de ", "escucha la canción ", 
            "escucha la musica ", "escucha la música ", "escucha ", "escuchar "
        ]
        consulta_media = cmd
        for p in prefijos_media:
            if consulta_media.startswith(p):
                consulta_media = consulta_media[len(p):].strip()
                break
                
        # Limpiar verbos secundarios de búsqueda/reproducción sobrantes (ej. "reproduce busca X")
        verbos_secundarios = ["busca ", "buscar ", "reproduce ", "reproducir ", "pon ", "poner ", "escucha ", "escuchar "]
        cambiado = True
        while cambiado:
            cambiado = False
            for v in verbos_secundarios:
                if consulta_media.startswith(v):
                    consulta_media = consulta_media[len(v):].strip()
                    cambiado = True
                
        # Determinar la plataforma (Spotify o YouTube)
        plataforma = None
        if "en spotify" in consulta_media or "de spotify" in consulta_media:
            plataforma = "spotify"
            consulta_media = consulta_media.replace("en spotify", "").replace("de spotify", "").strip()
        elif "en youtube" in consulta_media or "de youtube" in consulta_media or "en yotube" in consulta_media or "en iutub" in consulta_media:
            plataforma = "youtube"
            consulta_media = consulta_media.replace("en youtube", "").replace("de youtube", "").replace("en yotube", "").replace("en iutub", "").strip()
        else:
            # Si contiene "canción", "música", "álbum" o similares y no especifica, o si Spotify está abierto, priorizamos Spotify.
            # Si no, por defecto buscamos en YouTube que es más versátil.
            spotify_abierto = False
            for proc in psutil.process_iter(['name']):
                try:
                    if "spotify.exe" in proc.info['name'].lower():
                        spotify_abierto = True
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            if spotify_abierto or any(k in cmd for k in ["canción", "cancion", "música", "musica", "álbum", "album", "spotify"]):
                plataforma = "spotify"
            else:
                plataforma = "youtube"
                
        if plataforma == "spotify":
            # 1. Comprobar si Spotify está corriendo en los procesos de Windows
            spotify_corriendo = False
            for proc in psutil.process_iter(['name']):
                try:
                    if "spotify.exe" in proc.info['name'].lower():
                        spotify_corriendo = True
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # 2. Si está cerrado, abrir la app local
            msj_adicional = ""
            if not spotify_corriendo:
                msj_adicional = "He detectado que Spotify se encuentra desactivado. Procedo a inicializarlo. "
                # Buscar y abrir Spotify de forma local
                app_encontrada, tipo_app, exito_app = buscar_app_sistema("spotify")
                if not exito_app:
                    try:
                        # Si no encuentra .lnk o .exe en directorios del menú inicio, intenta abrir vía protocolo
                        os.startfile("spotify:")
                    except Exception:
                        pass
                # Esperar 2.5 segundos a que la aplicación inicie y registre el receptor de URIs
                time.sleep(2.5)
            
            # 3. Lanzar la consulta con codificación URI de Spotify
            try:
                import urllib.parse
                url_spotify = f"spotify:search:{urllib.parse.quote(consulta_media)}"
                os.startfile(url_spotify)
                return f"{msj_adicional}Reproduciendo '{consulta_media}' en Spotify de inmediato, Señor."
            except Exception:
                url_web = f"https://open.spotify.com/search/{urllib.parse.quote(consulta_media)}"
                webbrowser.open(url_web)
                return f"Iniciando reproducción de '{consulta_media}' en Spotify Web, Señor."
                
        elif plataforma == "youtube":
            import urllib.parse
            url_youtube = f"https://www.youtube.com/results?search_query={urllib.parse.quote(consulta_media)}"
            webbrowser.open(url_youtube)
            return f"Buscando '{consulta_media}' en YouTube. Abriendo los resultados de inmediato, Señor."

    # --- BUSCAR U ABRIR LOCAL O GOOGLE (ACCIONES DE NAVEGACIÓN Y APPS) ---
    if cmd.startswith("abre ") or cmd.startswith("lanza ") or cmd.startswith("busca ") or cmd.startswith("buscar "):
        # Limpiar prefijo para extraer el nombre del objetivo
        prefijos = [
            "abre la carpeta de ", "abre la carpeta ", "abre el disco ", "abre carpeta ", 
            "abre la página de ", "abre la página ", "abre la web de ", "abre la web ", 
            "abre el sitio de ", "abre el sitio ", "abre ", "lanza ", 
            "buscar la carpeta de ", "buscar la carpeta ", "buscar el archivo de ", "buscar el archivo ", "buscar ", 
            "busca la carpeta de ", "busca la carpeta ", "busca el archivo de ", "busca el archivo ", "busca "
        ]
        nombre_objetivo = cmd
        for p in prefijos:
            if nombre_objetivo.startswith(p):
                nombre_objetivo = nombre_objetivo[len(p):].strip()
                break
        
        # Normalizar fonética en inglés
        for clave_real, lista_fonetica in equivalentes_foneticos.items():
            if nombre_objetivo in lista_fonetica or any(f in nombre_objetivo for f in lista_fonetica):
                nombre_objetivo = clave_real
                break

        # A. Comprobar si es un programa común del sistema
        programas_comunes = {
            "notepad": "notepad.exe",
            "bloc de notas": "notepad.exe",
            "calculadora": "calc.exe",
            "paint": "mspaint.exe",
            "cmd": "cmd.exe",
            "consola": "cmd.exe",
            "explorer": "explorer.exe",
            "explorador de archivos": "explorer.exe",
            "vscode": "code",
            "visual studio code": "code",
            "code": "code"
        }
        
        if nombre_objetivo in programas_comunes:
            try:
                if nombre_objetivo in ["vscode", "visual studio code", "code"]:
                    subprocess.Popen(["code", "."])
                else:
                    subprocess.Popen(programas_comunes[nombre_objetivo])
                return f"Abriendo {nombre_objetivo} de inmediato, Señor."
            except Exception as e:
                return f"Fallo al abrir el ejecutable local: {e}"

        # B. Comprobar si el usuario especificó explícitamente una solicitud web
        es_solicitud_web = any(k in cmd for k in ["la web de", "la pagina de", "la página de", "el sitio de", "el sitio web de", ".com", ".net", ".org", ".es", "buscar en google", "busca en google", "en google", "en internet"])
        
        # C. Si no es una solicitud web explícita, buscar en el equipo local:
        if not es_solicitud_web:
            # 1. Comprobar si es una carpeta del sistema directa (como Descargas, Documentos, etc.)
            if nombre_objetivo in carpetas_sistema:
                ruta_carpeta = carpetas_sistema[nombre_objetivo]
                if os.path.exists(ruta_carpeta):
                    try:
                        os.startfile(ruta_carpeta)
                        return f"Abriendo la carpeta del sistema {nombre_objetivo}, Señor."
                    except Exception as e:
                        return f"He intentado abrir la carpeta {nombre_objetivo}, pero ocurrió un error: {e}"

            # 2. Buscar app instalada (desempaquetado correcto de 3 variables)
            app_encontrada, tipo_app, exito_app = buscar_app_sistema(nombre_objetivo)
            if exito_app:
                return f"Abriendo la aplicación local {app_encontrada}, Señor."
                
            # 3. Buscar archivo o carpeta local recursivamente
            nombre_encontrado, tipo, exito_local = buscar_archivo_o_carpeta_sistema(nombre_objetivo)
            if exito_local:
                return f"Localizado. Abriendo el {tipo} local {nombre_encontrado}, Señor."

        # D. Si es explícitamente web, o si NO se encontró localmente en Windows:
        #    Abrir navegador web o buscar en Google
        sitio_sin_espacios = nombre_objetivo.replace("la web de ", "").replace("la pagina de ", "").replace("la página de ", "").replace(" ", "")
        
        if not (sitio_sin_espacios.endswith(".com") or sitio_sin_espacios.endswith(".net") or sitio_sin_espacios.endswith(".org") or sitio_sin_espacios.endswith(".es") or sitio_sin_espacios.endswith(".io")):
            # Comprobar webs populares
            webs_populares = {
                "youtube": "https://www.youtube.com",
                "facebook": "https://www.facebook.com",
                "twitter": "https://www.twitter.com",
                "instagram": "https://www.instagram.com",
                "github": "https://www.github.com",
                "gmail": "https://mail.google.com",
                "netflix": "https://www.netflix.com",
                "chatgpt": "https://chat.openai.com",
                "google": "https://www.google.com",
                "spotify": "https://open.spotify.com"
            }
            if sitio_sin_espacios in webs_populares:
                url = webs_populares[sitio_sin_espacios]
                msj = f"Abriendo el portal web de {nombre_objetivo} en su navegador principal, Señor."
            else:
                # Búsqueda en Google
                url = f"https://www.google.com/search?q={requests.utils.quote(nombre_objetivo)}"
                msj = f"No he localizado ningún programa, archivo o carpeta llamada {nombre_objetivo} en sus discos locales. Iniciando búsqueda en Google, Señor."
        else:
            url = f"https://{sitio_sin_espacios}"
            msj = f"Abriendo el portal web de {nombre_objetivo} en su navegador principal, Señor."
            
        webbrowser.open(url)
        return msj

    return None

# =====================================================================
# 4. CAPTURA Y PROCESAMIENTO DE AUDIO (OÍDOS)
# =====================================================================
reconocedor = sr.Recognizer()
# Ajuste fino de silencios y sensibilidad del micrófono para latencia ultra-baja y precisión
reconocedor.pause_threshold = 0.5  # Pausa requerida para considerar fin de frase (muy ágil)
reconocedor.operation_timeout = 5.0 # Tiempo límite para conectarse a Google STT
reconocedor.dynamic_energy_threshold = True
reconocedor.dynamic_energy_threshold_damping = 0.15
reconocedor.dynamic_energy_threshold_low_cutoff = 100
reconocedor.energy_threshold = 200 # Sensibilidad inicial óptima para captar voz baja

def escuchar():
    with sr.Microphone() as origen:
        try:
            # Captura de audio optimizada con límite de frase amplio para indicaciones complejas
            audio = reconocedor.listen(origen, timeout=4, phrase_time_limit=9)
            texto = reconocedor.recognize_google(audio, language="es-ES").lower()
            return texto
        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            return ""
        except sr.RequestError:
            # Reconocimiento de Google no disponible sin conexión
            return ""
        except Exception:
            return ""

def extraer_comando(texto, palabras_clave):
    texto_lc = texto.lower()
    for kw in palabras_clave:
        if kw in texto_lc:
            idx = texto_lc.find(kw)
            comando = texto[idx + len(kw):].strip()
            # Limpiar puntuaciones iniciales de la frase extraída
            while comando and comando[0] in [",", ".", " ", "?", "¿", ":", "-", "_"]:
                comando = comando[1:].strip()
            return True, comando
    return False, ""

# =====================================================================
# BUCLE PRINCIPAL DE CONTROL
# =====================================================================
def main():
    # Detectar suite de pruebas automatizadas --test
    if "--test" in sys.argv:
        ejecutar_pruebas_unitarias()

    limpiar_pantalla()
    mostrar_logo()
    
    # 1. Cargar Cerebro
    cerebro = CerebroJarvis()
    
    # 2. Cargar Voz
    voz = MotorVocal()
    
    # 3. Cargar Motor de Machine Learning Local (PyTorch)
    motor_ml = MotorMLLayo()
    if motor_ml.activo:
        print(f"{Fore.GREEN}[ML Core] Modelo de red neuronal PyTorch cargado con éxito. Clasificación activa a 0ms.{Fore.RESET}")
    else:
        print(f"{Fore.YELLOW}[ML Core] Red neuronal inactiva (vocabulario/pesos no encontrados). Operando en modo de enrutamiento en la nube (Gemini).{Fore.RESET}")
    
    # Selector de canal de entrada físico para el usuario
    print(f"\n{Fore.CYAN}[Sistema] Seleccione el canal de comunicación central:{Fore.RESET}")
    print(f"{Fore.WHITE}  [1] Entrada por Voz (Micrófono - Manos Libres)")
    print(f"{Fore.WHITE}  [2] Entrada por Escritura (Teclado - Consola)")
    
    canal = input(f"\n{Fore.CYAN}Selección [1 o 2] (Por defecto es 1): {Fore.RESET}").strip()
    modo_entrada = "voz"
    if canal == "2":
        modo_entrada = "teclado"
        print(f"\n{Fore.GREEN}[Sistema] Canal establecido en Escritura (Teclado). Wake-words desactivados.{Fore.RESET}")
    else:
        print(f"\n{Fore.GREEN}[Sistema] Canal establecido en Voz (Micrófono). Wake-words activos.{Fore.RESET}")
    
    # Palabras clave de activación del asistente (incluye variantes de transcripción común)
    palabras_clave = ["jarvis", "yarvis", "harvis", "charvis", "layo", "rayo", "layono", "computadora"]
    
    # 3. Saludo Inicial e Calibración de Micrófono
    time.sleep(0.5)
    saludo = "Señor, sistemas operativos e interfaz neuronal de comunicación completamente restablecidos. Estoy en línea y listo para recibir sus instrucciones."
    voz.hablar(saludo)
    
    if modo_entrada == "voz":
        # Calibrar micrófono una sola vez al inicio para latencia cero en el bucle
        mostrar_estado("pensando")
        print(f"\r{Fore.CYAN}[Micrófono] Calibrando sensores de ruido ambiental para latencia cero...{Fore.RESET}")
        with sr.Microphone() as origen:
            reconocedor.adjust_for_ambient_noise(origen, duration=1.2)
        print(f"{Fore.GREEN}[Micrófono] Calibración de sensores completada con éxito.{Fore.RESET}")
    
    # 4. Ciclo infinito de escucha táctica o entrada de teclado
    try:
        while True:
            if modo_entrada == "voz":
                mostrar_estado("escuchando")
                cmd = escuchar()
                
                if not cmd:
                    continue
                    
                # Verificar si se mencionó alguna palabra clave de activación
                detectado, comando_directo = extraer_comando(cmd, palabras_clave)
                
                if detectado:
                    print(f"\r{Fore.YELLOW}{Fore.BOLD}Usted: {Fore.WHITE}{cmd}{Fore.RESET}")
                    
                    if not comando_directo:
                        mostrar_estado("esperando")
                        voz.hablar("Dígame, Señor.")
                        
                        mostrar_estado("escuchando")
                        cmd_secundario = escuchar()
                        
                        if not cmd_secundario:
                            mostrar_estado("hablando")
                            voz.hablar("Asumiendo inactividad. Volviendo al estado latente.")
                            continue
                            
                        print(f"\r{Fore.YELLOW}{Fore.BOLD}Usted: {Fore.WHITE}{cmd_secundario}{Fore.RESET}")
                        
                        mostrar_estado("pensando")
                        # 1. Intentar clasificación con Machine Learning Local
                        intencion, confianza = motor_ml.predecir(cmd_secundario)
                        respuesta_sistema = None
                        if intencion and confianza > 0.85:
                            comando_ml = procesar_intencion_ml(intencion, cmd_secundario)
                            if comando_ml:
                                print(f"\r{Fore.BLUE}[ML Core: {intencion} ({confianza:.1%})] -> {comando_ml}{Fore.RESET}")
                                respuesta_sistema = ejecutar_comando_sistema(comando_ml, voz, escuchar, cerebro=cerebro)
                        
                        if not respuesta_sistema:
                            respuesta_sistema = ejecutar_comando_sistema(cmd_secundario, voz, escuchar, cerebro=cerebro)
                        
                        if respuesta_sistema:
                            voz.hablar(respuesta_sistema)
                        else:
                            respuesta_gemini, accion = cerebro.pensar(cmd_secundario)
                            voz.hablar(respuesta_gemini)
                            if accion:
                                respuesta_accion = ejecutar_comando_sistema(accion, voz, escuchar, cerebro=cerebro)
                                if respuesta_accion:
                                    voz.hablar(respuesta_accion)
                    else:
                        mostrar_estado("pensando")
                        # 1. Intentar clasificación con Machine Learning Local
                        intencion, confianza = motor_ml.predecir(comando_directo)
                        respuesta_sistema = None
                        if intencion and confianza > 0.85:
                            comando_ml = procesar_intencion_ml(intencion, comando_directo)
                            if comando_ml:
                                print(f"\r{Fore.BLUE}[ML Core: {intencion} ({confianza:.1%})] -> {comando_ml}{Fore.RESET}")
                                respuesta_sistema = ejecutar_comando_sistema(comando_ml, voz, escuchar, cerebro=cerebro)
                                
                        if not respuesta_sistema:
                            respuesta_sistema = ejecutar_comando_sistema(comando_directo, voz, escuchar, cerebro=cerebro)
                        
                        if respuesta_sistema:
                            voz.hablar(respuesta_sistema)
                        else:
                            respuesta_gemini, accion = cerebro.pensar(comando_directo)
                            voz.hablar(respuesta_gemini)
                            if accion:
                                respuesta_accion = ejecutar_comando_sistema(accion, voz, escuchar, cerebro=cerebro)
                                if respuesta_accion:
                                    voz.hablar(respuesta_accion)
            else:
                # Entrada de Escritura (Teclado)
                mostrar_estado("esperando")
                sys.stdout.write("\r" + " " * 80 + "\r") # Limpiar la línea de estado
                cmd = input(f"{Fore.YELLOW}{Fore.BOLD}Usted: {Fore.WHITE}").strip()
                
                if not cmd:
                    continue
                
                mostrar_estado("pensando")
                # 1. Intentar clasificación con Machine Learning Local
                intencion, confianza = motor_ml.predecir(cmd)
                respuesta_sistema = None
                if intencion and confianza > 0.85:
                    comando_ml = procesar_intencion_ml(intencion, cmd)
                    if comando_ml:
                        print(f"\r{Fore.BLUE}[ML Core: {intencion} ({confianza:.1%})] -> {comando_ml}{Fore.RESET}")
                        respuesta_sistema = ejecutar_comando_sistema(comando_ml, voz, lambda: input(f"{Fore.YELLOW}Confirmar (si/no): {Fore.WHITE}"), cerebro=cerebro)
                        
                if not respuesta_sistema:
                    respuesta_sistema = ejecutar_comando_sistema(cmd, voz, lambda: input(f"{Fore.YELLOW}Confirmar (si/no): {Fore.WHITE}"), cerebro=cerebro)
                
                if respuesta_sistema:
                    voz.hablar(respuesta_sistema)
                else:
                    respuesta_gemini, accion = cerebro.pensar(cmd)
                    voz.hablar(respuesta_gemini)
                    if accion:
                        respuesta_accion = ejecutar_comando_sistema(accion, voz, lambda: input(f"{Fore.YELLOW}Confirmar (si/no): {Fore.WHITE}"), cerebro=cerebro)
                        if respuesta_accion:
                            voz.hablar(respuesta_accion)
                            
    except KeyboardInterrupt:
        print(f"\n\n{Fore.RED}[Desconexión] Apagando enlace Layo de forma segura. Hasta luego, Señor.{Fore.RESET}")

if __name__ == "__main__":
    main()