# turing-smart-screen-python - a Python system monitor and library for USB-C displays like Turing Smart Screen or XuanFang
# https://github.com/mathoudebine/turing-smart-screen-python/
# Copyright (C) 2021-2023  Matthieu Houdebine (mathoudebine)
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
from library.sensors.plex_media_controller import PlexMediaController
import library.config as config

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
class NowPlayingPlexTrack(CustomDataSource):
    def __init__(self):
        media_config = config.CONFIG_DATA.get('media_providers', {})
        plex_config = media_config.get('plex', {})
        product = plex_config.get('product', 'Plexamp')
        profile = plex_config.get('profile', 'Windows')
        device = plex_config.get('device', None)
        self.media_controller = PlexMediaController(plex_config.get('url'),  plex_config.get('token'), product, profile, device)
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
        self.media_controller = PlexMediaController(plex_config.get('url'),  plex_config.get('token'), product, profile, device)
        self.update_info()

    def update_info(self):
        """Actualiza la información del medio actual"""
        self.media_info = self.media_controller.get_media_info()

    def as_numeric(self) -> float:
        self.update_info()
        return self.media_info.custom_data.get('rating', 0) or 0

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
        self.media_controller = PlexMediaController(plex_config.get('url'),  plex_config.get('token'), product, profile, device)
        self.update_info()

    def update_info(self):
        """Actualiza la información del medio actual"""
        self.media_info = self.media_controller.get_media_info()

    def as_numeric(self) -> float:
        pass

    def as_string(self) -> str:
        self.update_info()

        year = self.media_info.custom_data.get('year', 0) or ''

        disc_number = self.media_info.custom_data.get('disc_number', 1)
        total_discs = self.media_info.custom_data.get('total_discs', 1)
        track_number_info = f"Pista {self.media_info.track_number} de {self.media_info.total_tracks}"
        if total_discs > 1:
            track_number_info = f"Disco {disc_number} de {total_discs} - {track_number_info}"
        return f"{self.media_info.album} ({year}) \n {self.media_info.album_artist} \n {self.media_info.genre} \n \n Interprete: {self.media_info.artist} \n {track_number_info}"

    def as_image(self) -> Image:
        pass

    def last_values(self) -> List[float]:
        pass

