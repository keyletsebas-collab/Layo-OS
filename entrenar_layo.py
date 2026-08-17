import os
import sys
import json
import time
import random
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

# =====================================================================
# CONFIGURACIÓN DE CONSOLA PREMIUM
# =====================================================================
try:
    import ctypes
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

# =====================================================================
# ARQUITECTURA DE APRENDIZAJE NEURONAL (IDÉNTICA A SISTEMA_LAYO)
# =====================================================================
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

# =====================================================================
# MATRICES DE GENERACIÓN SINTÉTICA COMBINATORIA (DATASET)
# =====================================================================
VERBOS_CARPETA = ["abre", "abre la carpeta", "abre la carpeta de", "abre el disco", "abre carpeta", "muestra", "muéstrame", "entra a", "entra en la carpeta", "busca la carpeta", "busca carpeta", "lanza la carpeta", "abrir la carpeta de"]
CARPETAS = [
    "descargas", "downloads", "daunlos", "daunlas", "descargar", 
    "documentos", "documents", "dokiuments", "mis documentos",
    "escritorio", "desktop", "destop", "de stop",
    "imágenes", "imagenes", "pictures", "mis fotos", "fotos",
    "música", "musica", "music", "miusic",
    "videos", "vídeos", "mis videos",
    "proyectos", "projects", "proyets", "código", "workspace", "trabajo",
    "disco c", "c", "disco d", "d"
]

VERBOS_APP = ["abre", "abre la aplicación", "abre la app", "abre la app de", "lanza", "lanza la aplicación", "lanza la app", "inicia", "iniciar", "ejecuta", "abre el programa", "arranca", "lanzar app"]
APPS = ["spotify", "espotifai", "spotifai", "steam", "estim", "es tim", "chrome", "crome", "google", "discord", "discor", "whatsapp", "wasap", "notepad", "bloc de notas", "paint", "calculadora", "vscode", "visual studio code", "code"]

VERBOS_MEDIA = ["reproduce", "reproducir", "reprodúceme", "reproduceme", "pon", "ponme", "poner", "escucha", "escuchar", "pon la canción de", "reproduce la canción de", "quiero escuchar", "toca la canción", "pon a sonar", "coloca"]
TEMAS_MEDIA = [
    "bohemian rhapsody", "bohemian rapsodi", "queen", "starboy", "the weeknd", "perfect", "adele", "shape of you", "sheip of iu", 
    "believer", "imagine dragons", "música para concentrarse", "música clásica", "lofi", "lo-fi", "lofi hip hop",
    "videos graciosos de gatitos", "vídeos de perritos", "trailer de avengers", "reactor arc", "iron man", "tony stark", "musica alegre", "cancion nueva"
]
CONECTORES_MEDIA = ["en spotify", "de spotify", "en youtube", "de youtube", "en yotube", "en iutub", "en internet", "en la web", ""]

VERBOS_VOLUMEN = ["sube", "subir", "incrementa", "aumenta", "sube un poco", "baja", "bajar", "reduce", "decrementa", "baja un poco", "pon en silencio", "silencio", "mutear", "quita el silencio", "desmutea", "volumen cero"]
COMPLEMENTOS_VOLUMEN = ["el volumen", "volumen", "los altavoces", "las bocinas", "el audio", "el sonido", ""]

VERBOS_CAPTURA = ["toma", "toma una", "haz una", "haz un", "captura", "capturar", "saca un", "saca una"]
TEMAS_CAPTURA = ["captura de pantalla", "pantallazo", "captura", "pantalla", "captura la pantalla", "foto de la pantalla"]

VERBOS_CODIGO = ["escribe un código", "escribe un codigo", "escribe código", "escribe codigo", "crea un código", "crea un codigo", "programa en vscode", "programa un código", "programa un codigo", "genera un código", "escribe un script"]
TEMAS_CODIGO = [
    "python de un juego de snake", "python de una calculadora", "html y css de una landing page", 
    "javascript de un tetris", "c++ de un algoritmo de ordenamiento", "python para web scraping",
    "un script de automatización", "un bot de discord", "un juego en 2d", "una base de datos sqlite"
]

FRASES_CONVERSACION = [
    "hola layo", "hola jarvis", "cómo estás", "quién eres", "cuéntame un chiste", "dime algo interesante", "estoy triste", "estoy feliz", "tengo sueño",
    "quién te creó", "cuál es tu propósito", "qué puedes hacer", "buenos días Layo", "buenas noches Jarvis", "gracias Layo", "eres genial", "hasta luego", "adiós"
]

VERBOS_VENTANAS = ["minimiza", "minimizar", "maximiza", "maximizar", "cierra", "cerrar", "bloquea", "bloquear", "abre el", "cambia de", "oculta", "muestra"]
OBJETIVOS_VENTANAS = ["la ventana", "ventana", "todas las ventanas", "todo", "el equipo", "la pc", "el computador", "el administrador de tareas", "procesos", "pestaña", "pantalla"]

VERBOS_NOTAS = ["crea una nota que diga", "crea nota que diga", "toma una nota que diga", "toma nota de", "escribe una nota que diga", "guarda una nota de", "anota", "apunta"]
TEMAS_NOTAS = ["comprar pan", "ir a entrenar", "recordar la reunión", "estudiar programación", "comprar manzanas", "llamar al jefe", "hacer la comida", "hola mundo", "terminar el proyecto"]
FRASES_LEER_NOTAS = ["lee mis notas", "muestra mis notas", "dime mis notas", "lee las notas", "cuáles son mis notas", "léeme las notas", "muéstrame las notas de hoy"]

VERBOS_WEB = ["busca en google", "buscar en google", "busca en internet", "buscar en internet", "busca información de", "busca informacion sobre", "investiga sobre", "googlea"]
TEMAS_WEB = ["cómo hacer un pastel de chocolate", "quién es el creador de python", "el clima en madrid", "noticias de hoy", "el precio del bitcoin", "cuándo juega el real madrid", "la teoría de la relatividad", "películas recomendadas"]

VERBOS_VISION = ["analiza", "analizar", "mira", "mirar", "qué hay en", "explícame qué hay en", "observa", "observar"]
OBJETIVOS_VISION = ["mi pantalla", "la pantalla", "mi monitor", "el monitor", "mi cámara", "la cámara", "mi webcam", "la webcam"]

# =====================================================================
# SIMULADOR DE ESCENARIOS (RUIDO Y ERRORES)
# =====================================================================
def generar_variaciones_ruido(texto):
    palabras = texto.split()
    variaciones = []
    
    # Reemplazos fonéticos comunes y errores de tipeo detectados
    reemplazos = {
        "downloads": ["daunlos", "daunlas", "danlas", "downla", "daonlas", "daonlos"],
        "desktop": ["destop", "de stop", "destap"],
        "documents": ["dokiuments", "documens"],
        "pictures": ["picshurs", "pichurs"],
        "music": ["miusic", "musi"],
        "steam": ["estim", "es tim", "istim", "istín"],
        "chrome": ["crome", "crom", "croma", "chrim"],
        "discord": ["discor", "discol", "disco"],
        "whatsapp": ["wasap", "guatsap", "watsap"],
        "spotify": ["espotifai", "spotifai", "espotify"]
    }
    
    # 1. Aplicar ruido fonético
    for i in range(len(palabras)):
        p = palabras[i].lower()
        if p in reemplazos:
            for r in reemplazos[p]:
                nueva_frase = palabras.copy()
                nueva_frase[i] = r
                variaciones.append(" ".join(nueva_frase))
                
    # 2. Simular errores de tipeo (letras duplicadas)
    if len(palabras) > 1:
        nueva_frase = palabras.copy()
        idx = random.randint(0, len(palabras) - 1)
        w = nueva_frase[idx]
        if len(w) > 4:
            char_idx = random.randint(0, len(w) - 1)
            w_noisy = w[:char_idx] + w[char_idx] + w[char_idx:]
            nueva_frase[idx] = w_noisy
            variaciones.append(" ".join(nueva_frase))
            
    return list(set(variaciones))

# =====================================================================
# GENERADOR Y ENTRENADOR NEURONAL
# =====================================================================
def generar_dataset():
    datos_base = []
    
    # 0: abrir_carpeta
    for v in VERBOS_CARPETA:
        for c in CARPETAS:
            datos_base.append((f"{v} {c}", 0))
                
    # 1: abrir_app
    for v in VERBOS_APP:
        for a in APPS:
            datos_base.append((f"{v} {a}", 1))
 
    # 2: reproducir_media
    for v in VERBOS_MEDIA:
        for t in TEMAS_MEDIA:
            for c in CONECTORES_MEDIA:
                datos_base.append((f"{v} {t} {c}".strip(), 2))
 
    verbos_busca_media = ["busca", "buscar"]
    conectores_busca_media = ["en spotify", "de spotify", "en youtube", "de youtube", "en yotube", "en iutub"]
    for v in verbos_busca_media:
        for t in TEMAS_MEDIA:
            for c in conectores_busca_media:
                datos_base.append((f"{v} {t} {c}".strip(), 2))
 
    # 3: volumen
    for v in VERBOS_VOLUMEN:
        for c in COMPLEMENTOS_VOLUMEN:
            frase = f"{v} {c}".strip()
            if len(frase) > 2:
                datos_base.append((frase, 3))
 
    # 4: captura
    for v in VERBOS_CAPTURA:
        for t in TEMAS_CAPTURA:
            datos_base.append((f"{v} {t}".strip(), 4))
 
    # 5: escribir_codigo
    for v in VERBOS_CODIGO:
        for t in TEMAS_CODIGO:
            datos_base.append((f"{v} {t}".strip(), 5))
 
    # 6: conversacion
    for f in FRASES_CONVERSACION:
        datos_base.append((f, 6))
 
    # 7: control_ventanas
    for v in VERBOS_VENTANAS:
        for o in OBJETIVOS_VENTANAS:
            datos_base.append((f"{v} {o}".strip(), 7))
 
    # 8: gestion_notas
    for v in VERBOS_NOTAS:
        for t in TEMAS_NOTAS:
            datos_base.append((f"{v} {t}".strip(), 8))
    for f in FRASES_LEER_NOTAS:
        datos_base.append((f, 8))
 
    # 9: busqueda_web
    for v in VERBOS_WEB:
        for t in TEMAS_WEB:
            datos_base.append((f"{v} {t}".strip(), 9))

    # 10: analizar_pantalla
    for v in VERBOS_VISION:
        for o in OBJETIVOS_VISION:
            datos_base.append((f"{v} {o}".strip(), 10))
 
    # Mezcladores combinatorios gigantescos para escalar a más de 1,000,000 de escenarios únicos
    saludos = ["hola", "buenas", "buenos días", "buenas noches", "oye", "escucha", "hey", "estimado layo", "querido jarvis", "computadora", "layo", "jarvis"]
    peticiones = ["por favor", "serías tan amable de", "podrías", "necesito que", "quiero que", "hazme el favor de", "procede a", "de inmediato"]
    cortesias_finales = ["gracias", "muchas gracias", "por favor", "ya mismo", "ahora", "inmediatamente", "cuando puedas", "amigo", "de inmediato", "lo antes posible"]
    
    datos_unicos = {}
    
    # Primero agregar todos los base
    for frase, clase in datos_base:
        datos_unicos[frase.lower().strip()] = clase
        
    # Aplicar expansión sistemática/aleatoria hasta superar los 1,000,000 de escenarios únicos
    random.seed(42) # Semilla constante para reproducibilidad
    
    intentos = 0
    max_intentos = 10000000 # Límite para evitar bucles infinitos
    
    while len(datos_unicos) < 1010000 and intentos < max_intentos:
        intentos += 1
        # Tomar un elemento base aleatorio
        frase_base, clase = random.choice(datos_base)
        
        # Aplicar combinaciones de saludos, peticiones o cortesías
        modificador = random.randint(1, 7)
        
        if modificador == 1:
            nueva_frase = f"{random.choice(saludos)} {frase_base}"
        elif modificador == 2:
            nueva_frase = f"{frase_base} {random.choice(cortesias_finales)}"
        elif modificador == 3:
            nueva_frase = f"{random.choice(peticiones)} {frase_base}"
        elif modificador == 4:
            nueva_frase = f"{random.choice(saludos)} {random.choice(peticiones)} {frase_base}"
        elif modificador == 5:
            nueva_frase = f"{random.choice(saludos)} {frase_base} {random.choice(cortesias_finales)}"
        elif modificador == 6:
            nueva_frase = f"{random.choice(peticiones)} {frase_base} {random.choice(cortesias_finales)}"
        else:
            nueva_frase = f"{random.choice(saludos)} {random.choice(peticiones)} {frase_base} {random.choice(cortesias_finales)}"
            
        nueva_frase_normalizada = nueva_frase.lower().strip()
        if nueva_frase_normalizada not in datos_unicos:
            datos_unicos[nueva_frase_normalizada] = clase
            
    datos = [(f, c) for f, c in datos_unicos.items()]
    random.shuffle(datos)
    return datos

def entrenar_modelo():
    limpiar_pantalla()
    print(f"{Fore.CYAN}{Fore.BOLD}")
    print("   ==================================================================")
    print("     _          /\\      __   __  ____  ")
    print("    | |        /  \\     \\ \\ / / / __ \\ ")
    print("    | |       / /\\ \\     \\ V / | |  | |")
    print("    | |      / ____ \\     | |  | |  | |")
    print("    | |____ /_/    \\_\\    |_|  \\ |__| |")
    print("    |______|              (_)   \\____/ ")
    print("   ==================================================================")
    print("               NÚCLEO NEURONAL DE APRENDIZAJE AUTÓNOMO (ML CENTRAL)")
    print("   ==================================================================")
    print(f"{Fore.RESET}")

    # 1. Generar dataset combinatorio
    print(f"{Fore.CYAN}[1/5] Compilando conjunto de datos semánticos...{Fore.RESET}")
    datos_completos = generar_dataset()
    print(f"{Fore.GREEN}--> Generadas exitosamente {len(datos_completos)} frases sintéticas únicas.{Fore.RESET}")
    
    # 2. Vectorizar y preparar datos
    print(f"\n{Fore.CYAN}[2/5] Fiteando vocabulario y estructurando vectores...{Fore.RESET}")
    textos = [d[0] for d in datos_completos]
    etiquetas = [d[1] for d in datos_completos]
    
    vectorizador = VectorizadorSimple()
    vectorizador.fit(textos)
    tamano_vocab = len(vectorizador.vocabulario)
    print(f"{Fore.GREEN}--> Vocabulario fiteado. Tamaño del vector de entrada: {tamano_vocab} palabras.{Fore.RESET}")
    
    # Transformar a tensores
    X_data = np.array([vectorizador.transform(t) for t in textos])
    y_data = np.array(etiquetas)
    
    # Separación Entrenamiento / Validación (80% / 20%)
    split_idx = int(len(X_data) * 0.8)
    
    X_train = torch.tensor(X_data[:split_idx], dtype=torch.float32)
    y_train = torch.tensor(y_data[:split_idx], dtype=torch.long)
    X_val = torch.tensor(X_data[split_idx:], dtype=torch.float32)
    y_val = torch.tensor(y_data[split_idx:], dtype=torch.long)
    
    # 3. Inicializar Red Neuronal Profunda
    print(f"\n{Fore.CYAN}[3/5] Inicializando capas lineales de la Red Neuronal PyTorch (MLP 64-32)...{Fore.RESET}")
    tamano_salida = 11 # 11 intenciones
    modelo = ClasificadorIntencion(tamano_vocab, tamano_salida)
    
    criterio = nn.CrossEntropyLoss()
    optimizador = optim.Adam(modelo.parameters(), lr=0.003)
    
    # Bucle de aprendizaje autónomo optimizado con Mini-Batches (1,000,000+ muestras)
    print(f"\n{Fore.CYAN}[4/5] Invocando optimizador de descenso de gradiente (Adam)...{Fore.RESET}")
    print(f"{Fore.WHITE}Entrenando en mini-lotes (batch size: 8192) para alto rendimiento.{Fore.RESET}")
    
    from torch.utils.data import DataLoader, TensorDataset
    dataset_train = TensorDataset(X_train, y_train)
    loader_train = DataLoader(dataset_train, batch_size=8192, shuffle=True)
    
    epochs = 15
    t_inicio = time.time()
    
    try:
        mejor_val_acc = 0.0
        
        for epoch in range(1, epochs + 1):
            modelo.train()
            epoch_loss = 0.0
            
            for X_batch, y_batch in loader_train:
                optimizador.zero_grad()
                outputs = modelo(X_batch)
                loss = criterio(outputs, y_batch)
                loss.backward()
                optimizador.step()
                epoch_loss += loss.item() * len(X_batch)
                
            epoch_loss /= len(X_train)
            
            # Validación rápida al final de cada época
            modelo.eval()
            with torch.no_grad():
                val_outputs = modelo(X_val)
                val_loss = criterio(val_outputs, y_val)
                _, predichos = torch.max(val_outputs, dim=1)
                val_acc = (predichos == y_val).sum().item() / len(y_val)
                
                # Guardar si es el mejor modelo
                if val_acc > mejor_val_acc:
                    mejor_val_acc = val_acc
                    torch.save(modelo.state_dict(), "modelo_layo.pth")
                    vectorizador.guardar("vocabulario_layo.json")
            
            # Barra de progreso Stark visual en consola
            ancho_barra = 20
            progreso = int((epoch / epochs) * ancho_barra)
            barra = f"[{'=' * progreso}{' ' * (ancho_barra - progreso)}]"
            
            sys.stdout.write(
                f"\r{Fore.CYAN}Época {epoch:2d}/{epochs} {Fore.WHITE}{barra} "
                f"| Pérdida: {epoch_loss:.4f} "
                f"| Val Loss: {val_loss.item():.4f} "
                f"| {Fore.GREEN}Val Acc: {val_acc:.1%}{Fore.RESET}    "
            )
            sys.stdout.flush()
                
        t_total = time.time() - t_inicio
        print(f"\n\n{Fore.GREEN}[Base OK] Modelo base optimizado con éxito en {t_total:.1f} segundos.{Fore.RESET}")
        print(f"{Fore.GREEN}--> Precisión de validación de base lograda: {mejor_val_acc:.2%}{Fore.RESET}")
        
        # 5. FASE DE AUTO-APRENDIZAJE ADVERSARIO AUTÓNOMO
        print(f"\n{Fore.MAGENTA}{Fore.BOLD}⚡ [5/5] INICIANDO COMPRENSIÓN NEURONAL ADVERSARIA (AUTO-APRENDIZAJE) ⚡{Fore.RESET}")
        print(f"{Fore.WHITE}Layo simulará escenarios ruidosos, evaluará sus propios fallos y los corregirá solo.{Fore.RESET}")
        print(f"{Fore.YELLOW}El ciclo se ejecutará continuamente para fortalecer las sinapsis locales...{Fore.RESET}")
        print(f"{Fore.YELLOW}Presione Ctrl+C en cualquier momento para consolidar pesos finales y salir.{Fore.RESET}\n")
        
        clases_ejemplo = [
            "abrir_carpeta", "abrir_app", "reproducir_media", "volumen", "captura", 
            "escribir_codigo", "conversacion", "control_ventanas", "gestion_notas", "busqueda_web", "analizar_pantalla"
        ]
        ciclo = 1
        
        while True:
            print(f"\n{Fore.CYAN}--- Ciclo de Simulación Autónoma #{ciclo} ---{Fore.RESET}")
            
            # A. Generar escenarios con ruido fonético y errores de tipeo
            print(f"{Fore.WHITE}[Simulador] Generando escenarios adversarios de prueba...{Fore.RESET}", end="", flush=True)
            escenarios_ruidosos = []
            for frase, clase_idx in datos_completos[:1000]:
                variaciones = generar_variaciones_ruido(frase)
                for var in variaciones:
                    escenarios_ruidosos.append((var, clase_idx))
            print(f" {Fore.GREEN}[OK] ({len(escenarios_ruidosos)} escenarios ruidosos creados).{Fore.RESET}")
            
            if not escenarios_ruidosos:
                time.sleep(2)
                continue
                
            # B. Evaluar el modelo actual sobre los escenarios con ruido
            modelo.eval()
            fallos = []
            exitos = 0
            
            with torch.no_grad():
                for frase_ruidosa, clase_idx in escenarios_ruidosos:
                    x_vec = vectorizador.transform(frase_ruidosa)
                    if np.linalg.norm(x_vec) == 0:
                        fallos.append((frase_ruidosa, clase_idx))
                        continue
                        
                    x_tensor = torch.tensor(x_vec, dtype=torch.float32).unsqueeze(0)
                    logits = modelo(x_tensor)
                    probabilidades = torch.softmax(logits, dim=1).squeeze().numpy()
                    
                    if probabilidades.ndim == 0:
                        pred_idx = 0
                        confianza = float(probabilidades)
                    else:
                        pred_idx = np.argmax(probabilidades)
                        confianza = probabilidades[pred_idx]
                    
                    if pred_idx == clase_idx and confianza >= 0.85:
                        exitos += 1
                    else:
                        fallos.append((frase_ruidosa, clase_idx))
            
            precision_ruido = exitos / len(escenarios_ruidosos)
            print(f"{Fore.WHITE}[Evaluador] Precisión en escenarios adversarios: {Fore.YELLOW}{precision_ruido:.1%}{Fore.RESET}")
            
            if fallos:
                print(f"{Fore.RED}[Auto-Corrector] Detectados {len(fallos)} fallos de confianza/clasificación en escenarios simulados.{Fore.RESET}")
                ejemplos = random.sample(fallos, min(len(fallos), 3))
                for frase_f, clase_f in ejemplos:
                    print(f"  {Fore.YELLOW}* Fallo de Simulación: '{frase_f}' (Clase esperada: {clases_ejemplo[clase_f]}){Fore.RESET}")
                
                # C. Entrenar el modelo focalizando específicamente los fallos (Active Learning)
                print(f"{Fore.BLUE}[Entrenador] Ejecutando mini-bach de retropropagación focalizado...{Fore.RESET}")
                modelo.train()
                
                X_fallos = torch.tensor(np.array([vectorizador.transform(f[0]) for f in fallos]), dtype=torch.float32)
                y_fallos = torch.tensor(np.array([f[1] for f in fallos]), dtype=torch.long)
                
                # optimizador para fallos
                optimizador_fallos = optim.Adam(modelo.parameters(), lr=0.002)
                for _ in range(80):
                    optimizador_fallos.zero_grad()
                    out_fallos = modelo(X_fallos)
                    loss_fallos = criterio(out_fallos, y_fallos)
                    loss_fallos.backward()
                    optimizador_fallos.step()
                    
                torch.save(modelo.state_dict(), "modelo_layo.pth")
                print(f"{Fore.GREEN}[Auto-Corrector] Modelo auto-optimizado y guardado con éxito.{Fore.RESET}")
            else:
                print(f"{Fore.GREEN}[Auto-Corrector] ¡Layo ha clasificado el 100% de escenarios adversarios a la perfección!{Fore.RESET}")
                
            ciclo += 1
            time.sleep(4.0)

    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}[Auto-Estudio Finalizado] Pesos neuronalmente consolidados y optimizados.{Fore.RESET}")
        print(f"{Fore.CYAN}Sistemas listos y pesos exportados en caliente.{Fore.RESET}\n")

if __name__ == "__main__":
    entrenar_modelo()
