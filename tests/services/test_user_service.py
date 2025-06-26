import pytest
from carmain.models.users import User
from carmain.schemas.user_schema import UserSchema
from carmain.services.user_service import UserService

@pytest.fixture
def user_service(mock_repository):
    return UserService(user_repository=mock_repository)


@pytest.mark.asyncio
async def test_get_by_id_calls_repository(mock_repository, user_service):
    user_id = 1
    fake_user = User(id=user_id, email="test@example.com")
    mock_repository.get_by_id.return_value = fake_user
    result = await user_service.get_by_id(user_id)
    assert result is fake_user
    mock_repository.get_by_id.assert_awaited_once_with(user_id)


@pytest.mark.asyncio
async def test_add_calls_create_and_passes_correct_user(mock_repository, user_service):
    fake_user = User(id=7, email="new@example.com")
    mock_repository.create.return_value = fake_user
    schema = UserSchema(id=7, email="new@example.com")
    result = await user_service.add(schema)
    assert result is fake_user
    assert mock_repository.create.call_count == 1
    created_arg = mock_repository.create.call_args.args[0]
    assert isinstance(created_arg, User)
    assert created_arg.id == 7
    assert created_arg.email == "new@example.com"


@pytest.mark.asyncio
async def test_patch_calls_update_by_id_with_correct_data(mock_repository, user_service):
    user_id = 3
    updated_user = User(id=user_id, email="upd@example.com")
    mock_repository.update_by_id.return_value = updated_user
    schema = UserSchema(id=user_id, email="upd@example.com")
    result = await user_service.patch(user_id, schema)
    assert result is updated_user
    expected_data = {"id": user_id, "email": "upd@example.com"}
    mock_repository.update_by_id.assert_awaited_once_with(user_id, expected_data)


@pytest.mark.asyncio
async def test_remove_by_id_calls_delete_by_id_and_returns_user(mock_repository, user_service):
    user_id = 4
    deleted_user = User(id=user_id, email="del@example.com")
    mock_repository.delete_by_id.return_value = deleted_user
    result = await user_service.remove_by_id(user_id)
    assert result is deleted_user
    mock_repository.delete_by_id.assert_awaited_once_with(user_id)


@pytest.mark.asyncio
async def test_all_returns_all_users(mock_repository, user_service):
    users = [User(id=5, email="a@x.com"), User(id=6, email="b@y.com")]
    mock_repository.all.return_value = users
    result = await user_service.all()
    assert result == users
    mock_repository.all.assert_awaited_once()