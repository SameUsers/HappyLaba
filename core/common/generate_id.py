import uuid
from uuid import UUID

def generate_uuid()->UUID:
    return str(uuid.uuid4())