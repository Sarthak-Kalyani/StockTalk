
from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_and_search_catalogue(client):
    payload = {
        "vendor_id": 1,
        "product_name": "Basmati Rice",
        "description": "Premium rice",
        "category": "Groceries",
        "price": 120.0,
        "unit": "kg",
        "available_quantity": 50,
        "is_available": True,
    }

    create_response = client.post(
        "/vendors/catalogue",
        json=payload,
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["product_name"] == "Basmati Rice"
    assert created["vendor_id"] == 1

    search_response = client.get(
        "/vendors/catalogue",
        params={"search": "Basmati", "vendor_id": 1},
    )

    assert search_response.status_code == 200
    products = search_response.json()
    assert len(products) == 1
    assert products[0]["product_name"] == "Basmati Rice"


def test_save_vendor_location(client):
    payload = {
        "vendor_id": 1,
        "latitude": 28.4744,
        "longitude": 77.5040,
        "address": "Greater Noida",
        "city": "Greater Noida",
        "service_radius_km": 10,
    }

    response = client.post("/vendors/location", json=payload)

    assert response.status_code == 200
    assert response.json()["vendor_id"] == 1
    assert response.json()["city"] == "Greater Noida"


def test_create_conversation_and_list_it(client):
    payload = {
        "shopkeeper_id": 100,
        "vendor_id": 1,
    }

    response = client.post("/conversations", json=payload)

    assert response.status_code == 201
    conversation = response.json()
    assert conversation["shopkeeper_id"] == 100
    assert conversation["vendor_id"] == 1

    list_response = client.get(
        "/conversations",
        params={"user_id": 100},
    )

    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["id"] == conversation["id"]


def test_send_and_read_messages(client):
    conversation_response = client.post(
        "/conversations",
        json={"shopkeeper_id": 100, "vendor_id": 1},
    )
    assert conversation_response.status_code == 201

    conversation_id = conversation_response.json()["id"]

    send_response = client.post(
        f"/conversations/{conversation_id}/messages",
        json={
            "sender_id": 100,
            "content": "Hello, do you have rice in stock?",
        },
    )

    assert send_response.status_code == 201
    assert send_response.json()["content"] == (
        "Hello, do you have rice in stock?"
    )

    history_response = client.get(
        f"/conversations/{conversation_id}/messages",
        params={"user_id": 1},
    )

    assert history_response.status_code == 200
    assert len(history_response.json()) == 1
    assert history_response.json()[0]["sender_id"] == 100
    assert history_response.json()[0]["is_read"] is False

    read_response = client.post(
        f"/conversations/{conversation_id}/read",
        params={"user_id": 1},
    )

    assert read_response.status_code == 200
    assert read_response.json()["messages_marked_as_read"] == 1

    updated_history = client.get(
        f"/conversations/{conversation_id}/messages",
        params={"user_id": 1},
    )

    assert updated_history.status_code == 200
    assert updated_history.json()[0]["is_read"] is True


def test_non_participant_cannot_read_chat(client):
    conversation_response = client.post(
        "/conversations",
        json={"shopkeeper_id": 100, "vendor_id": 1},
    )
    conversation_id = conversation_response.json()["id"]

    response = client.get(
        f"/conversations/{conversation_id}/messages",
        params={"user_id": 999},
    )

    assert response.status_code == 403


def test_non_participant_cannot_send_message(client):
    conversation_response = client.post(
        "/conversations",
        json={"shopkeeper_id": 100, "vendor_id": 1},
    )
    conversation_id = conversation_response.json()["id"]

    response = client.post(
        f"/conversations/{conversation_id}/messages",
        json={
            "sender_id": 999,
            "content": "Unauthorized message",
        },
    )

    assert response.status_code == 403
