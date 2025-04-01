from medicalapp.models import Conversation, Message, MedicalImage  # Import from Django models
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Pydantic schemas for FastAPI
class MessageSchema(BaseModel):
    id: int
    conversation_id: int
    content: str
    sender: str
    timestamp: datetime

class ConversationSchema(BaseModel):
    id: int
    user_id: int
    start_time: datetime
    last_interaction: datetime
    messages: List[MessageSchema] = []

class MedicalImageSchema(BaseModel):
    id: int
    conversation_id: int
    image: str  # Path to image
    analysis_result: Optional[str]
    uploaded_at: datetime
