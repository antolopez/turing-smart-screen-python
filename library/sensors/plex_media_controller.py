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

    def _update_music_info(self, session) -> MediaInfo:
        """Actualiza la información para contenido musical"""
        try:
            # Obtener artista de la pista o usar el artista del álbum como fallback
            track_artist = getattr(session, 'originalTitle', None) or session.grandparentTitle
            track_number = getattr(session, 'index', 0) or 0

            # Obtener información del álbum
            album = session.album()
            total_tracks = album.leafCount if album else 0

            # Obtener género
            genre = session.genres[0].tag if session.genres else None
            if genre is None:
                genre = album.genres[0].tag if album.genres else "Sin género"

            # Obtener año
            year = getattr(session, 'originallyAvailableAt', None) or getattr(album, 'year', None)

            # Obtener información del disco
            disc_number = getattr(session, 'parentIndex', 1) or 1
            all_tracks = album.tracks() if album else []
            total_discs = max(getattr(t, 'parentIndex', 1) or 1 for t in all_tracks)
            # Obtener total de pistas del disco actual
            tracks_in_disc = [t for t in all_tracks if getattr(t, 'parentIndex', 1) == disc_number]
            total_tracks = len(tracks_in_disc)

            return MediaInfo(
                title=session.title,
                artist=track_artist,
                album=session.parentTitle,
                album_artist=session.grandparentTitle,
                track_number=track_number,
                total_tracks=total_tracks,
                genre=genre,
                position=self._get_position(session),
                duration=session.duration / 1000,
                is_playing=session.player.state == 'playing',
                thumbnail=self._get_thumbnail(session.thumbUrl),
                custom_data={
                    "media_type": "music",
                    "rating": session.userRating,
                    "year": year,
                    "disc_number": disc_number,
                    "total_discs": total_discs,
                }
            )
        except Exception as e:
            logger.error(f"Error procesando información musical: {e}")
            return MediaInfo()

    def _update_movie_info(self, session) -> MediaInfo:
        """Actualiza la información para películas"""
        try:
            # Obtener los dos primeros actores
            actors = []
            if hasattr(session, 'roles') and session.roles:
                actors = [role.tag for role in session.roles[:2]]
            actors_str = " & ".join(actors) if actors else "Sin actores"

            # Obtener información de la colección (saga)
            collection_info = {}
            try:
                # Intentar obtener la colección primero desde collections
                if hasattr(session, 'collections') and session.collections:
                    collection = session.collections[0]
                    collection_movies = collection.items()
                    collection_info = {
                        "collection_name": collection.tag,  # Usar tag en lugar de title
                        "total_movies": len(collection_movies),
                        "movie_number": next((i+1 for i, movie in enumerate(collection_movies)
                                            if movie.ratingKey == session.ratingKey), 0)
                    }
                    logger.debug(f"Colección encontrada via collections: {collection.tag}")
                # Si no, intentar mediante collection()
                elif hasattr(session, 'collection') and callable(session.collection):
                    collection = session.collection()
                    if collection:
                        collection_movies = collection.items()
                        collection_info = {
                            "collection_name": collection.title,
                            "total_movies": len(collection_movies),
                            "movie_number": next((i+1 for i, movie in enumerate(collection_movies)
                                                if movie.ratingKey == session.ratingKey), 0)
                        }
                        logger.debug(f"Colección encontrada via collection(): {collection.title}")

                logger.debug(f"Información detallada de saga: {collection_info}")
            except Exception as e:
                logger.debug(f"Error obteniendo información de colección: {e}")
                collection_info = {}

            # Obtener información de audio y subtítulos
            stream_info = self._get_audio_subtitle_info(session)

            # Obtener resolución del video
            resolution = "Desconocida"
            try:
                video_stream = next((stream for stream in session.media[0].parts[0].videoStreams()), None)
                if video_stream:
                    # Intentar diferentes atributos para la resolución
                    if hasattr(video_stream, 'resolution'):
                        resolution = video_stream.resolution
                    elif hasattr(video_stream, 'height'):
                        resolution = f"{video_stream.height}p"
                    elif hasattr(session.media[0], 'videoResolution'):
                        resolution = session.media[0].videoResolution
                logger.debug(f"Resolución de video: {resolution}")
            except Exception as e:
                logger.debug(f"Error obteniendo resolución: {e}")

            return MediaInfo(
                title=session.title,
                artist=actors_str,
                album=collection_info.get("collection_name", ""),
                album_artist=session.directors[0].tag if session.directors else "Sin director",
                track_number=collection_info.get("movie_number", 1),
                total_tracks=collection_info.get("total_movies", 1),
                genre=session.genres[0].tag if session.genres else "Sin género",
                position=self._get_position(session),
                duration=session.duration / 1000,
                is_playing=session.player.state == 'playing',
                thumbnail=self._get_thumbnail(session.thumbUrl),
                custom_data={
                    "media_type": "movie",
                    "rating": session.userRating,
                    "year": getattr(session, 'year', None),
                    "resolution": resolution,
                    "audio": stream_info["audio"],
                    "subtitles": stream_info["subtitles"],
                }
            )
        except Exception as e:
            logger.error(f"Error procesando información de película: {e}")
            return MediaInfo()

    def _update_episode_info(self, session) -> MediaInfo:
        """Actualiza la información para episodios de series"""
        try:
            # Obtener información de audio y subtítulos
            stream_info = self._get_audio_subtitle_info(session)

            # Obtener el creador principal de la serie
            show = session.show()  # Obtener objeto de la serie
            # Obtener el creador/escritor de la serie
            creator = "Sin creador"
            try:
                if hasattr(session, 'writers'):
                    # Primero buscar roles específicos de creador/escritor
                    creator_roles = [role for role in session.writers]
                    if creator_roles:
                        creator = creator_roles[0].tag
                        logger.debug(f"Creador encontrado: {creator}")

                # Si no encontramos creador, intentar con roles generales
                if creator == "Sin creador" and session.directors:
                    creator = session.directors[0].tag
                    logger.debug(f"Usando director como creador: {creator}")

            except Exception as e:
                logger.debug(f"Error obteniendo creador: {e}")

            # Obtener los dos primeros actores DE LA SERIE (no del episodio)
            actors = []
            try:
                if hasattr(show, 'roles'):
                    # Filtrar solo roles de actor y ordenados como aparecen en Plex
                    actor_roles = [role for role in show.roles]
                    actors = [role.tag for role in actor_roles[:2]]
                    logger.debug(f"Actores principales de la serie: {actors}")
            except Exception as e:
                logger.debug(f"Error obteniendo actores: {e}")

            actors_str = " & ".join(actors) if actors else "Sin actores"

            # Obtener información de la temporada
            season = session.season()
            total_episodes = season.leafCount if season else 0
            logger.debug(f"Total episodios en temporada: {total_episodes}")

            # Obtener género de la serie
            genre = "Sin género"
            if hasattr(show, 'genres') and show.genres:
                genre = show.genres[0].tag
            logger.debug(f"Género de la serie: {genre}")

            # Obtener total de temporadas de la serie
            total_seasons = getattr(show, 'seasonCount', 0) if show else 0
            logger.debug(f"Total temporadas de la serie: {total_seasons}")

            return MediaInfo(
                title=session.title,
                artist=actors_str,
                album=session.grandparentTitle, # Nombre de la serie
                album_artist=creator, # Creador de la serie
                track_number=session.index,       # Número de episodio
                total_tracks=total_episodes, # Episodios temporada
                genre=genre,
                position=self._get_position(session),
                duration=session.duration / 1000,
                is_playing=session.player.state == 'playing',
                thumbnail = self._get_thumbnail(show.thumbUrl) if show else self._get_thumbnail(session.thumbUrl),
                custom_data={
                    "media_type": "show",
                    "rating": session.userRating,
                    "year": getattr(session, 'year', None),
                    "disc_number": session.parentIndex, # Número de temporada
                    "total_discs": total_seasons, # Total de temporadas
                    "audio": stream_info["audio"],
                    "subtitles": stream_info["subtitles"],
                }
            )
        except Exception as e:
            logger.error(f"Error procesando información de episodio: {e}")
            return MediaInfo()

    def _get_audio_subtitle_info(self, session) -> dict:
        """Obtiene información de audio y subtítulos de la sesión actual

        Args:
            session: Sesión de Plex actual

        Returns:
            dict: Diccionario con información de audio y subtítulos
        """
        audio_info = "Desconocido"
        subtitle_info = "Ninguno"

        try:
            # Obtener el stream de audio seleccionado
            audio_stream = next((stream for stream in session.media[0].parts[0].audioStreams()
                            if stream.selected), None)
            if audio_stream:
                audio_info = f"{audio_stream.language or 'Desconocido'} ({audio_stream.displayTitle})"
                logger.debug(f"Audio stream: {audio_info}")

            # Obtener el stream de subtítulos seleccionado
            subtitle_stream = next((stream for stream in session.media[0].parts[0].subtitleStreams()
                                if stream.selected), None)
            if subtitle_stream:
                subtitle_info = f"{subtitle_stream.language or 'Desconocido'} ({subtitle_stream.displayTitle})"
                logger.debug(f"Subtitle stream: {subtitle_info}")
        except Exception as e:
            logger.debug(f"Error obteniendo información de streams: {e}")

        return {
            "audio": audio_info,
            "subtitles": subtitle_info
        }

    def _get_position(self, session) -> float:
        """Calcula la posición actual de reproducción"""
        global plex_last_reported_position
        global plex_last_position_datetime

        position = session.viewOffset / 1000
        is_playing = session.player.state == 'playing'

        if is_playing:
            if plex_last_reported_position != position:
                plex_last_reported_position = position
                plex_last_position_datetime = datetime.now()
            else:
                elapsed_time = (datetime.now() - plex_last_position_datetime).total_seconds()
                position = position + elapsed_time

        return position

    def _update_media_info(self) -> MediaInfo:
        """Actualiza la información del medio actual"""
        try:
            sessions = self._plex.sessions()
            for session in sessions:
                logger.debug(f"Buscando sesión de Plex: {self.product}, {self.profile}, {self.device}")
                is_target = session.player.product == self.product and session.player.profile == self.profile and (session.player.title == self.device or self.device is None)
                if is_target or sessions.__len__() == 1:
                    logger.debug(f"Encontrada sesión {session.player.product}, {session.player.profile}, {session.player.title}")
                    logger.debug(f"Estado de reproducción: {session.player.state}")

                    # Determinar el tipo de contenido
                    media_type = session.type
                    logger.debug(f"Tipo de medio detectado: {media_type}")

                    if media_type == 'track':
                        return self._update_music_info(session)
                    elif media_type == 'movie':
                        return self._update_movie_info(session)
                    elif media_type == 'episode':
                        return self._update_episode_info(session)
                    else:
                        logger.warning(f"Tipo de medio no soportado: {media_type}")
                        return MediaInfo()

            return MediaInfo()
        except Exception as e:
            logger.error(f"Error al actualizar la información de Plex: {str(e)}")
            return MediaInfo()

    def get_media_info(self) -> MediaInfo:
        """Obtiene la información actual del medio en reproducción"""
        return self._update_media_info()