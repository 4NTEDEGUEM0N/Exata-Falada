import pytest
from models.task_model import TaskModel
from routes.converter_routes import TaskStatusEnum

@pytest.fixture
def auth_headers(client):
    login_response = client.post(
        "/user/token",
        data={"username": "normal_test", "password": "testpass"}
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def admin_auth_headers(client):
    login_response = client.post(
        "/user/token",
        data={"username": "admin_test", "password": "testpass"}
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def test_user_id(client, auth_headers):
    me_response = client.get("/user/me", headers=auth_headers)
    return me_response.json()["id"]

@pytest.fixture
def admin_user_id(client, admin_auth_headers):
    me_response = client.get("/user/me", headers=admin_auth_headers)
    return me_response.json()["id"]

@pytest.fixture
def dummy_tasks(setup_db, test_user_id, admin_user_id):
    task1 = TaskModel(
        pdf_filename="test1.pdf",
        status=TaskStatusEnum.COMPLETED.value,
        user_id=test_user_id,
        html_filename="test1.html",
        storage_provider="local"
    )
    task2 = TaskModel(
        pdf_filename="test2.pdf",
        status=TaskStatusEnum.CREATED.value,
        user_id=admin_user_id,
        storage_provider="local"
    )
    setup_db.add(task1)
    setup_db.add(task2)
    setup_db.commit()
    return task1.id, task2.id

def test_get_all_tasks_admin(client, admin_auth_headers):
    response = client.get("/task/", headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "page" in data
    assert "total_pages" in data
    assert "tasks" in data

def test_get_all_tasks_non_admin(client, auth_headers):
    response = client.get("/task/", headers=auth_headers)
    assert response.status_code == 401
    assert response.json() == {"detail": "UNAUTHORIZED"}

def test_get_user_tasks_own(client, auth_headers, test_user_id):
    response = client.get(f"/task/user/{test_user_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "page" in data
    assert "total_pages" in data
    assert "tasks" in data

def test_get_user_tasks_admin(client, admin_auth_headers, test_user_id):
    response = client.get(f"/task/user/{test_user_id}", headers=admin_auth_headers)
    assert response.status_code == 200
    assert "tasks" in response.json()

def test_get_user_tasks_other_user(client, auth_headers, admin_user_id):
    response = client.get(f"/task/user/{admin_user_id}", headers=auth_headers)
    assert response.status_code == 401
    assert response.json() == {"detail": "UNAUTHORIZED"}

def test_get_task_by_id_own(client, auth_headers, dummy_tasks):
    task_id, _ = dummy_tasks
    response = client.get(f"/task/{task_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == task_id

def test_get_task_by_id_admin(client, admin_auth_headers, dummy_tasks):
    task_id, _ = dummy_tasks
    response = client.get(f"/task/{task_id}", headers=admin_auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == task_id

def test_get_task_by_id_other_user(client, auth_headers, dummy_tasks):
    _, admin_task_id = dummy_tasks
    response = client.get(f"/task/{admin_task_id}", headers=auth_headers)
    assert response.status_code == 401
    assert response.json() == {"detail": "UNAUTHORIZED"}

def test_get_task_not_found(client, auth_headers):
    response = client.get("/task/9999", headers=auth_headers)
    assert response.status_code == 404
    assert response.json() == {"detail": "NOT FOUND"}

def test_delete_task_unauthorized(client, auth_headers, dummy_tasks):
    _, admin_task_id = dummy_tasks
    response = client.post(f"/task/delete/{admin_task_id}", headers=auth_headers)
    assert response.status_code == 401
    assert response.json() == {"detail": "UNAUTHORIZED"}

def test_delete_task_not_found(client, auth_headers):
    response = client.post("/task/delete/9999", headers=auth_headers)
    assert response.status_code == 404
    assert response.json() == {"detail": "NOT FOUND"}

def test_delete_task_own(client, auth_headers, dummy_tasks):
    task_id, _ = dummy_tasks
    response = client.post(f"/task/delete/{task_id}", headers=auth_headers)
    assert response.status_code == 204
    
    get_response = client.get(f"/task/{task_id}", headers=auth_headers)
    assert get_response.status_code == 404

def test_delete_task_admin(client, admin_auth_headers, setup_db, test_user_id):
    task = TaskModel(
        pdf_filename="test3.pdf",
        status=TaskStatusEnum.CREATED.value,
        user_id=test_user_id,
        storage_provider="local"
    )
    setup_db.add(task)
    setup_db.commit()
    
    response = client.post(f"/task/delete/{task.id}", headers=admin_auth_headers)
    assert response.status_code == 204
