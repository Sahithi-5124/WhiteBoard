import pytest

from server.rooms.room_manager import RoomManager


def test_create_room():

    manager = RoomManager()

    room = manager.create_room("u1", "Alice", "Physics")

    assert room["name"] == "Physics"
    assert len(room["room_id"]) == 8
    assert room["host_id"] == "u1"
    assert len(room["participants"]) == 1
    assert room["participants"][0]["is_host"] is True


def test_join_existing_room():

    manager = RoomManager()

    room = manager.create_room("u1", "Alice", "Physics")

    joined_room = manager.join_room(
        "u2",
        "Bob",
        room["room_id"]
    )

    assert len(joined_room["participants"]) == 2


def test_join_nonexistent_room():

    manager = RoomManager()

    with pytest.raises(ValueError):
        manager.join_room("u1", "Alice", "INVALID1")


def test_user_cannot_join_multiple_rooms():

    manager = RoomManager()

    room1 = manager.create_room("u1", "Alice", "Physics")
    room2 = manager.create_room("u2", "Bob", "Chemistry")

    with pytest.raises(ValueError):
        manager.join_room("u1", "Alice", room2["room_id"])


def test_user_can_leave_room():

    manager = RoomManager()

    room = manager.create_room("u1", "Alice", "Physics")

    result = manager.leave_room("u1")

    assert result["room_deleted"] is True
    assert manager.get_user_room_id("u1") is None


def test_host_transfers_when_leaving():

    manager = RoomManager()

    room = manager.create_room("u1", "Alice", "Physics")

    manager.join_room("u2", "Bob", room["room_id"])

    result = manager.leave_room("u1")

    assert result["new_host_id"] == "u2"

    updated_room = manager.get_room_snapshot(room["room_id"])

    assert updated_room["host_id"] == "u2"
    assert updated_room["participants"][0]["is_host"] is True


def test_empty_room_is_deleted():

    manager = RoomManager()

    room = manager.create_room("u1", "Alice", "Physics")

    manager.leave_room("u1")

    with pytest.raises(ValueError):
        manager.get_room_snapshot(room["room_id"])


def test_room_name_validation():

    manager = RoomManager()

    with pytest.raises(ValueError):
        manager.create_room("u1", "Alice", "")

    with pytest.raises(ValueError):
        manager.create_room("u1", "Alice", "A" * 51)