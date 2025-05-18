from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from PIL import Image
from datetime import datetime

@dataclass
class MediaInfo:
    """Clase base para almacenar información multimedia"""
    title: str = "Desconocido"
    artist: str = "Desconocido"
    album: str = "Desconocido"
    album_artist: str = "Desconocido"
    track_number: int = 0
    total_tracks: int = 0
    genre: str = "Desconocido"
    position: float = 0
    duration: float = 0
    timeline_last_update: Optional[datetime] = None
    is_playing: bool = False
    thumbnail: Optional[Image.Image] = None
    custom_data: Optional[dict] = None

    @property
    def position_str(self) -> str:
        return f"{int(self.position // 60)}:{int(self.position % 60):02d}"

    @property
    def duration_str(self) -> str:
        if self.duration == 0:
            return "Desconocido"
        return f"{int(self.duration // 60)}:{int(self.duration % 60):02d}"

    @property
    def progress(self) -> float:
        duration = self.duration
        if duration == 0:
            duration = 240 # Algunos reproductores no reportan la duración, por lo que se asigna un valor por defecto de 4 minutos
        return (self.position / duration * 100) if duration > 0 else 0

    def __str__(self) -> str:
        base_info = (
            f"\nMediaInfo:"
            f"\n - Título: {self.title}"
            f"\n - Artista: {self.artist}"
            f"\n - Álbum: {self.album}"
            f"\n - Artista del álbum: {self.album_artist}"
            f"\n - Número de pista: {self.track_number}"
            f"\n - Total de pistas: {self.total_tracks}"
            f"\n - Género: {self.genre}"
            f"\n - Posición: {self.position_str}"
            f"\n - Duración: {self.duration_str}"
            f"\n - En reproducción: {self.is_playing}"
            f"\n - Tiene miniatura: {self.thumbnail is not None}"
            f"\n - Progreso: {self.progress:.1f}%"
        )

        # Añadir atributos personalizados al string si existen
        if self.custom_data:
            custom_info = "\n - Atributos personalizados:"
            for key, value in self.custom_data.items():
                custom_info += f"\n   - {key}: {value}"
            base_info = base_info + custom_info

        return base_info

class MediaController(ABC):
    """Interfaz base para controladores multimedia"""

    @abstractmethod
    def get_media_info(self) -> MediaInfo:
        """Obtiene la información actual del medio en reproducción"""
        pass