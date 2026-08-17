import http.server
import socketserver
import json
import os
import requests
import threading
import time
import webbrowser
from urllib.parse import parse_qs, urlparse
from agente_aprendizaje import AgenteAprendizaje

PORT = 5000

# Inicialización diferida del cerebro y motor de voz de Layo
cerebro_global = None
voz_global = None

def obtener_cerebro():
    global cerebro_global
    if cerebro_global is None:
        try:
            from sistema_layo import CerebroJarvis
            cerebro_global = CerebroJarvis()
        except Exception as e:
            print(f"[GUI Cerebro Init Error]: {e}")
    return cerebro_global

def obtener_voz():
    global voz_global
    if voz_global is None:
        try:
            from sistema_layo import MotorVocal
            voz_global = MotorVocal()
        except Exception as e:
            print(f"[GUI Voz Init Error]: {e}")
    return voz_global


class LayoGUIHandler(http.server.BaseHTTPRequestHandler):
    agente = AgenteAprendizaje()

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/" or parsed.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            template_path = os.path.join("templates", "index.html")
            if os.path.exists(template_path):
                with open(template_path, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.wfile.write(b"<h1>Plantilla no encontrada</h1>")
        
        elif parsed.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            ollama_activo = False
            modelos_ollama = []
            try:
                r = requests.get("http://localhost:11434/api/tags", timeout=2)
                if r.status_code == 200:
                    ollama_activo = True
                    models_data = r.json().get("models", [])
                    modelos_ollama = [m.get("name") for m in models_data]
            except Exception:
                ollama_activo = False

            voces_onnx = [f for f in os.listdir(".") if f.endswith(".onnx")]
            if os.path.exists("Voz"):
                for root, _, files in os.walk("Voz"):
                    for f in files:
                        if f.endswith(".onnx"):
                            voces_onnx.append(os.path.join(root, f))

            stats = self.agente.obtener_estadisticas_aprendizaje()

            payload = {
                "ollama_activo": ollama_activo,
                "modelos_ollama": modelos_ollama,
                "modelo_llm": modelos_ollama[0] if modelos_ollama else "qwen2.5:1.5b (Servidor Offline)",
                "voz_onnx": voces_onnx[0] if voces_onnx else "es_ES-sharvard-medium.onnx",
                "voces_disponibles": voces_onnx,
                "errores_aprendidos": stats["errores_aprendidos"],
                "memorias_registradas": stats["memorias_registradas"],
                "db_bytes": stats["db_tamano_bytes"]
            }
            self.wfile.write(json.dumps(payload).encode("utf-8"))

        elif parsed.path == "/api/learning":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            data = self.agente.obtener_historial_errores()
            self.wfile.write(json.dumps(data).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        body_bytes = self.rfile.read(content_length) if content_length > 0 else b""
        
        try:
            data = json.loads(body_bytes.decode('utf-8')) if body_bytes else {}
        except Exception:
            data = {}

        if parsed.path == "/api/chat":
            mensaje = data.get("mensaje", "")
            cerebro = obtener_cerebro()
            voz = obtener_voz()
            
            respuesta_texto = "Señor, estoy procesando su solicitud..."
            accion = None
            
            if cerebro:
                res_ai, acc_ai = cerebro.pensar(mensaje)
                if res_ai:
                    respuesta_texto = res_ai
                    accion = acc_ai

            # Si hay una acción de sistema solicitada por la IA
            if accion:
                try:
                    from sistema_layo import ejecutar_comando_sistema, escuchar
                    res_cmd = ejecutar_comando_sistema(accion, voz, escuchar, cerebro=cerebro)
                    if res_cmd:
                        respuesta_texto += f" {res_cmd}"
                except Exception as e:
                    print(f"[GUI Action Error]: {e}")

            # Hacer que Layo hable la respuesta por los altavoces en un hilo separado
            if voz and respuesta_texto:
                threading.Thread(target=lambda: voz.hablar(respuesta_texto), daemon=True).start()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"respuesta": respuesta_texto}).encode("utf-8"))

        elif parsed.path == "/api/test_voice":
            voz = obtener_voz()
            if voz:
                threading.Thread(target=lambda: voz.hablar("Señor. Motor vocal Piper ONNX verificado y funcionando sin conexión."), daemon=True).start()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

def iniciar_servidor_gui():
    url_gui = f"http://localhost:{PORT}"
    print(f"\n==========================================================================")
    print(f"  [GUI Web] ABRIENDO INTERFAZ GRÁFICA EN EL NAVEGADOR: {url_gui}")
    print(f"==========================================================================")
    
    def abrir_navegador():
        time.sleep(1)
        try:
            webbrowser.open(url_gui)
        except Exception:
            pass

    threading.Thread(target=abrir_navegador, daemon=True).start()

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), LayoGUIHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[GUI Web] Servidor finalizado.")

if __name__ == "__main__":
    iniciar_servidor_gui()
