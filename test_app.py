"""
ACEest Fitness & Gym – Pytest Test Suite
Tests cover: health, programs, clients, calorie calculation, validation,
CRUD operations, and error handling.
"""

import pytest
import json
from app import app, clients, calculate_calories, validate_client_payload, PROGRAMS


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    """Flask test client with fresh in-memory store per test."""
    app.config["TESTING"] = True
    with app.test_client() as c:
        clients.clear()
        yield c
        clients.clear()


VALID_CLIENT = {
    "name": "Arjun Kumar",
    "age": 28,
    "weight_kg": 75.0,
    "program": "Fat Loss (FL)",
}


# ── Health & Root ─────────────────────────────────────────────────────────────

class TestHealthAndRoot:
    def test_root_returns_200(self, client):
        res = client.get("/")
        assert res.status_code == 200

    def test_root_contains_service_name(self, client):
        data = res = client.get("/").get_json()
        assert "ACEest" in data["service"]

    def test_health_returns_healthy(self, client):
        res = client.get("/health")
        assert res.status_code == 200
        assert res.get_json()["status"] == "healthy"


# ── Programs ──────────────────────────────────────────────────────────────────

class TestPrograms:
    def test_list_programs_returns_all_three(self, client):
        res = client.get("/programs")
        assert res.status_code == 200
        programs = res.get_json()["programs"]
        assert len(programs) == 3

    def test_list_programs_contains_fat_loss(self, client):
        programs = client.get("/programs").get_json()["programs"]
        assert "Fat Loss (FL)" in programs

    def test_list_programs_contains_muscle_gain(self, client):
        programs = client.get("/programs").get_json()["programs"]
        assert "Muscle Gain (MG)" in programs

    def test_list_programs_contains_beginner(self, client):
        programs = client.get("/programs").get_json()["programs"]
        assert "Beginner (BG)" in programs

    def test_get_program_detail(self, client):
        res = client.get("/programs/Fat Loss (FL)")
        assert res.status_code == 200
        data = res.get_json()
        assert data["name"] == "Fat Loss (FL)"
        assert "workout" in data
        assert "diet" in data
        assert "calorie_factor" in data

    def test_get_program_muscle_gain(self, client):
        res = client.get("/programs/Muscle Gain (MG)")
        assert res.status_code == 200
        assert res.get_json()["calorie_factor"] == 35

    def test_get_program_beginner(self, client):
        res = client.get("/programs/Beginner (BG)")
        assert res.status_code == 200
        assert res.get_json()["calorie_factor"] == 26

    def test_get_nonexistent_program_returns_404(self, client):
        res = client.get("/programs/Powerlifting")
        assert res.status_code == 404


# ── Calorie Calculation ───────────────────────────────────────────────────────

class TestCalorieCalculation:
    def test_fat_loss_calories(self):
        assert calculate_calories(70.0, "Fat Loss (FL)") == 1540  # 70 * 22

    def test_muscle_gain_calories(self):
        assert calculate_calories(80.0, "Muscle Gain (MG)") == 2800

    def test_beginner_calories(self):
        assert calculate_calories(60.0, "Beginner (BG)") == 1560

    def test_calories_scale_linearly(self):
        c1 = calculate_calories(50.0, "Fat Loss (FL)")
        c2 = calculate_calories(100.0, "Fat Loss (FL)")
        assert c2 == c1 * 2

    def test_calories_returns_integer(self):
        result = calculate_calories(73.5, "Fat Loss (FL)")
        assert isinstance(result, int)


# ── Validation ────────────────────────────────────────────────────────────────

class TestValidation:
    def test_valid_payload_returns_no_errors(self):
        assert validate_client_payload(VALID_CLIENT) == []

    def test_missing_name_returns_error(self):
        data = {**VALID_CLIENT, "name": ""}
        errors = validate_client_payload(data)
        assert any("name" in e for e in errors)

    def test_invalid_program_returns_error(self):
        data = {**VALID_CLIENT, "program": "Powerlifting"}
        errors = validate_client_payload(data)
        assert any("program" in e for e in errors)

    def test_zero_weight_returns_error(self):
        data = {**VALID_CLIENT, "weight_kg": 0}
        errors = validate_client_payload(data)
        assert any("weight_kg" in e for e in errors)

    def test_negative_weight_returns_error(self):
        data = {**VALID_CLIENT, "weight_kg": -10}
        errors = validate_client_payload(data)
        assert any("weight_kg" in e for e in errors)

    def test_zero_age_returns_error(self):
        data = {**VALID_CLIENT, "age": 0}
        errors = validate_client_payload(data)
        assert any("age" in e for e in errors)

    def test_missing_weight_returns_error(self):
        data = {k: v for k, v in VALID_CLIENT.items() if k != "weight_kg"}
        errors = validate_client_payload(data)
        assert any("weight_kg" in e for e in errors)


# ── Client CRUD ───────────────────────────────────────────────────────────────

class TestClientCreate:
    def test_create_client_returns_201(self, client):
        res = client.post("/clients", json=VALID_CLIENT)
        assert res.status_code == 201

    def test_create_client_returns_correct_name(self, client):
        data = client.post("/clients", json=VALID_CLIENT).get_json()
        assert data["name"] == VALID_CLIENT["name"]

    def test_create_client_calculates_calories(self, client):
        data = client.post("/clients", json=VALID_CLIENT).get_json()
        expected = calculate_calories(VALID_CLIENT["weight_kg"], VALID_CLIENT["program"])
        assert data["calories_per_day"] == expected

    def test_create_client_missing_name_returns_400(self, client):
        payload = {**VALID_CLIENT, "name": ""}
        res = client.post("/clients", json=payload)
        assert res.status_code == 400

    def test_create_client_invalid_program_returns_400(self, client):
        payload = {**VALID_CLIENT, "program": "Olympic Lifting"}
        res = client.post("/clients", json=payload)
        assert res.status_code == 400

    def test_create_client_stores_adherence_default(self, client):
        data = client.post("/clients", json=VALID_CLIENT).get_json()
        assert data["adherence_pct"] == 0

    def test_create_client_with_custom_adherence(self, client):
        payload = {**VALID_CLIENT, "adherence_pct": 85}
        data = client.post("/clients", json=payload).get_json()
        assert data["adherence_pct"] == 85


class TestClientRead:
    def test_list_clients_empty_at_start(self, client):
        data = client.get("/clients").get_json()
        assert data["clients"] == []

    def test_list_clients_after_creation(self, client):
        client.post("/clients", json=VALID_CLIENT)
        data = client.get("/clients").get_json()
        assert len(data["clients"]) == 1

    def test_get_existing_client(self, client):
        client.post("/clients", json=VALID_CLIENT)
        res = client.get(f"/clients/{VALID_CLIENT['name']}")
        assert res.status_code == 200

    def test_get_nonexistent_client_returns_404(self, client):
        res = client.get("/clients/Nobody")
        assert res.status_code == 404

    def test_client_calories_endpoint(self, client):
        client.post("/clients", json=VALID_CLIENT)
        res = client.get(f"/clients/{VALID_CLIENT['name']}/calories")
        assert res.status_code == 200
        data = res.get_json()
        assert "calories_per_day" in data

    def test_client_calories_nonexistent_returns_404(self, client):
        res = client.get("/clients/Ghost/calories")
        assert res.status_code == 404


class TestClientUpdate:
    def test_update_client_program(self, client):
        client.post("/clients", json=VALID_CLIENT)
        updated = {**VALID_CLIENT, "program": "Muscle Gain (MG)"}
        res = client.put(f"/clients/{VALID_CLIENT['name']}", json=updated)
        assert res.status_code == 200
        assert res.get_json()["program"] == "Muscle Gain (MG)"

    def test_update_recalculates_calories(self, client):
        client.post("/clients", json=VALID_CLIENT)
        updated = {**VALID_CLIENT, "program": "Muscle Gain (MG)"}
        data = client.put(f"/clients/{VALID_CLIENT['name']}", json=updated).get_json()
        expected = calculate_calories(VALID_CLIENT["weight_kg"], "Muscle Gain (MG)")
        assert data["calories_per_day"] == expected

    def test_update_nonexistent_client_returns_404(self, client):
        res = client.put("/clients/Nobody", json=VALID_CLIENT)
        assert res.status_code == 404


class TestClientDelete:
    def test_delete_client_returns_200(self, client):
        client.post("/clients", json=VALID_CLIENT)
        res = client.delete(f"/clients/{VALID_CLIENT['name']}")
        assert res.status_code == 200

    def test_delete_removes_client(self, client):
        client.post("/clients", json=VALID_CLIENT)
        client.delete(f"/clients/{VALID_CLIENT['name']}")
        res = client.get(f"/clients/{VALID_CLIENT['name']}")
        assert res.status_code == 404

    def test_delete_nonexistent_client_returns_404(self, client):
        res = client.delete("/clients/Ghost")
        assert res.status_code == 404


# ── Multiple Clients ──────────────────────────────────────────────────────────

class TestMultipleClients:
    def test_create_multiple_clients(self, client):
        client.post("/clients", json=VALID_CLIENT)
        client.post("/clients", json={
            "name": "Priya Rajan",
            "age": 24,
            "weight_kg": 58.0,
            "program": "Beginner (BG)",
        })
        data = client.get("/clients").get_json()
        assert len(data["clients"]) == 2

    def test_different_programs_different_calories(self, client):
        c1_data = client.post("/clients", json=VALID_CLIENT).get_json()
        c2_data = client.post("/clients", json={
            "name": "Priya Rajan",
            "age": 24,
            "weight_kg": VALID_CLIENT["weight_kg"],
            "program": "Muscle Gain (MG)",
        }).get_json()
        assert c1_data["calories_per_day"] != c2_data["calories_per_day"]


# ── Error Handling ────────────────────────────────────────────────────────────

class TestErrorHandling:
    def test_unknown_route_returns_404(self, client):
        res = client.get("/nonexistent")
        assert res.status_code == 404

    def test_post_to_readonly_route_returns_405(self, client):
        res = client.post("/programs")
        assert res.status_code == 405

    def test_invalid_json_body_returns_400(self, client):
        res = client.post(
            "/clients",
            data="not-json",
            content_type="application/json",
        )
        assert res.status_code == 400
