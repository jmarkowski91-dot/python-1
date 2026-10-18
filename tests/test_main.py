from unittest.mock import MagicMock, mock_open, patch

import pytest
import requests

from python1.main import AccessDeniedError, HttpError, NotFoundError, download_file


def test_downloads_and_saves_content(tmp_path):
    path = tmp_path / "latest.txt"
    response = MagicMock(content=b"sample content")
    response.raise_for_status.return_value = None

    with patch("python1.main.requests.get", return_value=response):
        download_file("http://example.com/file", str(path))

    assert path.read_bytes() == b"sample content"


def test_calls_get_with_given_url():
    response = MagicMock(content=b"")
    with (
        patch("python1.main.requests.get", return_value=response) as mock_get,
        patch("builtins.open", mock_open()),
    ):
        download_file("http://example.com/file")

    mock_get.assert_called_once_with("http://example.com/file")


def test_default_filename(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    response = MagicMock(content=b"data")
    with patch("python1.main.requests.get", return_value=response):
        download_file("http://example.com/file")

    assert (tmp_path / "latest.txt").read_bytes() == b"data"


def test_raises_exception_for_http_error():
    response = MagicMock()
    response.raise_for_status.side_effect = requests.HTTPError("404")

    with (
        patch("python1.main.requests.get", return_value=response),
        patch("builtins.open", mock_open()) as mock_file,
        pytest.raises(requests.HTTPError),
    ):
        download_file("http://example.com/file")

    mock_file.assert_not_called()


def test_raises_not_found_error_for_404(tmp_path):
    path = tmp_path / "latest.txt"
    response = MagicMock(status_code=404)

    with (
        patch("python1.main.requests.get", return_value=response),
        pytest.raises(NotFoundError, match="404|not found|example.com") as exc_info,
    ):
        download_file("http://example.com/file", str(path))

    assert isinstance(exc_info.value, HttpError)
    assert not path.exists()


def test_raises_access_denied_error_for_403(tmp_path):
    path = tmp_path / "latest.txt"
    response = MagicMock(status_code=403)

    with (
        patch("python1.main.requests.get", return_value=response),
        pytest.raises(AccessDeniedError, match="403|denied|example.com") as exc_info,
    ):
        download_file("http://example.com/file", str(path))

    assert isinstance(exc_info.value, HttpError)
    assert not path.exists()


def test_exception_hierarchy():
    assert issubclass(HttpError, Exception)
    assert issubclass(NotFoundError, HttpError)
    assert issubclass(AccessDeniedError, HttpError)
