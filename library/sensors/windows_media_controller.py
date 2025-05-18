from library.sensors.media_controller import MediaController, MediaInfo

from winsdk.windows.media.control import \
    GlobalSystemMediaTransportControlsSessionManager as MediaManager
from winsdk.windows.storage.streams import Buffer, DataReader
import asyncio
from io import BytesIO
from PIL import Image
from typing import Optional
from library.log import logger
from datetime import datetime

windows_last_reported_position = None
windows_last_position_datetime = None
windows_last_track_reported = None

class WindowsMediaController(MediaController):
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self._current_info = MediaInfo()
        self._last_update_time = 0
        self._last_known_position = 0

    async def _get_thumbnail2(self, session) -> Optional[Image.Image]:
        try:
            media_props = await session.try_get_media_properties_async()
            thumbnail_ref = media_props.thumbnail

            if thumbnail_ref:
                try:
                    # Abrir el stream
                    stream = await thumbnail_ref.open_read_async()
                    size = int(stream.size)

                    # Crear un buffer del tamaño exacto necesario
                    buffer = Buffer(size)

                    # Leer todo el contenido de una vez
                    bytes_read = await stream.read_async(buffer, size, 0)

                    if bytes_read == size:
                        # Convertir el buffer a bytes
                        reader = DataReader.from_buffer(buffer)
                        bytes_data = bytearray(size)
                        reader.read_bytes(bytes_data)

                        # Crear la imagen con el modo "RGBA" explícito
                        try:
                            image = Image.frombytes("RGBA", (size, size), bytes_data)
                            # Si llegamos aquí, la imagen es válida
                            return image
                        except Exception as img_error:
                            logger.error(f"Error al crear la imagen: {str(img_error)}")
                            return None
                    else:
                        logger.error(f"No se pudieron leer todos los bytes: {bytes_read}/{size}")
                        return None

                except Exception as stream_error:
                    logger.error(f"Error al leer el stream: {str(stream_error)}")
                    return None

            return None
        except Exception as e:
            logger.error(f"Error general: {str(e)}")
            return None

    async def _get_thumbnail(self, session) -> Optional[Image.Image]:
        try:
            media_props = await session.try_get_media_properties_async()
            thumbnail_ref = media_props.thumbnail

            if thumbnail_ref:
                try:
                    # Abrir el stream
                    stream = await thumbnail_ref.open_read_async()

                    # Crear un DataReader para el stream
                    reader = DataReader(stream)

                    # Cargar los datos en el reader
                    size = int(stream.size)
                    await reader.load_async(size)

                    # Leer todos los bytes del buffer
                    buffer = bytearray(size)
                    reader.read_bytes(buffer)

                    # Crear la imagen desde los bytes
                    return Image.open(BytesIO(buffer))

                except Exception as stream_error:
                    logger.error(f"Error al leer el stream de la miniatura: {str(stream_error)}")
                    logger.debug(f"Detalles del error: {stream_error.__class__.__name__}")
                    return None

            return None
        except Exception as e:
            logger.error(f"Error al obtener la miniatura del medio actual: {str(e)}")
            logger.debug(f"Tipo de thumbnail: {type(media_props.thumbnail)}")
            return None

    async def _update_media_info(self) -> MediaInfo:
        global last_reported_position
        try:
            sessions = await MediaManager.request_async()
            current_session = sessions.get_current_session()

            if current_session:
                media_props = await current_session.try_get_media_properties_async()
                timeline_props = current_session.get_timeline_properties()
                playback_info = current_session.get_playback_info()

                # Calcular posición estimada
                global windows_last_reported_position
                global windows_last_position_datetime
                global windows_last_track_reported
                is_playing = playback_info.playback_status == 4
                position = timeline_props.position.total_seconds()
                if is_playing:
                    if windows_last_reported_position != position:
                        # Actualizar la posición reportada
                        windows_last_reported_position = position
                        windows_last_position_datetime = datetime.now()
                    else:
                        # Calcular la posición estimada
                        elapsed_time = (datetime.now() - windows_last_position_datetime).total_seconds()
                        position = position + elapsed_time

                        if windows_last_track_reported != media_props.title:
                            # Actualizar el título reportado
                            windows_last_reported_position = 0
                            windows_last_position_datetime = datetime.now()
                    windows_last_track_reported = media_props.title

                self._current_info = MediaInfo(
                    title=media_props.title or "Desconocido",
                    artist=media_props.artist or "Desconocido",
                    album=media_props.album_title or "Desconocido",
                    album_artist=media_props.album_artist or "Desconocido",
                    track_number=media_props.track_number or 0,
                    total_tracks=media_props.album_track_count or 0,
                    genre=media_props.genres[0] if media_props.genres and len(media_props.genres) > 0 else "Sin género",
                    position=position,
                    duration=timeline_props.end_time.total_seconds(),
                    is_playing=is_playing,
                    thumbnail=await self._get_thumbnail(current_session),
                    custom_data={
                        "type": playback_info.playback_type.name,  # Acceder al tipo de reproducción
                        "application": current_session.source_app_user_model_id,  # Obtener el ID de la aplicación
                    }
                )

                # Añadir el log aquí
                logger.debug(str(self._current_info))
            else:
                self._current_info = MediaInfo()
                self._is_playing = False

        except Exception:
            self._current_info = MediaInfo()

        return self._current_info

    def get_media_info(self) -> MediaInfo:
        """Obtiene la información actual del medio en reproducción"""
        return self.loop.run_until_complete(self._update_media_info())