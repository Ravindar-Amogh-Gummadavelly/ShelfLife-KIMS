from fastapi.testclient import TestClient

import app.main as main


def test_root_serves_built_frontend_index(tmp_path, monkeypatch) -> None:
    index_file = tmp_path / "index.html"
    index_file.write_text("<!doctype html><title>ShelfLife</title>", encoding="utf-8")
    monkeypatch.setattr(main, "FRONTEND_DIST", tmp_path)

    with TestClient(main.app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "<title>ShelfLife</title>" in response.text


def test_root_returns_not_found_without_frontend_build(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(main, "FRONTEND_DIST", tmp_path)

    with TestClient(main.app) as client:
        response = client.get("/")

    assert response.status_code == 404
    assert response.json() == {"detail": "Frontend build is not available"}
