import pytest

from app.api.dto.task_dto import TaskValidationDataDTO, TaskValidationResponseDTO
from app.api.services.task_service import task_service

pytestmark = pytest.mark.anyio("asyncio")


@pytest.mark.anyio
async def test_task_validation_endpoint_returns_signature(async_client, monkeypatch):
    """Ensure /task/{id}/validate delegates to the task service and returns its DTO."""

    sample_signature = "0xabc123"
    sample_task_id = "task-1"

    async def fake_validate_task_for_user(task_id: str, user_id: str):
        assert task_id == sample_task_id
        return TaskValidationResponseDTO(
            success=True,
            message="Validated",
            data=TaskValidationDataDTO(
                task_id=task_id,
                user_wallet="0x000000000000000000000000000000000000dEaD",
                actual_balance="100",
                required_balance="10",
                signature=sample_signature,
                verification_hash="hash123",
                task_details={"id": task_id},
            ),
        )

    monkeypatch.setattr(
        task_service, "validate_task_for_user", fake_validate_task_for_user
    )

    response = await async_client.post(f"/api/v1/task/{sample_task_id}/validate")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["signature"] == sample_signature
