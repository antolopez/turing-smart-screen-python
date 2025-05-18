from library.sensors.media_controller import MediaController, MediaInfo
from plexapi.server import PlexServer
from dataclasses import dataclass
from typing import Optional
from PIL import Image
import requests
from io import BytesIO
from library.log import logger
from datetime import datetime

plex_last_reported_position = None
plex_last_position_datetime = None

class PlexMediaController(MediaController):
    def __init__(self, base_url: str, token: str, product: str, profile: str, device: str = None):
        self._plex = PlexServer(base_url, token)
        self._current_info = MediaInfo()
        self.product = product
        self.profile = profile
        self.device = device

    def _get_thumbnail(self, thumb_url: str) -> Optional[Image.Image]:
        """Obtiene la miniatura de la canción actual"""
        try:
            response = requests.get(thumb_url)
            if response.status_code == 200:
                return Image.open(BytesIO(response.content))
            else:
                logger.error(f"Error al obtener la miniatura. Status code: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error al obtener la miniatura: {str(e)}")
            return None

    def _update_media_info(self) -> MediaInfo:
        """Actualiza la información del medio actual"""
        try:
            sessions = self._plex.sessions()
            for session in sessions:
                # Buscar sesión de Plexamp
                logger.debug(f"Buscando sesión de Plexamp: {self.product}, {self.profile}, {self.device}")
                is_target = session.player.product == self.product and session.player.profile == self.profile and (session.player.title == self.device or self.device is None)
                if is_target or sessions.__len__() == 1:
                    logger.debug(f"Encontrada sesión {session.player.product}, {session.player.profile}, {session.player.title}")
                    logger.debug(f"Estado de reproducción: {session.player.state}")

                    # Obtener artista de la pista o usar el artista del álbum como fallback
                    track_artist = getattr(session, 'originalTitle', None) or session.grandparentTitle
                    # Obtener información de la pista actual y total
                    track_number = getattr(session, 'index', 0) or 0  # Número de pista actual
                    # Obtener total de pistas del álbum
                    try:
                        # Intentar obtener el álbum y su número total de pistas
                        album = session.album()
                        total_tracks = album.leafCount
                    except Exception as e:
                        logger.debug(f"No se pudo obtener el total de pistas: {e}")
                        total_tracks = 0
                    # Obtener el primer género si existe
                    try:
                        genre = session.genres[0].tag if session.genres else "Sin género"
                    except Exception as e:
                        logger.debug(f"No se pudo obtener el género: {e}")
                        genre = "Sin género"

                    # Obtener el año, primero de la pista y si no del álbum
                    try:
                        # Intentar obtener el año de la pista primero
                        year = getattr(session, 'year', None)
                        logger.debug(f"Año de la pista: {year}")

                        # Si no hay año en la pista, intentar obtenerlo del álbum
                        if not year:
                            try:
                                album = session.album()
                                year = getattr(album, 'year', None)
                                logger.debug(f"Año del álbum: {year}")
                            except Exception as e:
                                logger.debug(f"No se pudo obtener el año del álbum: {e}")
                                year = None
                    except Exception as e:
                        logger.debug(f"No se pudo obtener el año: {e}")
                        year = None

                    # Obtener información del disco
                    try:
                        # Número de disco actual
                        disc_number = getattr(session, 'parentIndex', 1) or 1

                        # Obtener total de discos contando los diferentes parentIndex
                        album = session.album()
                        all_tracks = album.tracks()
                        total_discs = max(getattr(t, 'parentIndex', 1) or 1 for t in all_tracks)

                        # Obtener total de pistas del disco actual
                        tracks_in_disc = [t for t in all_tracks if getattr(t, 'parentIndex', 1) == disc_number]
                        total_tracks = len(tracks_in_disc)

                        logger.debug(f"Disco actual: {disc_number}")
                        logger.debug(f"Total discos: {total_discs}")
                        logger.debug(f"Pistas en disco actual: {total_tracks}")

                    except Exception as e:
                        logger.debug(f"No se pudo obtener la información de discos: {e}")
                        disc_number = 1
                        total_discs = 1
                        total_tracks = 0

                    # Obtener la duración de la pista estimando el tiempo de reproducción para mayor precision
                    global plex_last_reported_position
                    global plex_last_position_datetime
                    position=session.viewOffset / 1000  # Convertir de ms a s
                    duration=session.duration / 1000    # Convertir de ms a s
                    is_playing=session.player.state == 'playing',
                    if is_playing:
                        if plex_last_reported_position != position:
                            # Actualizar la posición reportada
                            plex_last_reported_position = position
                            plex_last_position_datetime = datetime.now()
                        else:
                            # Calcular la posición estimada
                            elapsed_time = (datetime.now() - plex_last_position_datetime).total_seconds()
                            position = position + elapsed_time

                    # Actualizar información
                    self._current_info = MediaInfo(
                        title=session.title,
                        artist=track_artist,
                        album=session.parentTitle,
                        album_artist=session.grandparentTitle,
                        track_number=track_number,
                        total_tracks=total_tracks,
                        genre=genre,
                        position=position,
                        duration=duration,
                        is_playing=is_playing,
                        thumbnail=self._get_thumbnail(session.thumbUrl),
                        custom_data={
                            "rating": session.userRating,
                            "year": year,
                            "disc_number": disc_number,
                            "total_discs": total_discs,
                        }
                    )

                    logger.debug(f"Sesión Plex: {session.rating}")
                    logger.debug(f"audirat: {session.userRating }")
                    logger.debug(str(self._current_info))
                    return self._current_info

            # Si no se encuentra sesión activa
            logger.debug("No se encontró reproducción activa en Plexamp")
            self._current_info = MediaInfo()

        except Exception as e:
            logger.error(f"Error al actualizar la información de Plex: {str(e)}")
            self._current_info = MediaInfo()

        return self._current_info

    def get_media_info(self) -> MediaInfo:
        """Obtiene la información actual del medio en reproducción"""
        return self._update_media_info()