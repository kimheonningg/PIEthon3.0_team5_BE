from fastapi import APIRouter, Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List, Dict, Any, Optional
from loguru import logger

# Import your dependencies
from app.core.db import get_db, User
from app.core.auth import get_current_user

# Import your DTOs
from app.dto.agent import (
    ChatRequest,
    ChatResponse,
    ChatResponseData,
    ChatToolCall,
    SimpleChatRequest,
    SimpleChatResponse,
    SimpleChatToolCall,
    ConversationInfo
)

# Import the agent components
from app.core.agent.tools import create_tools_with_user_context
from app.core.agent.runner import run_graph_with_controller, AccumulatorController
from app.core.agent.messages import convert_to_langchain_messages
from app.core.agent.graph_builder import build_agent_graph
from assistant_stream import create_run, RunController
from assistant_stream.serialization import DataStreamResponse
from app.core.agent.prompt_builder import build_system_prompt
from app.service.postgres.conversation_service import ConversationService
from langchain_core.messages import SystemMessage, HumanMessage

router = APIRouter()

# Build agent graph once at module level for efficiency
agent_graph = build_agent_graph().compile()

# Build agent graph once at module level for efficiency
agent_graph = build_agent_graph().compile()

@router.post("/simple-chat", response_model=SimpleChatResponse)
async def simple_chat(
    request: SimpleChatRequest, 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Simple chat endpoint that takes just message.
    Uses current_user from authentication and patient_id from request if available.
    """
    try:
        # Create tools with user, db, and patient context
        tools = create_tools_with_user_context(db, current_user, request.patient_mrn)
        
        # Build system prompt using your existing prompt builder
        system_prompt = build_system_prompt("", tools)
        
        # Convert to LangChain format   
        langchain_messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=request.message)  # Fixed: was request_data.message
        ]
        
        # Create config for the agent
        config = {
            "tools": tools,
            "user_id": str(current_user.user_id),
            "patient_mrn": request.patient_mrn
        }
        
        # Set up controller
        controller = AccumulatorController()
        
        # Run the agent
        await run_graph_with_controller(
            graph=agent_graph, 
            messages=langchain_messages, 
            config=config, 
            controller=controller
        )
        
        # Get result from controller
        result = controller.get_final_result()
        
        # Create tool calls for response
        tool_calls = [
            SimpleChatToolCall(
                id=tc["id"],
                name=tc["name"],
                args=tc.get("args", ""),
                result=tc.get("result")
            )
            for tc in result.get("tool_calls", [])
        ]
        
        # Return response
        return SimpleChatResponse(
            message="Chat response generated successfully",
            conversation_id=None,  # Simple chat doesn't use conversations
            text=result.get("text", ""),
            tool_calls=tool_calls
        )
        
    except Exception as e:
        logger.error(f"Error in simple chat endpoint: {str(e)}")
        return SimpleChatResponse(
            success=False,
            message=f"Error generating response: {str(e)}",
            conversation_id=None
        )

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest, 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Chat with the AI agent using conversation system.
    """
    try:
        service = ConversationService(db)
        
        # Handle conversation logic
        conversation_id = request.conversation_id
        langchain_messages = []
        
        if conversation_id:
            # Load existing conversation messages
            messages = await service.get_conversation_messages(conversation_id, current_user.user_id)
            if not messages:
                raise HTTPException(status_code=404, detail="Conversation not found")
            
            # Convert to LangChain format
            for msg in messages:
                if msg.role == "user":
                    langchain_messages.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    langchain_messages.append(SystemMessage(content=msg.content))
        
        # Add current user query to messages
        langchain_messages.append(HumanMessage(content=request.query))
        
        # If no conversation_id, create new conversation from query
        if not conversation_id:
            title = service.generate_title_from_message(request.query)
            conversation_id = await service.create_conversation(
                doctor_id=current_user.user_id,
                patient_mrn=request.patient_mrn,
                title=title
            )
        
        # Save user query to conversation
        if conversation_id:
            await service.add_message_to_conversation(
                conversation_id=conversation_id,
                role="user",
                content=request.query
            )
        
        # Create tools and config
        tools = create_tools_with_user_context(db, current_user, request.patient_mrn)
        config = {
            "tools": tools,
            "user_id": str(current_user.user_id),
            "patient_mrn": request.patient_mrn
        }
        
        # Run agent
        controller = AccumulatorController()
        await run_graph_with_controller(
            graph=agent_graph, 
            messages=langchain_messages, 
            config=config, 
            controller=controller
        )
        
        # Get result
        result = controller.get_final_result()
        
        # Save assistant response
        if conversation_id:
            await service.add_message_to_conversation(
                conversation_id=conversation_id,
                role="assistant",
                content=result.get("text", ""),
                tool_calls=result.get("tool_calls", [])
            )
        
        await db.commit()
        
        # Return response
        return ChatResponse(
            message="Chat response generated successfully",
            conversation_id=conversation_id,
            response=ChatResponseData(
                text=result.get("text", ""),
                tool_calls=[
                    ChatToolCall(
                        id=tc["id"],
                        name=tc["name"],
                        args=tc.get("args", ""),
                        result=tc.get("result")
                    )
                    for tc in result.get("tool_calls", [])
                ]
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return ChatResponse(
            success=False,
            message=f"Error generating response: {str(e)}",
            conversation_id=None,
            response=None
        )

@router.post("/chat-stream")
async def chat_stream(
    request: ChatRequest, 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Chat with the AI agent with streaming response using conversation system.
    """
    try:
        service = ConversationService(db)
        
        # Handle conversation logic (similar to chat endpoint)
        conversation_id = request.conversation_id
        langchain_messages = []
        
        if conversation_id:
            messages = await service.get_conversation_messages(conversation_id, current_user.user_id)
            if not messages:
                raise HTTPException(status_code=404, detail="Conversation not found")
            
            for msg in messages:
                if msg.role == "user":
                    langchain_messages.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    langchain_messages.append(SystemMessage(content=msg.content))
        
        # Add current user query to messages
        langchain_messages.append(HumanMessage(content=request.query))
        
        # Create conversation if needed
        if not conversation_id:
            title = service.generate_title_from_message(request.query)
            conversation_id = await service.create_conversation(
                doctor_id=current_user.user_id,
                patient_mrn=request.patient_mrn,
                title=title
            )
        
        # Save user query to conversation
        if conversation_id:
            await service.add_message_to_conversation(
                conversation_id=conversation_id,
                role="user",
                content=request.query
            )
        
        # Create tools and config
        tools = create_tools_with_user_context(db, current_user, request.patient_mrn)
        config = {
            "tools": tools,
            "user_id": str(current_user.user_id),
            "patient_mrn": request.patient_mrn,
            "conversation_id": conversation_id,
            "conversation_service": service
        }
        
        # Use RunController with assistant_stream
        async def run(controller: RunController):
            await run_graph_with_controller(agent_graph, langchain_messages, config, controller)
            # TODO: Save final response to conversation
            
        return DataStreamResponse(create_run(run))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat-stream endpoint: {str(e)}")
        return JSONResponse(
            content={"error": f"Error generating response: {str(e)}"},
            status_code=500
        )

# =============================================================================
# CONVERSATION MANAGEMENT ENDPOINTS
# =============================================================================

@router.get("/conversations/{patient_mrn}", response_model=List[ConversationInfo])
async def get_patient_conversations(
    patient_mrn: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50
):
    """Get all conversations for a patient."""
    try:
        service = ConversationService(db)
        conversations = await service.get_conversations_for_patient(
            doctor_id=current_user.user_id,
            patient_mrn=patient_mrn,
            limit=limit
        )
        return conversations
        
    except Exception as e:
        logger.error(f"Error getting conversations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting conversations: {str(e)}")