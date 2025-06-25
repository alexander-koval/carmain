import os
import uuid
import shutil
from typing import Optional
from fastapi import UploadFile
from carmain.core.config import get_settings


class FileService:
    """Сервис для работы с файлами"""

    def __init__(self, media_path: Optional[str] = None, static_path: Optional[str] = None):
        settings = get_settings()
        self.media_path = media_path or settings.media_path
        self.static_path = static_path or settings.static_path

    async def save_vehicle_photo(self, photo: UploadFile) -> str:
        """
        Сохранить фото автомобиля

        Args:
            photo: Загружаемый файл

        Returns:
            str: Относительный путь к сохраненному файлу
        """
        if not photo or not photo.filename:
            raise ValueError("Файл не предоставлен")

        upload_dir = f"{self.media_path}/vehicles"
        os.makedirs(upload_dir, exist_ok=True)

        file_extension = os.path.splitext(photo.filename)[1].lower()

        allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
        if file_extension not in allowed_extensions:
            raise ValueError(f"Неподдерживаемый формат файла: {file_extension}")

        filename = f"{uuid.uuid4()}{file_extension}"
        file_path = f"{upload_dir}/{filename}"

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)

        return f"vehicles/{filename}"

    def delete_vehicle_photo(self, photo_path: Optional[str]) -> bool:
        """
        Удалить фото автомобиля

        Args:
            photo_path: Относительный путь к файлу

        Returns:
            bool: True если файл был удален, False если файл не существует
        """
        if not photo_path:
            return False

        full_path = f"{self.media_path}/{photo_path}"

        try:
            if os.path.exists(full_path):
                os.remove(full_path)
                return True
            return False
        except Exception:
            return False

    def get_full_path(self, relative_path: Optional[str]) -> Optional[str]:
        """
        Получить полный путь к файлу

        Args:
            relative_path: Относительный путь

        Returns:
            str: Полный путь к файлу или None
        """
        if not relative_path:
            return None

        full_path = f"{self.media_path}/{relative_path}"
        return full_path if os.path.exists(full_path) else None
