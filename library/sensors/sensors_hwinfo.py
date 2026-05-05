import re
import mmap
import struct

from library.log import logger

class HWInfo:
    def __init__(self):
        self.shmem_name = r"Global\HWiNFO_SENS_SM2"
        self._sensor_data = {}

    def _read_shared_memory(self):
        try:
            with mmap.mmap(-1, 0x2C, self.shmem_name, mmap.ACCESS_READ) as mm:
                h = struct.unpack('<IIIqIIIIII', mm.read(0x2C))

                # Bloque de Sensores (Padres)
                sens_off, sens_size, sens_cnt = h[4], h[5], h[6]
                # Bloque de Lecturas (Hijos)
                read_off, read_size, read_cnt = h[7], h[8], h[9]
                total_size = read_off + (read_size * read_cnt)

            with mmap.mmap(-1, total_size, self.shmem_name, mmap.ACCESS_READ) as mm:
                # 1. Leer nombres de Padres
                sensor_names = []
                for i in range(sens_cnt):
                    offset = sens_off + (i * sens_size)
                    s_name_raw = struct.unpack_from('128s', mm, offset + 8)[0]
                    s_name = s_name_raw.split(b'\x00')[0].decode('utf-8', 'ignore')
                    sensor_names.append(s_name)

                # 2. Leer Lecturas Hijos
                for i in range(read_cnt):
                    offset = read_off + (i * read_size)

                    # El índice del padre empieza en el offset 4
                    parent_idx = struct.unpack_from('<I', mm, offset + 4)[0]

                    name_raw = struct.unpack_from('128s', mm, offset + 12)[0]
                    reading_name = name_raw.split(b'\x00')[0].decode('utf-8', 'ignore')
                    value = struct.unpack_from('<d', mm, offset + 284)[0]

                    # GUARDADO 1: Nombre corto intacto (ej. "CPU Package")
                    self._sensor_data[reading_name] = value

                    # GUARDADO 2: Nombre combinado
                    if parent_idx < len(sensor_names):
                        full_name = f"{sensor_names[parent_idx]} - {reading_name}"
                        self._sensor_data[full_name] = value

        except Exception as e:
            logger.debug(f"Error al leer la memoria compartida de HWiNFO: {e}")
            self._sensor_data = {}

    def get_sensor_value(self, sensor_name: str) -> float:
        self._read_shared_memory()
        return self._sensor_data.get(sensor_name, 0.0)

    def get_disk_activity_info(self) -> dict:
        self._read_shared_memory()
        max_activity = -1.0
        current_disk_letter = "N/A"
        current_disk_number = "N/A"
        fallback_name = "N/A"
        best_parent_name = None  # disco ganador

        for name, value in self._sensor_data.items():
            if name.endswith(" - Total Activity") or name.endswith(" - Drive Activity"):
                # Extraemos el nombre del padre (quitando la parte de " - Total Activity")
                parent_name = name.rsplit(" - ", 1)[0]

                match_letter = re.search(r'[\[\(]([A-Za-z]:)[\]\)]', name)
                match_number = re.search(r'[\[\(]Disk (\d+)[\]\)]', name)

                if match_letter or match_number:
                    if value > max_activity:
                        max_activity = value
                        best_parent_name = parent_name  # Guardamos el nombre del disco
                        if match_letter:
                            current_disk_letter = match_letter.group(1)
                            current_disk_number = "N/A"
                        elif match_number:
                            current_disk_number = match_number.group(1)
                            current_disk_letter = "N/A"
                else:
                    if "S.M.A.R.T." in name or "Drive:" in name:
                        if value > max_activity:
                            max_activity = value
                            best_parent_name = parent_name  # Guardamos el nombre del disco
                            fallback_name = "Activo"

        final_activity = max(max_activity, 0.0)

        if final_activity > 0.0 and current_disk_letter == "N/A" and current_disk_number == "N/A":
            current_disk_number = fallback_name

        # lectura y escritura exacta de ESE disco:
        read_rate = 0.0
        write_rate = 0.0
        if best_parent_name:
            read_rate = self._sensor_data.get(f"{best_parent_name} - Read Rate", 0.0)
            write_rate = self._sensor_data.get(f"{best_parent_name} - Write Rate", 0.0)

        return {
            "letter": current_disk_letter,
            "number": current_disk_number,
            "activity": final_activity,
            "read_rate": read_rate,   # Suele venir en MB/s
            "write_rate": write_rate  # Suele venir en MB/s
        }

    def get_cpu_sensor_value(self, reading_name: str) -> float:
        """Encuentra un sensor ignorando al Padre, buscando solo el final del nombre."""
        self._read_shared_memory()

        target = f" - {reading_name}"

        # 1. Búsqueda exacta: Busca cualquier sensor que termine en " - Core VIDs"
        for full_name, value in self._sensor_data.items():
            if full_name.endswith(target):
                # Descomenta esto si quieres ver en el log quién era el verdadero Padre
                # logger.debug(f"¡Cazado! Sensor exacto: '{full_name}' = {value}")
                return value

        # 2. Búsqueda flexible: Por si HWiNFO le pone algún espacio raro al final
        for full_name, value in self._sensor_data.items():
            if reading_name in full_name:
                # logger.debug(f"Cazado por aproximación: '{full_name}' = {value}")
                return value

        # 3. Fallback de seguridad
        logger.debug(f"No se ha encontrado el sensor: '{reading_name}'")
        return 0.0