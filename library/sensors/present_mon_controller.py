import subprocess
import threading
from library.log import logger

g_current_fps = 0.0
g_app_name = 'IDLE'
g_limiter = 'N/A'
g_latency = 0.0
g_api = 'N/A'
presentmont_started = False

class PresentMonController:
    def __init__(self):
        self._exe_path = "./external/PresentMon/PresentMon-2.4.1-x64.exe"
        self._blacklist = ["explorer", "WindowsTerminal", "dwm", "Code", "firefox"]
        self._start_monitoring()

    def _get_command(self):
        cmd = [self._exe_path, "--output_stdout", "--stop_existing_session"]
        return cmd

    def _process_line(self, parts):
        global g_current_fps, g_app_name, g_limiter, g_latency, g_api

        # Limpiamos el nombre que viene de PresentMon
        raw_app_name = parts[0].strip('"').lower()

        # Si el nombre está en la blacklist, ignoramos esta línea y salimos de la función
        if any(blacklisted.lower() in raw_app_name for blacklisted in self._blacklist):
            return

        # 1. Identificación básica
        app_name = parts[0].strip('"')

        logger.debug(f"Datos recibidos: App='{app_name}', API='{parts[3]}', msFrame={parts[10]}, msGPU={parts[13]}, Latency={parts[14]}")
        # 2. Extracción de datos (basada en tu output real)
        api = parts[3]              # DXGI
        ms_frame = float(parts[10]) # 1.777 (msBetweenPresents)
        ms_gpu = float(parts[13])   # 4.261 (msGpuActive)
        latency = float(parts[14])  # 4.963 (msUntilDisplayed)

        if ms_frame > 0:
            # 3. FPS e Indicador
            current_fps = round(1000.0 / ms_frame, 1)

            # Ratio GPU/CPU
            ratio = ms_gpu / ms_frame
            if ratio > 0.95: limiter = "GPU"
            elif ratio < 0.70: limiter = "CPU"
            else: limiter = "BAL"

            g_app_name = app_name.replace(".exe", "")#[:8]
            g_api = api
            g_limiter = limiter
            g_latency = latency
            g_current_fps = current_fps

    def _start_monitoring(self):
        global presentmont_started
        def run():
            cmd = self._get_command()

            try:
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, creationflags=subprocess.CREATE_NO_WINDOW)

                logger.info(f"PresentMon started with PID {proc.pid}")

                for line in proc.stdout:
                    # Limpieza inicial de la línea
                    line = line.strip()
                    if not line:
                        continue

                    parts = line.split(',')
                    # Verificamos que tenga las columnas necesarias (al menos 15)
                    if len(parts) >= 15:
                        try:
                            self._process_line(parts)

                        except (ValueError, IndexError):
                            continue
            except Exception as e:
                logger.error(f"Error al iniciar o procesar salida PresentMon: {e}")

        if not presentmont_started:
            presentmont_started = True
            threading.Thread(target=run, daemon=True).start()

    def get_current_metrics(self):
        return {
            "app_name": g_app_name,
            "api": g_api,
            "fps": g_current_fps,
            "limiter": g_limiter,
            "latency": g_latency
        }