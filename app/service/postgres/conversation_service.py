"""
Conversation service for managing AI chat conversations.
"""

import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from app.core.db.schema import Conversation, Message, User, Patient
from app.dto.agent import ConversationInfo
from app.service.postgres.reference_manager import ReferenceManager

class ConversationService:
    """Service for managing conversations and messages."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.reference_manager = ReferenceManager(db)
    
    async def create_conversation(
        self, 
        doctor_id: str, 
        patient_mrn: str, 
        title: Optional[str] = None
    ) -> str:
        """Create a new conversation."""
        conversation_id = str(uuid.uuid4())
        
        # Generate title from first message if not provided
        if not title:
            title = f"Conversation - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        conversation = Conversation(
            conversation_id=conversation_id,
            title=title,
            patient_mrn=patient_mrn,
            doctor_id=doctor_id
        )
        
        self.db.add(conversation)
        await self.db.flush()
        
        return conversation_id
    
    async def get_conversations_for_patient(
        self, 
        doctor_id: str, 
        patient_mrn: str,
        limit: int = 50
    ) -> List[ConversationInfo]:
        """Get all conversations for a patient."""
        # Subquery to count messages per conversation
        message_count_subquery = (
            select(
                Message.conversation_id,
                func.count(Message.message_id).label('message_count')
            )
            .group_by(Message.conversation_id)
            .subquery()
        )
        
        # Main query with message counts
        result = await self.db.execute(
            select(Conversation, message_count_subquery.c.message_count)
            .outerjoin(
                message_count_subquery,
                Conversation.conversation_id == message_count_subquery.c.conversation_id
            )
            .where(
                Conversation.doctor_id == doctor_id,
                Conversation.patient_mrn == patient_mrn
            )
            .order_by(desc(Conversation.last_updated))
            .limit(limit)
        )
        
        conversations = []
        for conv, msg_count in result:
            conversations.append(ConversationInfo(
                conversation_id=conv.conversation_id,
                title=conv.title,
                patient_mrn=conv.patient_mrn,
                doctor_id=conv.doctor_id,
                created_at=conv.created_at.isoformat(),
                last_updated=conv.last_updated.isoformat(),
                message_count=msg_count or 0
            ))
        
        return conversations
    
    async def get_conversation_messages(
        self, 
        conversation_id: str,
        doctor_id: str,
        limit: int = 50
    ) -> Optional[List[Message]]:
        """Get conversation messages (recent first)."""
        # First verify conversation exists and user has access
        conv_result = await self.db.execute(
            select(Conversation).where(
                Conversation.conversation_id == conversation_id,
                Conversation.doctor_id == doctor_id
            )
        )
        conversation = conv_result.scalar_one_or_none()
        
        if not conversation:
            return None
        
        # Get recent messages
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
            .limit(limit)
        )
        
        return result.scalars().all()
    
    async def add_message_to_conversation(
        self, 
        conversation_id: str,
        role: str,
        content: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Add a message to a conversation."""
        message_id = str(uuid.uuid4())
        
        message = Message(
            message_id=message_id,
            conversation_id=conversation_id,
            role=role,
            content=content,
            tool_calls=tool_calls
        )
        
        self.db.add(message)
        
        # Update conversation's last_updated timestamp
        conversation_result = await self.db.execute(
            select(Conversation).where(Conversation.conversation_id == conversation_id)
        )
        conversation = conversation_result.scalar_one()
        conversation.last_updated = datetime.utcnow()
        
        await self.db.flush()
        
        # Process references from tool calls - store all references returned by tools
        if tool_calls:
            reference_ids = []
            
            for tool_call in tool_calls:
                tool_name = tool_call.get("name", "")
                result_str = tool_call.get("result", "{}")
                
                # Handle web search external references
                if tool_name == "web_search":
                    # For web search, create external references for any hash references found
                    import re
                    hash_refs = re.findall(r'\[([a-f0-9]{6,12})\]', result_str)
                    
                    for hash_ref in hash_refs:
                        try:
                            # Create external reference with the specific hash ID
                            placeholder_url = f"https://external-source.example.com/{hash_ref}"
                            await self.reference_manager.create_external_reference(
                                url=placeholder_url,
                                title="External Medical Source",
                                reference_id=hash_ref  # Use the exact hash ID
                            )
                            reference_ids.append(hash_ref)
                        except Exception as e:
                            print(f"Error creating external reference {hash_ref}: {e}")
                            # Skip this reference if creation fails
                else:
                    # Handle internal references from medical record tools
                    try:
                        import json
                        result = json.loads(result_str) if isinstance(result_str, str) else result_str
                    except (json.JSONDecodeError, TypeError):
                        continue
                    
                    if isinstance(result, dict):
                        # Extract reference IDs from tool results
                        for key in ["notes", "appointments", "medical_histories", "examinations", "lab_results"]:
                            if key in result:
                                for record in result[key]:
                                    if isinstance(record, dict) and "reference_id" in record:
                                        ref_id = record["reference_id"]
                                        
                                        # Create reference record if it doesn't exist
                                        await self.reference_manager._ensure_internal_reference_exists(ref_id, result)
                                        reference_ids.append(ref_id)
            
            # Link all references to the message
            if reference_ids:
                await self.reference_manager.link_message_references(message_id, reference_ids)
        
        return message_id
    
    async def update_conversation_title(
        self, 
        conversation_id: str,
        doctor_id: str,
        title: str
    ) -> bool:
        """Update conversation title."""
        result = await self.db.execute(
            select(Conversation).where(
                Conversation.conversation_id == conversation_id,
                Conversation.doctor_id == doctor_id
            )
        )
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            return False
        
        conversation.title = title
        conversation.last_updated = datetime.utcnow()
        await self.db.flush()
        
        return True
    
    async def delete_conversation(
        self, 
        conversation_id: str,
        doctor_id: str
    ) -> bool:
        """Delete a conversation and all its messages."""
        result = await self.db.execute(
            select(Conversation).where(
                Conversation.conversation_id == conversation_id,
                Conversation.doctor_id == doctor_id
            )
        )
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            return False
        
        await self.db.delete(conversation)
        await self.db.flush()
        
        return True
    
    def generate_title_from_message(self, message: str) -> str:
        """Generate a conversation title from the first user message."""
        # Take first 50 characters and clean up
        title = message.strip()[:50]
        if len(message) > 50:
            title += "..."
        
        # Remove newlines and extra spaces
        title = " ".join(title.split())
        
        return title or "New Conversation"