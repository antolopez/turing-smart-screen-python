# SPDX-License-Identifier: GPL-3.0-or-later
#
# turing-smart-screen-python - a Python system monitor and library for USB-C displays like Turing Smart Screen or XuanFang
# https://github.com/mathoudebine/turing-smart-screen-python/
#
# Copyright (C) 2021 Matthieu Houdebine (mathoudebine)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# This file allows to add custom data source as sensors and display them in System Monitor themes
# There is no limitation on how much custom data source classes can be added to this file
# See CustomDataExample theme for the theme implementation part

import math
import platform
from abc import ABC, abstractmethod
from typing import List
from PIL import Image
from library.sensors.windows_media_controller import WindowsMediaController
from library.sensors.plex_media_controller import PlexMediaController
from library.sensors.present_mon_controller import PresentMonController
from library.sensors.sensors_hwinfo import HWInfo
import library.config as config
import re


# Custom data classes must be implemented in this file, inherit the CustomDataSource and implement its 2 methods
class CustomDataSource(ABC):
    @abstractmethod
    def as_numeric(self) -> float:
        # Numeric value will be used for graph and radial progress bars
        # If there is no numeric value, keep this function empty
        pass

    @abstractmethod
    def as_string(self) -> str:
        # Text value will be used for text display and radial progress bar inner text
        # Numeric value can be formatted here to be displayed as expected
        # It is also possible to return a text unrelated to the numeric value
        # If this function is empty, the numeric value will be used as string without formatting
        pass

    @abstractmethod
    def last_values(self) -> List[float]:
        # List of last numeric values will be used for plot graph
        # If you do not want to draw a line graph or if your custom data has no numeric values, keep this function empty
        pass


# Example for a custom data class that has numeric and text values
class ExampleCustomNumericData(CustomDataSource):
    # This list is used to store the last 10 values to display a line graph
    last_val = [math.nan] * 10  # By default, it is filed with math.nan values to indicate there is no data stored

    def as_numeric(self) -> float:
        # Numeric value will be used for graph and radial progress bars
        # Here a Python function from another module can be called to get data
        # Example: self.value = my_module.get_rgb_led_brightness() / audio.system_volume() ...
        self.value = 75.845

        # Store the value to the history list that will be used for line graph
        self.last_val.append(self.value)
        # Also remove the oldest value from history list
        self.last_val.pop(0)

        return self.value

    def as_string(self) -> str:
        # Text value will be used for text display and radial progress bar inner text.
        # Numeric value can be formatted here to be displayed as expected
        # It is also possible to return a text unrelated to the numeric value
        # If this function is empty, the numeric value will be used as string without formatting
        # Example here: format numeric value: add unit as a suffix, and keep 1 digit decimal precision
        return f'{self.value:>5.1f}%'
        # Important note! If your numeric value can vary in size, be sure to display it with a default size.
        # E.g. if your value can range from 0 to 9999, you need to display it with at least 4 characters every time.
        # --> return f'{self.as_numeric():>4}%'
        # Otherwise, part of the previous value can stay displayed ("ghosting") after a refresh

    def last_values(self) -> List[float]:
        # List of last numeric values will be used for plot graph
        return self.last_val


# Example for a custom data class that only has text values
class ExampleCustomTextOnlyData(CustomDataSource):
    def as_numeric(self) -> float:
        # If there is no numeric value, keep this function empty
        pass

    def as_string(self) -> str:
        # If a custom data class only has text values, it won't be possible to display graph or radial bars
        return "Python: " + platform.python_version()

    def last_values(self) -> List[float]:
        # If a custom data class only has text values, it won't be possible to display line graph
        pass

class NowPlayingWindowsTrack(CustomDataSource):
    def __init__(self):
        self.media_controller = WindowsMediaController()
        self.update_info()

    def update_info(self):
        """Actualiza la información del medio actual"""
        self.media_info = self.media_controller.get_media_info()

    def as_numeric(self) -> float:
        pass

    def as_string(self) -> str:
        return self.media_info.title

    def as_image(self) -> Image:
        return self.media_info.thumbnail

    def last_values(self) -> List[float]:
        pass

class NowPlayingWindowsTimeline(CustomDataSource):
    def __init__(self):
        self.media_controller = WindowsMediaController()
        self.update_info()

    def update_info(self):
        """Actualiza la información del medio actual"""
        self.media_info = self.media_controller.get_media_info()

    def as_numeric(self) -> float:
        return self.media_info.progress

    def as_string(self) -> str:
        return f"{self.media_info.position_str} / {self.media_info.duration_str}"

    def as_image(self) -> Image:
        pass

    def last_values(self) -> List[float]:
        pass

class NowPlayingWindowsTrackInfo(CustomDataSource):
    def __init__(self):
        self.media_controller = WindowsMediaController()
        self.update_info()

    def update_info(self):
        """Actualiza la información del medio actual"""
        self.media_info = self.media_controller.get_media_info()

    def as_numeric(self) -> float:
        pass

    def as_string(self) -> str:
        track_number_info = f"Pista {self.media_info.track_number} de {self.media_info.total_tracks}"
        return f"{self.media_info.album} \n {self.media_info.album_artist} \n {self.media_info.genre} \n \n Interprete: {self.media_info.artist} \n {track_number_info}"

    def as_image(self) -> Image:
        pass

    def last_values(self) -> List[float]:
        pass

class NowPlayingWindowsPlayer(CustomDataSource):
    def __init__(self):
        self.media_controller = WindowsMediaController()
        self.update_info()

    def update_info(self):
        """Actualiza la información del medio actual"""
        self.media_info = self.media_controller.get_media_info()

    def as_numeric(self) -> float:
        pass

    def as_string(self) -> str:
        if (not self.media_info.custom_data):
            return 'Desconocido'
        app = self.media_info.custom_data.get('application', 'Desconocido')
        # Usando regex para coger todo hasta el primer punto
        app = re.split(r'\.', app)[0]
        return f"{app}"

    def as_image(self) -> Image:
        pass

    def last_values(self) -> List[float]:
        pass

class NowPlayingPlexTrack(CustomDataSource):
    def __init__(self):
        media_config = config.CONFIG_DATA.get('media_providers', {})
        plex_config = media_config.get('plex', {})
        product = plex_config.get('product', 'Plexamp')
        profile = plex_config.get('profile', 'Windows')
        device = plex_config.get('device', None)
        custom_interval = config.THEME_DATA['STATS']['CUSTOM'].get("INTERVAL", 5)
        self.media_controller = PlexMediaController(plex_config.get('url'),  plex_config.get('token'), product, profile, device, custom_interval)
        self.update_info()

    def update_info(self):
        """Actualiza la información del medio actual"""
        self.media_info = self.media_controller.get_media_info()

    def as_numeric(self) -> float:
        self.update_info()
        return self.media_info.progress

    def as_string(self) -> str:
        self.update_info()
        return self.media_info.title

    def as_image(self) -> Image:
        self.update_info()
        return self.media_info.thumbnail

    def last_values(self) -> List[float]:
        pass

class NowPlayingPlexTrackRating(CustomDataSource):
    def __init__(self):
        media_config = config.CONFIG_DATA.get('media_providers', {})
        plex_config = media_config.get('plex', {})
        product = plex_config.get('product', 'Plexamp')
        profile = plex_config.get('profile', 'Windows')
        device = plex_config.get('device', None)
        custom_interval = config.THEME_DATA['STATS']['CUSTOM'].get("INTERVAL", 5)
        self.media_controller = PlexMediaController(plex_config.get('url'),  plex_config.get('token'), product, profile, device, custom_interval)
        self.update_info()

    def update_info(self):
        """Actualiza la información del medio actual"""
        self.media_info = self.media_controller.get_media_info()

    def as_numeric(self) -> float:
        self.update_info()
        return (self.media_info.custom_data and self.media_info.custom_data.get('rating', 0)) or 0

    def as_string(self) -> str:
        self.update_info()

        return f"{self.media_info.position_str} / {self.media_info.duration_str}"

    def as_image(self) -> Image:
        pass

    def last_values(self) -> List[float]:
        pass

class NowPlayingPlexTrackInfo(CustomDataSource):
    def __init__(self):
        media_config = config.CONFIG_DATA.get('media_providers', {})
        plex_config = media_config.get('plex', {})
        product = plex_config.get('product', 'Plexamp')
        profile = plex_config.get('profile', 'Windows')
        device = plex_config.get('device', None)
        custom_interval = config.THEME_DATA['STATS']['CUSTOM'].get("INTERVAL", 5)
        self.media_controller = PlexMediaController(plex_config.get('url'),  plex_config.get('token'), product, profile, device, custom_interval)
        self.update_info()

    def update_info(self):
        """Actualiza la información del medio actual"""
        self.media_info = self.media_controller.get_media_info()

    def as_numeric(self) -> float:
        pass

    def as_string(self) -> str:
        self.update_info()

        if (not self.media_info.custom_data):
            return 'Desconocido'

        year = self.media_info.custom_data.get('year', 0) or ''

        disc_str = "Disco"
        if self.media_info.custom_data.get('media_type', '') == 'movie':
            disc_str = "Parte"
        if self.media_info.custom_data.get('media_type', '') == 'show':
            disc_str = "T"

        track_str = "Pista"
        if self.media_info.custom_data.get('media_type', '') == 'movie':
            track_str = "Parte"
        if self.media_info.custom_data.get('media_type', '') == 'show':
            track_str = "Episodio"

        artist_str = "Interprete:"
        if self.media_info.custom_data.get('media_type', '') == 'movie':
            artist_str = ""
        if self.media_info.custom_data.get('media_type', '') == 'show':
            artist_str = ""

        disc_number = self.media_info.custom_data.get('disc_number', 1)
        total_discs = self.media_info.custom_data.get('total_discs', 1)
        track_number_info = f"{track_str} {self.media_info.track_number} de {self.media_info.total_tracks}"
        if total_discs > 1:
            track_number_info = f"{disc_str} {disc_number} de {total_discs} - {track_number_info}"
        return f"{self.media_info.album} ({year}) \n {self.media_info.album_artist} \n {self.media_info.genre} \n \n {artist_str} {self.media_info.artist} \n {track_number_info}"

    def as_image(self) -> Image:
        pass

    def last_values(self) -> List[float]:
        pass


# --- SENSOR DE FPS (PresentMon) ---
class PresentMonFPSDataSource:
    def __init__(self):
        self.present_mon = PresentMonController()  # Iniciar el controlador de PresentMon para que comience a recolectar datos
        self.present_mon._start_monitoring()

    def as_numeric(self) -> float:
        return self.present_mon.get_current_metrics().get("fps", 0.0)

    def as_string(self) -> str:
        return f'{int(self.as_numeric())}\nFPS'

    def last_values(self):
        pass

    def as_image(self):
        pass

class PresentMonExtraInfoDataSource:
    def __init__(self):
        self.present_mon = PresentMonController()  # Iniciar el controlador de PresentMon para que comience a recolectar datos
        self.present_mon._start_monitoring()

    def as_numeric(self) -> float:
        pass

    def as_string(self) -> str:
        metrics = self.present_mon.get_current_metrics()
        return f"{metrics['app_name']}\n\n{metrics['api']}\n{metrics['limiter']}\n{metrics['latency']:.1f}ms" if metrics['fps'] > 1.0 else "IDLE"

    def last_values(self):
        pass

    def as_image(self):
        pass

# --- Instancia global para que todos los sensores compartan la misma lectura ---
# Asegúrate de que la clase HWInfo (la que arreglamos antes) esté definida más arriba en este mismo archivo
hwinfo_reader = HWInfo()

class HWInfoCPUTempDataSource(CustomDataSource):
    def __init__(self):
        super().__init__()
        self._values = []

    def as_numeric(self) -> float:
        if not hasattr(self, '_values'):
            self._values = []

        # Usamos la clase centralizada para obtener el valor
        current_temp = hwinfo_reader.get_sensor_value("CPU Package")

        # Gestión del historial para gráficas
        self._values.append(current_temp)
        if len(self._values) > 30:
            self._values.pop(0)

        return current_temp

    def as_string(self) -> str:
        val = self.as_numeric()
        return f"{int(val)}°C"

    def as_image(self):
        pass

    def last_values(self):
        return getattr(self, '_values', [0.0])

class HWInfoCoreVIDDataSource(CustomDataSource):
    def __init__(self):
        super().__init__()
        self._values = []

    def as_numeric(self) -> float:
        if not hasattr(self, '_values'):
            self._values = []

        # Usamos el nuevo método pasándole el nombre EXACTO del hijo
        current_vid = hwinfo_reader.get_cpu_sensor_value("Vcore")

        # NOTA: Si en tu placa/procesador resulta que HWiNFO lo llama "Vcore",
        # simplemente cambias "Core VIDs" por "Vcore" en la línea de arriba.

        self._values.append(current_vid)
        if len(self._values) > 30:
            self._values.pop(0)

        return current_vid

    def as_string(self) -> str:
        val = self.as_numeric()
        return f"{val:.3f} V"

    def as_image(self):
        pass

    def last_values(self):
        return getattr(self, '_values', [0.0])

class HWInfoAverageEffectiveClockDataSource(CustomDataSource):
    def __init__(self):
        super().__init__()
        self._values = []

    def as_numeric(self) -> float:
        if not hasattr(self, '_values'):
            self._values = []

        # Pedimos el nombre EXACTO
        current_clock = hwinfo_reader.get_cpu_sensor_value("Average Effective Clock")

        self._values.append(current_clock)
        if len(self._values) > 30:
            self._values.pop(0)

        return current_clock

    def as_string(self) -> str:
        val = self.as_numeric()
        return f"{int(val)} MHz"

    def as_image(self):
        pass

    def last_values(self):
        return getattr(self, '_values', [0.0])

class HWInfoDiskActivityDataSource(CustomDataSource):
    """Clase pensada para el RADIAL (solo devuelve el porcentaje limpio)"""
    def __init__(self):
        super().__init__()
        self._values = []

    def as_numeric(self) -> float:
        if not hasattr(self, '_values'):
            self._values = []

        disk_info = hwinfo_reader.get_disk_activity_info()
        max_activity = disk_info["activity"]

        self._values.append(max_activity)
        if len(self._values) > 30:
            self._values.pop(0)

        return max_activity

    def as_string(self) -> str:
        # Solo devuelve "15%" para que el texto central del Radial no se rompa
        val = self.as_numeric()
        return f"{int(val)}%"

    def as_image(self):
        pass

    def last_values(self):
        return getattr(self, '_values', [0.0])


class HWInfoDiskActivityTextDataSource(CustomDataSource):
    """Clase pensada para el TEXTO (devuelve porcentaje + letra de la unidad)"""
    def __init__(self):
        super().__init__()
        self._values = []

    def as_numeric(self) -> float:
        if not hasattr(self, '_values'):
            self._values = []

        disk_info = hwinfo_reader.get_disk_activity_info()
        max_activity = disk_info["activity"]

        self._values.append(max_activity)
        if len(self._values) > 30:
            self._values.pop(0)

        return max_activity

    def as_string(self) -> str:
        disk_info = hwinfo_reader.get_disk_activity_info()
        activity = disk_info.get('activity', 0.0)
        letter = disk_info.get('letter', 'N/A')
        number = disk_info.get('number', 'N/A')

        if letter != "N/A":
            return f"DISK {letter}"
        elif number != "N/A":
            return f"DISK {number}"
        else:
            return f"DISK {int(activity)}%"

    def as_image(self):
        pass

    def last_values(self):
        return getattr(self, '_values', [0.0])


class HWInfoAverageEffectiveClockDataSource(CustomDataSource):
    def __init__(self):
        super().__init__()
        self._values = []

    def as_numeric(self) -> float:
        if not hasattr(self, '_values'):
            self._values = []

        # Usamos la clase centralizada
        current_clock = hwinfo_reader.get_sensor_value("Average Effective Clock")

        self._values.append(current_clock)
        if len(self._values) > 30:
            self._values.pop(0)

        return current_clock

    def as_string(self) -> str:
        val = self.as_numeric()
        return f"{val:.0f} MHz"

    def as_image(self):
        pass

    def last_values(self):
        return getattr(self, '_values', [0.0])


class HWInfoThermalThrottlingDataSource(CustomDataSource):
    def __init__(self):
        super().__init__()
        self._values = []

    def as_numeric(self) -> float:
        if not hasattr(self, '_values'):
            self._values = []

        # Usamos la clase centralizada
        current_throttling = hwinfo_reader.get_sensor_value("Package/Ring Thermal Throttling")

        self._values.append(current_throttling)
        if len(self._values) > 30:
            self._values.pop(0)

        return current_throttling

    def as_string(self) -> str:
        val = self.as_numeric()
        return f"{val:.1f}%"

    def as_image(self):
        pass

    def last_values(self):
        return getattr(self, '_values', [0.0])

class HWInfoRAMAvgTempDataSource(CustomDataSource):
    def __init__(self):
        super().__init__()
        self._values = []

    def as_numeric(self) -> float:
        if not hasattr(self, '_values'):
            self._values = []

        total_temp = 0.0
        count = 0

        # Nos aseguramos de tener los datos más recientes
        hwinfo_reader._read_shared_memory()

        # Recorremos toda la memoria buscando todos los módulos de RAM
        for full_name, value in hwinfo_reader._sensor_data.items():
            # Buscamos específicamente los nombres largos para no contar doble el nombre corto
            if full_name.endswith(" - SPD Hub Temperature"):
                total_temp += value
                count += 1

        # Calculamos la media. Si no encuentra ninguna RAM (count = 0), devuelve 0.0 para no dar error
        avg_temp = (total_temp / count) if count > 0 else 0.0

        self._values.append(avg_temp)
        if len(self._values) > 30:
            self._values.pop(0)

        return avg_temp

    def as_string(self) -> str:
        val = self.as_numeric()
        # Lo dejamos en número entero para que se vea limpio en pantalla
        return f"{int(val)}°C"

    def as_image(self):
        pass

    def last_values(self):
        return getattr(self, '_values', [0.0])

class HWInfoDiskReadRateDataSource(CustomDataSource):
    def __init__(self):
        super().__init__()
        self._values = []

    def as_numeric(self) -> float:
        if not hasattr(self, '_values'):
            self._values = []

        # Usamos la info que ya nos da el método centralizado
        disk_info = hwinfo_reader.get_disk_activity_info()
        read_rate = disk_info.get("read_rate", 0.0)

        self._values.append(read_rate)
        if len(self._values) > 30:
            self._values.pop(0)

        return read_rate

    def as_string(self) -> str:
        val = self.as_numeric()
        return f"{val:.1f} MB/s"

    def as_image(self):
        pass

    def last_values(self):
        return getattr(self, '_values', [0.0])


class HWInfoDiskWriteRateDataSource(CustomDataSource):
    def __init__(self):
        super().__init__()
        self._values = []

    def as_numeric(self) -> float:
        if not hasattr(self, '_values'):
            self._values = []

        disk_info = hwinfo_reader.get_disk_activity_info()
        write_rate = disk_info.get("write_rate", 0.0)

        self._values.append(write_rate)
        if len(self._values) > 30:
            self._values.pop(0)

        return write_rate

    def as_string(self) -> str:
        val = self.as_numeric()
        return f"{val:.1f} MB/s"

    def as_image(self):
        pass

    def last_values(self):
        return getattr(self, '_values', [0.0])

class HWInfoNetDownloadDataSource(CustomDataSource):
    def __init__(self):
        super().__init__()
        self._values = []

        # --- ¡CONFIGURA AQUÍ TU VELOCIDAD! ---
        # Pon los Megas que tienes contratados (ej: 300, 600, 1000)
        self.MI_VELOCIDAD_CONTRATADA_MBPS = 1000

        # Matemáticas internas: Convertimos Megabits a KiloBytes/segundo
        # 1000 Mbps / 8 = 125 MB/s -> 125 * 1024 = 128000 KB/s
        self.max_kbps = (self.MI_VELOCIDAD_CONTRATADA_MBPS / 8) * 1024

    def as_numeric(self) -> float:
        if not hasattr(self, '_values'):
            self._values = []

        max_dl = 0.0
        # Nos aseguramos de que los datos de HWiNFO están frescos
        hwinfo_reader._read_shared_memory()

        # Buscamos la tarjeta de red que esté descargando en este momento
        for name, value in hwinfo_reader._sensor_data.items():
            if name.endswith(" - Current DL rate"):
                if value > max_dl:
                    max_dl = value  # HWiNFO lo da en KB/s

        # Calculamos el porcentaje
        percentage = (max_dl / self.max_kbps) * 100.0

        # Un seguro de vida por si algún día descargas más rápido de lo que tienes contratado
        percentage = min(percentage, 100.0)

        self._values.append(percentage)
        if len(self._values) > 30:
            self._values.pop(0)

        return percentage

    def as_string(self) -> str:
        val = self.as_numeric()
        return f"{int(val)}%"

    def as_image(self):
        pass

    def last_values(self):
        return getattr(self, '_values', [0.0])


class HWInfoNetUploadDataSource(CustomDataSource):
    def __init__(self):
        super().__init__()
        self._values = []

        # --- ¡CONFIGURA AQUÍ TU VELOCIDAD! ---
        # Si tienes fibra simétrica, será igual que la descarga.
        self.MI_VELOCIDAD_CONTRATADA_MBPS = 1000
        self.max_kbps = (self.MI_VELOCIDAD_CONTRATADA_MBPS / 8) * 1024

    def as_numeric(self) -> float:
        if not hasattr(self, '_values'):
            self._values = []

        max_up = 0.0
        hwinfo_reader._read_shared_memory()

        for name, value in hwinfo_reader._sensor_data.items():
            if name.endswith(" - Current UP rate"):
                if value > max_up:
                    max_up = value

        percentage = (max_up / self.max_kbps) * 100.0
        percentage = min(percentage, 100.0)

        self._values.append(percentage)
        if len(self._values) > 30:
            self._values.pop(0)

        return percentage

    def as_string(self) -> str:
        val = self.as_numeric()
        return f"{int(val)}%"

    def as_image(self):
        pass

    def last_values(self):
        return getattr(self, '_values', [0.0])