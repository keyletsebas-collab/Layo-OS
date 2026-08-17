import torch
import sounddevice as sd

print("[Inicializando núcleo neuronal de audio...]")
print("[Si es la primera vez, descargará el modelo de voz silenciosamente]")

# 1. Cargar el modelo táctico de Silero (Español)
device = torch.device('cpu')
torch.set_num_threads(4) # Usa 4 hilos de tu procesador para que sea veloz

# Descarga/Carga el modelo directamente desde el repositorio oficial
modelo, textos_ejemplo = torch.hub.load(repo_or_dir='snakers4/silero-models',
                                     model='silero_tts',
                                     language='es',
                                     speaker='v3_es')
modelo.to(device)

# 2. Función de habla neuronal
def hablar_natural(texto):
    print(f"\nLayono: {texto}")
    # Genera el audio usando la voz "es_1" (puedes cambiar a es_0 o es_2 para tonos distintos)
    audio = modelo.apply_tts(text=texto,
                             speaker='es_1', 
                             sample_rate=48000)
    
    # Reproduce el audio al instante
    sd.play(audio.numpy(), samplerate=48000)
    sd.wait()

# 3. Prueba de fuego
hablar_natural("Señor, sistemas de voz táctica en línea. Confirmando latencia cero y operabilidad sin conexión a la red.")
hablar_natural("¿Qué le parece el nuevo sistema de comunicación?")