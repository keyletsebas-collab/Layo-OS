import sqlite3
import os
import time
import requests
from datetime import datetime

DB_PATH = "layo_agent_memory.db"

class AgenteAprendizaje:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.inicializar_db()

    def obtener_conexion(self):
        return sqlite3.connect(self.db_path)

    def inicializar_db(self):
        """Crea las tablas de base de datos SQLite si no existen"""
        with self.obtener_conexion() as conn:
            cursor = conn.cursor()
            
            # Tabla de Registro de Errores y Autocorrecciones Aprendidas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS registro_errores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contexto_error TEXT NOT NULL,
                    comando_original TEXT NOT NULL,
                    comando_corregido TEXT,
                    explicacion_solucion TEXT,
                    fecha_creacion TEXT NOT NULL,
                    conteo_exito INTEGER DEFAULT 1
                )
            ''')
            
            # Tabla de Memoria Semántica del Usuario (Preferencias, gustos, etc.)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS memoria_usuario (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    categoria TEXT NOT NULL,
                    clave TEXT NOT NULL,
                    valor TEXT NOT NULL,
                    fecha_actualizacion TEXT NOT NULL,
                    UNIQUE(categoria, clave)
                )
            ''')
            
            conn.commit()

    def consultar_solucion(self, comando):
        """Busca si el comando falló en el pasado y devuelve la versión corregida aprendida"""
        comando_clean = comando.strip().lower()
        with self.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT comando_corregido, explicacion_solucion 
                FROM registro_errores 
                WHERE LOWER(comando_original) = ? OR LOWER(contexto_error) LIKE ?
                ORDER BY conteo_exito DESC, id DESC LIMIT 1
            ''', (comando_clean, f"%{comando_clean}%"))
            row = cursor.fetchone()
            if row and row[0]:
                return row[0], row[1]
        return None, None

    def registrar_error_y_aprender(self, contexto_error, comando_fallido, error_str, cerebro_ollama=None):
        """Utiliza Ollama para reflexionar sobre un error, encontrar la corrección y guardarla en SQLite"""
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        comando_corregido = comando_fallido
        explicacion = "Corrección automática por fallback del sistema."

        if cerebro_ollama and hasattr(cerebro_ollama, 'pensar'):
            prompt_reflexion = (
                f"Analiza este error de comando en el sistema de la computadora:\n"
                f"- Comando que falló: '{comando_fallido}'\n"
                f"- Contexto / Detalle del error: '{error_str}'\n"
                f"Dime cuál es el comando corregido para que no vuelva a fallar. "
                f"Responde estrictamente en formato JSON: {{\"comando_corregido\": \"...\", \"explicacion\": \"...\"}}"
            )
            try:
                res, _ = cerebro_ollama.pensar(prompt_reflexion)
                import json, re
                match = re.search(r'\{.*\}', res, re.DOTALL)
                if match:
                    data = json.loads(match.group(0))
                    comando_corregido = data.get("comando_corregido", comando_fallido)
                    explicacion = data.get("explicacion", explicacion)
            except Exception as e:
                print(f"[Agente Aprendizaje] Error al consultar Ollama para autoreflejo: {e}")

        with self.obtener_conexion() as conn:
            cursor = conn.cursor()
            # Verificar si ya existía para incrementar el conteo
            cursor.execute('''
                SELECT id, conteo_exito FROM registro_errores 
                WHERE LOWER(comando_original) = ?
            ''', (comando_fallido.strip().lower(),))
            row = cursor.fetchone()
            if row:
                cursor.execute('''
                    UPDATE registro_errores 
                    SET comando_corregido = ?, explicacion_solucion = ?, conteo_exito = conteo_exito + 1, fecha_creacion = ?
                    WHERE id = ?
                ''', (comando_corregido, explicacion, fecha, row[0]))
            else:
                cursor.execute('''
                    INSERT INTO registro_errores (contexto_error, comando_original, comando_corregido, explicacion_solucion, fecha_creacion)
                    VALUES (?, ?, ?, ?, ?)
                ''', (contexto_error, comando_fallido, comando_corregido, explicacion, fecha))
            conn.commit()

        print(f"\n[Auto-Aprendizaje] Error registrado y corregido en SQLite: '{comando_fallido}' -> '{comando_corregido}'")
        return comando_corregido

    def guardar_memoria(self, categoria, clave, valor):
        """Guarda o actualiza preferencias del usuario en SQLite"""
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO memoria_usuario (categoria, clave, valor, fecha_actualizacion)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(categoria, clave) DO UPDATE SET
                    valor = excluded.valor,
                    fecha_actualizacion = excluded.fecha_actualizacion
            ''', (categoria, clave, valor, fecha))
            conn.commit()

    def obtener_todas_memorias(self):
        """Retorna todas las memorias guardadas en SQLite"""
        with self.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT categoria, clave, valor, fecha_actualizacion FROM memoria_usuario ORDER BY categoria, clave')
            rows = cursor.fetchall()
            return [{"categoria": r[0], "clave": r[1], "valor": r[2], "fecha": r[3]} for r in rows]

    def obtener_historial_errores(self):
        """Retorna el historial de errores y soluciones de SQLite"""
        with self.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, contexto_error, comando_original, comando_corregido, explicacion_solucion, fecha_creacion, conteo_exito FROM registro_errores ORDER BY id DESC')
            rows = cursor.fetchall()
            return [{
                "id": r[0],
                "contexto": r[1],
                "original": r[2],
                "corregido": r[3],
                "explicacion": r[4],
                "fecha": r[5],
                "exitos": r[6]
            } for r in rows]

    def obtener_estadisticas_aprendizaje(self):
        with self.obtener_conexion() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM registro_errores')
            total_errores = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM memoria_usuario')
            total_memorias = cursor.fetchone()[0]
            return {
                "errores_aprendidos": total_errores,
                "memorias_registradas": total_memorias,
                "db_path": self.db_path,
                "db_tamano_bytes": os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            }
