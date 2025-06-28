"""
Reference management for AI agent responses.
Handles creation and tracking of internal and external references.
"""

import hashlib
import uuid
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.db.schema import Reference, MessageReference, Message, ReferenceType

def generate_reference_hash(url: str, title: Optional[str] = None) -> str:
    """Generate a hash for external references."""
    # Use URL as primary input, with title as secondary
    content = url
    if title:
        content += f"|{title}"
    
    # Create SHA-256 hash and take first 12 characters for readability
    return hashlib.sha256(content.encode()).hexdigest()[:12]

def generate_internal_reference_id(reference_type: ReferenceType, internal_id: str) -> str:
    """Generate reference ID for internal database entities."""
    return f"{reference_type.value}_{internal_id}"

class ReferenceManager:
    """Manages creation and tracking of references for AI responses."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_external_reference(
        self, 
        url: str, 
        title: Optional[str] = None,
        reference_id: Optional[str] = None
    ) -> str:
        """Create or get existing external reference."""
        if not reference_id:
            reference_id = generate_reference_hash(url, title)
        
        # Check if reference already exists
        result = await self.db.execute(
            select(Reference).where(Reference.reference_id == reference_id)
        )
        existing_ref = result.scalar_one_or_none()
        
        if not existing_ref:
            # Create new reference
            new_ref = Reference(
                reference_id=reference_id,
                reference_type=ReferenceType.EXTERNAL,
                internal_id=None,
                external_url=url,
                title=title or self._extract_title_from_url(url)
            )
            self.db.add(new_ref)
            await self.db.flush()  # Ensure it's created
        
        return reference_id
    
    async def create_internal_reference(
        self, 
        reference_type: ReferenceType, 
        internal_id: str,
        title: Optional[str] = None
    ) -> str:
        """Create or get existing internal reference."""
        reference_id = generate_internal_reference_id(reference_type, internal_id)
        
        # Check if reference already exists
        result = await self.db.execute(
            select(Reference).where(Reference.reference_id == reference_id)
        )
        existing_ref = result.scalar_one_or_none()
        
        if not existing_ref:
            # Create new reference
            new_ref = Reference(
                reference_id=reference_id,
                reference_type=reference_type,
                internal_id=internal_id,
                external_url=None,
                title=title
            )
            self.db.add(new_ref)
            await self.db.flush()
        
        return reference_id
    
    async def link_message_references(
        self, 
        message_id: str, 
        reference_ids: List[str]
    ) -> None:
        """Link references to a message."""
        for ref_id in reference_ids:
            message_ref = MessageReference(
                message_id=message_id,
                reference_id=ref_id
            )
            self.db.add(message_ref)
    
    def _extract_title_from_url(self, url: str) -> str:
        """Extract a reasonable title from URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.replace('www.', '')
            return f"Source from {domain}"
        except:
            return "External Source"
    
    async def get_references_for_message(self, message_id: str) -> List[Dict[str, Any]]:
        """Get all references for a message."""
        result = await self.db.execute(
            select(Reference)
            .join(MessageReference)
            .where(MessageReference.message_id == message_id)
        )
        references = result.scalars().all()
        
        return [
            {
                "reference_id": ref.reference_id,
                "reference_type": ref.reference_type.value,
                "internal_id": ref.internal_id,
                "external_url": ref.external_url,
                "title": ref.title,
                "created_at": ref.created_at.isoformat()
            }
            for ref in references
        ]
    
    async def _ensure_internal_reference_exists(self, reference_id: str, tool_result: Dict[str, Any]):
        """Ensure internal reference exists in database."""
        # Check if reference already exists
        result = await self.db.execute(
            select(Reference).where(Reference.reference_id == reference_id)
        )
        existing_ref = result.scalar_one_or_none()
        
        if existing_ref:
            return  # Reference already exists
        
        # Parse reference ID to get type and internal ID
        if "_" in reference_id:
            ref_type_str, internal_id = reference_id.split("_", 1)
            
            # Map reference type string to ReferenceType enum
            type_mapping = {
                "notes": ReferenceType.NOTES,
                "appointments": ReferenceType.APPOINTMENTS,
                "medicalhistories": ReferenceType.MEDICALHISTORIES,
                "examinations": ReferenceType.EXAMINATIONS,
                "labresults": ReferenceType.LABRESULTS
            }
            
            reference_type = type_mapping.get(ref_type_str)
            if not reference_type:
                return  # Unknown reference type
            
            # Extract title from tool result
            title = self._extract_title_from_tool_result(reference_id, tool_result)
            
            # Create new internal reference
            new_ref = Reference(
                reference_id=reference_id,
                reference_type=reference_type,
                internal_id=internal_id,
                external_url=None,
                title=title
            )
            self.db.add(new_ref)
            await self.db.flush()
    
    def _extract_title_from_tool_result(self, reference_id: str, tool_result: Dict[str, Any]) -> str:
        """Extract a descriptive title from tool result for the given reference ID."""
        # Find the record that matches this reference_id
        data_keys = ["notes", "appointments", "medical_histories", "examinations", "lab_results"]
        
        for data_key in data_keys:
            if data_key in tool_result:
                for record in tool_result[data_key]:
                    if isinstance(record, dict) and record.get("reference_id") == reference_id:
                        # Extract title based on record type
                        if "title" in record:
                            return record["title"]
                        elif "test_name" in record:
                            return f"Lab Result: {record['test_name']}"
                        elif "appointment_detail" in record:
                            detail = record["appointment_detail"]
                            return detail[:100] + "..." if len(detail) > 100 else detail
                        else:
                            return f"Medical Record: {reference_id}"
        
        return f"Medical Record: {reference_id}"
    
    def _extract_citations_from_text(self, text: str) -> Dict[str, str]:
        """Extract citation numbers and their corresponding URLs from text."""
        import re
        
        citations = {}
        
        # Look for Sources section
        sources_match = re.search(r'\*\*Sources:\*\*\n(.*?)(?:\n\n|$)', text, re.DOTALL)
        if sources_match:
            sources_text = sources_match.group(1)
            
            # Extract [1] URL patterns
            for line in sources_text.split('\n'):
                match = re.match(r'\[(\d+)\]\s+(.+)', line.strip())
                if match:
                    citation_num = match.group(1)
                    url = match.group(2)
                    citations[citation_num] = url
        
        return citations