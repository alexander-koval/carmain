import os
import io
import uuid

import pytest

from carmain.services.file_service import FileService


class DummyUploadFile:
    def __init__(self, filename: str, content: bytes):
        self.filename = filename
        self.file = io.BytesIO(content)


@pytest.mark.asyncio
async def test_save_vehicle_photo_success(tmp_path):
    media_dir = tmp_path / "media"
    service = FileService(media_path=str(media_dir), static_path="unused")
    content = b"test image content"
    photo = DummyUploadFile("photo.png", content)
    rel_path = await service.save_vehicle_photo(photo)
    assert rel_path.startswith("vehicles/")
    assert rel_path.lower().endswith(".png")
    full_path = media_dir / rel_path
    assert full_path.exists()
    assert full_path.read_bytes() == content


@pytest.mark.asyncio
async def test_save_vehicle_photo_unsupported_extension(tmp_path):
    service = FileService(media_path=str(tmp_path), static_path="unused")
    photo = DummyUploadFile("file.txt", b"data")
    with pytest.raises(ValueError) as exc:
        await service.save_vehicle_photo(photo)
    assert "Неподдерживаемый формат файла" in str(exc.value)


@pytest.mark.asyncio
async def test_save_vehicle_photo_no_filename(tmp_path):
    service = FileService(media_path=str(tmp_path), static_path="unused")
    photo = DummyUploadFile("", b"data")
    with pytest.raises(ValueError) as exc:
        await service.save_vehicle_photo(photo)
    assert "Файл не предоставлен" in str(exc.value)


def test_delete_vehicle_photo(tmp_path):
    media_dir = tmp_path / "media"
    service = FileService(media_path=str(media_dir), static_path="unused")
    rel = "vehicles/test.jpg"
    full_dir = media_dir / "vehicles"
    full_dir.mkdir(parents=True)
    file_path = full_dir / "test.jpg"
    file_path.write_bytes(b"data")
    assert service.delete_vehicle_photo(rel) is True
    assert not file_path.exists()
    assert service.delete_vehicle_photo(rel) is False
    assert service.delete_vehicle_photo(None) is False


def test_get_full_path(tmp_path):
    media_dir = tmp_path / "media"
    service = FileService(media_path=str(media_dir), static_path="unused")
    rel = "vehicles/pic.png"
    full_dir = media_dir / "vehicles"
    full_dir.mkdir(parents=True)
    file_path = full_dir / "pic.png"
    file_path.write_bytes(b"img")
    full = service.get_full_path(rel)
    assert full == str(file_path)
    assert service.get_full_path("vehicles/missing.png") is None
    assert service.get_full_path(None) is None
