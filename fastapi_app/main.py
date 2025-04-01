from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from .db import get_db
from .models import Conversation, Message, MedicalImage, ConversationSchema, MessageSchema, MedicalImageSchema

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "FastAPI is running!"}

@app.get("/conversations/", response_model=list[ConversationSchema])
def get_conversations(db: Session = Depends(get_db)):
    conversations = Conversation.objects.all()
    return [ConversationSchema(id=c.id, user_id=c.user_id, start_time=c.start_time, last_interaction=c.last_interaction) for c in conversations]

@app.get("/messages/{conversation_id}", response_model=list[MessageSchema])
def get_messages(conversation_id: int, db: Session = Depends(get_db)):
    messages = Message.objects.filter(conversation_id=conversation_id)
    return [MessageSchema(id=m.id, conversation_id=m.conversation_id, content=m.content, sender=m.sender, timestamp=m.timestamp) for m in messages]

@app.get("/images/{conversation_id}", response_model=list[MedicalImageSchema])
def get_images(conversation_id: int, db: Session = Depends(get_db)):
    images = MedicalImage.objects.filter(conversation_id=conversation_id)
    return [MedicalImageSchema(id=img.id, conversation_id=img.conversation_id, image=img.image.url, analysis_result=img.analysis_result, uploaded_at=img.uploaded_at) for img in images]
