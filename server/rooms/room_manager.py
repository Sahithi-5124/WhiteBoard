import threading
import uuid

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Room:
    room_id: str
    name: str
    host_id: str

    # user_id -> username
    participants: dict = field(default_factory=dict)

    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class RoomManager:

    def __init__(self):
        self.rooms = {}
        self.user_rooms = {}

        self.lock = threading.Lock()

    def generate_room_id(self):
        return uuid.uuid4().hex[:8].upper()

    def create_room(self, user_id, username, room_name="Untitled Room"):

        if not isinstance(room_name, str):
            raise ValueError("Room name must be a string.")

        room_name = room_name.strip()

        if not room_name or len(room_name) > 50:
            raise ValueError(
                "Room name must contain between 1 and 50 characters."
            )

        with self.lock:

            if user_id in self.user_rooms:
                raise ValueError("You are already in a room.")

            room_id = self.generate_room_id()

            while room_id in self.rooms:
                room_id = self.generate_room_id()

            room = Room(
                room_id=room_id,
                name=room_name,
                host_id=user_id
            )

            room.participants[user_id] = username

            self.rooms[room_id] = room
            self.user_rooms[user_id] = room_id

            return self._create_snapshot(room)

    def join_room(self, user_id, username, room_id):

        if not isinstance(room_id, str):
            raise ValueError("Room code must be a string.")

        room_id = room_id.strip().upper()

        if not room_id:
            raise ValueError("Room code cannot be empty.")

        with self.lock:

            if user_id in self.user_rooms:
                raise ValueError("You are already in a room.")

            room = self.rooms.get(room_id)

            if room is None:
                raise ValueError("Room does not exist.")

            room.participants[user_id] = username
            self.user_rooms[user_id] = room_id

            return self._create_snapshot(room)

    def leave_room(self, user_id):

        with self.lock:

            room_id = self.user_rooms.get(user_id)

            if room_id is None:
                raise ValueError("You are not in a room.")

            room = self.rooms[room_id]

            username = room.participants.pop(user_id)

            del self.user_rooms[user_id]

            new_host_id = None
            room_deleted = False

            if not room.participants:

                del self.rooms[room_id]
                room_deleted = True

            elif room.host_id == user_id:

                new_host_id = next(iter(room.participants))
                room.host_id = new_host_id

            return {
                "room_id": room_id,
                "user_id": user_id,
                "username": username,
                "new_host_id": new_host_id,
                "room_deleted": room_deleted
            }

    def get_user_room_id(self, user_id):

        with self.lock:
            return self.user_rooms.get(user_id)

    def get_participants(self, room_id):

        with self.lock:

            room = self.rooms.get(room_id)

            if room is None:
                raise ValueError("Room does not exist.")

            return [
                {
                    "user_id": user_id,
                    "username": username,
                    "is_host": user_id == room.host_id
                }
                for user_id, username in room.participants.items()
            ]

    def get_room_snapshot(self, room_id):

        with self.lock:

            room = self.rooms.get(room_id)

            if room is None:
                raise ValueError("Room does not exist.")

            return self._create_snapshot(room)

    def _create_snapshot(self, room):

        return {
            "room_id": room.room_id,
            "name": room.name,
            "host_id": room.host_id,
            "created_at": room.created_at,
            "participants": [
                {
                    "user_id": user_id,
                    "username": username,
                    "is_host": user_id == room.host_id
                }
                for user_id, username in room.participants.items()
            ]
        }