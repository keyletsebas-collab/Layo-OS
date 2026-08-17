import time
import os
import sys

print("==========================================================================")
print("  LAYO-OS: MOTOR DE ENTRENAMIENTO CONTINUO E INTELIGENCIA INFINITA")
print("==========================================================================")
print("[Daemon]: Iniciando ciclo infinito de auto-perfeccionamiento y red neuronal...")

ciclo = 1
while True:
    print(f"\n---> Ejecutando Sesión Intensiva de Auto-Estudio #{ciclo} <---")
    os.system("python3 entrenar_layo.py")
    ciclo += 1
    time.sleep(3)
