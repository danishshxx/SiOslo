import io
import pandas as pd
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.analysis import InnovationBlueprintItem

client = TestClient(app)

# Data CSV valid untuk test
VALID_CSV_CONTENT = (
    "tanggal,nama_produk,kategori,terjual_bulan_ini,sisa_stok,harga_satuan\n"
    "01/06/2026,Kopi Susu Aren,Minuman,120,30,18000\n"
    "02/06/2026,Keripik Singkong Pedas,Makanan Ringan,80,45,12000\n"
    "03/06/2026,Es Teh Nusantara,Minuman,200,15,8000\n"
).encode("utf-8")

# Data CSV tidak valid (hanya satu kolom)
INVALID_CSV_CONTENT = b"tanggal\n01/06/2026\n"


def _mock_db_session():
    """Membuat mock database session yang bisa menerima operasi SQLAlchemy."""
    session = MagicMock()
    session.query.return_value.all.return_value = []   # demographics, competitor kosong
    session.add.return_value = None
    session.commit.return_value = None
    session.flush.return_value = None
    session.refresh.return_value = None
    return session


def test_analyze_endpoint_success(mocker):
    """Endpoint /analyze harus mengembalikan 200 dengan respons lengkap."""

    # ============ 1. DEFINISIKAN MOCK BLUEPRINT TERLEBIH DAHULU ============
    mock_blueprint = [
        InnovationBlueprintItem(
            id="inv-001",
            title="Kopi Susu Aren Premium",
            target_location="Jakarta Selatan",
            recommended_price=20000,
            competitor_price_ceiling=25000,
            justification="Korelasi tinggi dengan pasar",
            risk_factors=["Fluktuasi harga susu"],
            whatsapp_copy_text="Coba Kopi Susu Aren Premium! ☕"
        )
    ]

    # ============ 2. MOCK PARSER JAY ============
    mock_parse_result = {
        "status": "success",
        "cleaned_data": pd.DataFrame({
            "product_name": ["Kopi Susu Aren"],
            "category": ["Minuman"],
            "qty_sold": [120],
            "remaining_stock": [30],
            "unit_price": [18000]
        }),
        "data_health": {
            "reliability_score": 85,
            "status_color": "green",
            "warning_message": "Sehat",
            "score_breakdown": {"base_score": 100, "penalty": 15},
            "issues": [{"row_index": None, "column": "category", "issue_type": "missing_value", "detail": "kosong"}]
        }
    }
    # Mock di dua tempat agar referensi lokal ikut terganti
    mocker.patch("app.services.csv_parser.parse_and_validate", return_value=mock_parse_result)
    mocker.patch("app.api.v1.endpoints.analyze.parse_and_validate", return_value=mock_parse_result)

    # ============ 3. MOCK KORELASI CH3COO ============
    mock_corr_result = {
        "status": "success",
        "correlation_data": {
            "keyword_overlap": {
                "per_product": [
                    {
                        "product_name": "Kopi Susu Aren",
                        "category": "Minuman",
                        "keyword_overlap_score": 0.65,
                        "matched_keywords": ["kopi", "susu"],
                        "matched_segment": "Pecinta Kopi"
                    }
                ]
            },
            "price_competitiveness": {
                "per_product": [
                    {
                        "product_name": "Kopi Susu Aren",
                        "price_competitiveness_score": 0.8,
                        "user_price": 18000,
                        "avg_competitor_price": 22000
                    }
                ]
            }
        }
    }
    mocker.patch("app.services.correlation_engine.compute_correlation", return_value=mock_corr_result)

    # ============ 4. MOCK LLM SERVICE ============
    mocker.patch("app.services.llm_service.generate_innovation_blueprint", return_value=mock_blueprint)
    mocker.patch("app.api.v1.endpoints.analyze.generate_innovation_blueprint", return_value=mock_blueprint)

    # ============ 5. MOCK DATABASE SESSION ============
    mock_db = _mock_db_session()
    mocker.patch("app.api.v1.endpoints.analyze.get_db", return_value=iter([mock_db]))

    # ============ 6. KIRIM REQUEST ============
    response = client.post(
        "/api/v1/analyze/",
        files={"file": ("test.csv", io.BytesIO(VALID_CSV_CONTENT), "text/csv")},
        data={"target_lokasi": "Jakarta Selatan"}
    )

    # ============ 7. ASSERTIONS ============
    assert response.status_code == 200
    json_resp = response.json()
    assert json_resp["status"] == "success"
    assert json_resp["data_health"]["reliability_score"] == 85
    assert json_resp["data_health"]["status_color"] == "green"
    assert len(json_resp["innovation_blueprint"]) == 1
    assert json_resp["innovation_blueprint"][0]["title"] == "Kopi Susu Aren Premium"


def test_analyze_endpoint_csv_error(mocker):
    """Endpoint harus mengembalikan 422 jika CSV tidak valid."""
    mock_parse_result = {
        "status": "error",
        "data_health": {
            "warning_message": "Kolom wajib tidak ditemukan"
        }
    }
    mocker.patch("app.services.csv_parser.parse_and_validate", return_value=mock_parse_result)
    mocker.patch("app.api.v1.endpoints.analyze.parse_and_validate", return_value=mock_parse_result)

    mock_db = _mock_db_session()
    mocker.patch("app.api.v1.endpoints.analyze.get_db", return_value=iter([mock_db]))

    response = client.post(
        "/api/v1/analyze/",
        files={"file": ("invalid.csv", io.BytesIO(INVALID_CSV_CONTENT), "text/csv")},
        data={"target_lokasi": "Bandung"}
    )

    assert response.status_code == 422
    assert "Kolom wajib" in response.json()["detail"]


def test_analyze_endpoint_no_file(mocker):
    """Tanpa file, endpoint harus mengembalikan 422."""
    mock_db = _mock_db_session()
    mocker.patch("app.api.v1.endpoints.analyze.get_db", return_value=iter([mock_db]))

    response = client.post(
        "/api/v1/analyze/",
        data={"target_lokasi": "Surabaya"}
    )
    assert response.status_code == 422


def test_list_routes():
    """Debug: cetak semua route yang terdaftar (optional)."""
    for route in app.routes:
        if hasattr(route, "methods"):
            print(route.path, route.methods)