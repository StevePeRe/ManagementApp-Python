import json


class TestHealthEndpoint:
    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestCreateTask:
    def test_create_task(self, client):
        response = client.post(
            "/api/tasks",
            json={"name": "New Task"},
        )
        assert response.status_code == 201
        assert response.headers["Location"] == "/api/tasks/1"

    def test_create_task_empty_name(self, client):
        response = client.post(
            "/api/tasks",
            json={"name": "   "},
        )
        assert response.status_code == 400
        data = response.json()
        assert "name" in data["errors"]

    def test_create_task_missing_name(self, client):
        response = client.post(
            "/api/tasks",
            json={},
        )
        assert response.status_code == 400

    def test_create_task_with_state(self, client):
        response = client.post(
            "/api/tasks",
            json={"name": "Running Task", "state": "RUNNING"},
        )
        assert response.status_code == 201


class TestGetTasks:
    def test_get_all_tasks(self, client, sample_task):
        response = client.get("/api/tasks")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Task"
        assert data[0]["state"] == "CREATED"

    def test_get_all_tasks_empty(self, client):
        response = client.get("/api/tasks")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_task_by_id(self, client, sample_task):
        response = client.get(f"/api/tasks/{sample_task.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Task"
        assert data["id"] == sample_task.id

    def test_get_task_not_found(self, client):
        response = client.get("/api/tasks/999")
        assert response.status_code == 404
        data = response.json()
        assert "999" in data["message"]
        assert data["exception"] == "TaskNotFoundError"


class TestUpdateTask:
    def test_update_task(self, client, sample_task):
        response = client.put(
            f"/api/tasks/{sample_task.id}",
            json={"name": "Updated", "state": "RUNNING"},
        )
        assert response.status_code == 202

        get_response = client.get(f"/api/tasks/{sample_task.id}")
        assert get_response.json()["name"] == "Updated"
        assert get_response.json()["state"] == "RUNNING"

    def test_update_task_not_found(self, client):
        response = client.put(
            "/api/tasks/999",
            json={"name": "Nope", "state": "CREATED"},
        )
        assert response.status_code == 404

    def test_update_task_invalid_state(self, client, sample_task):
        response = client.put(
            f"/api/tasks/{sample_task.id}",
            json={"name": "Bad", "state": "INVALID"},
        )
        assert response.status_code == 400


class TestDeleteTask:
    def test_delete_task(self, client, sample_task):
        response = client.delete(f"/api/tasks/{sample_task.id}")
        assert response.status_code == 202

        get_response = client.get(f"/api/tasks/{sample_task.id}")
        assert get_response.status_code == 404

    def test_delete_task_not_found(self, client):
        response = client.delete("/api/tasks/999")
        assert response.status_code == 404
