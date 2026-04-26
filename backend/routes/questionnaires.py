"""
Questionnaire Routes - Dynamic Form Builder API

Allows sign shops to create, manage, and collect responses from
custom intake forms for different job types.
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Optional, List
from datetime import datetime, timezone
import uuid
import os

from motor.motor_asyncio import AsyncIOMotorClient
from models.questionnaires import (
    Questionnaire, QuestionnaireCreate, QuestionnaireUpdate,
    QuestionnaireResponse, QuestionnaireResponseCreate,
    QuestionnaireStatus, QuestionnaireCategory,
    Question, QuestionType, QUESTIONNAIRE_TEMPLATES
)
from models import UserInDB
from core.auth_deps import get_current_active_user

# Database connection
mongo_client = AsyncIOMotorClient(os.environ.get('MONGO_URL'))
db = mongo_client[os.environ.get('DB_NAME', 'signguy')]

router = APIRouter(prefix="/questionnaires", tags=["Questionnaires"])


# ============== QUESTIONNAIRE CRUD ==============

@router.get("")
async def list_questionnaires(
    status: Optional[str] = None,
    category: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """List all questionnaires for the tenant"""
    query = {"tenant_id": current_user.tenant_id}
    
    if status:
        query["status"] = status
    if category:
        query["category"] = category
    
    questionnaires = await db.questionnaires.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return questionnaires


@router.get("/templates")
async def get_templates(
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get pre-built questionnaire templates"""
    templates = []
    for key, template in QUESTIONNAIRE_TEMPLATES.items():
        templates.append({
            "id": key,
            "name": template["name"],
            "description": template["description"],
            "category": template["category"],
            "question_count": len(template["questions"])
        })
    return templates


@router.post("/from-template/{template_id}")
async def create_from_template(
    template_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Create a new questionnaire from a template"""
    if template_id not in QUESTIONNAIRE_TEMPLATES:
        raise HTTPException(status_code=404, detail="Template not found")
    
    template = QUESTIONNAIRE_TEMPLATES[template_id]
    
    # Create questions with IDs
    questions = []
    for i, q in enumerate(template["questions"]):
        question = Question(
            id=str(uuid.uuid4()),
            type=QuestionType(q["type"]),
            label=q["label"],
            description=q.get("description"),
            placeholder=q.get("placeholder"),
            required=q.get("required", False),
            options=[{"value": o["value"], "label": o["label"]} for o in q.get("options", [])],
            validation=q.get("validation"),
            order=q.get("order", i),
            accept_file_types=q.get("accept_file_types"),
            max_file_size_mb=q.get("max_file_size_mb", 10)
        )
        questions.append(question)
    
    now = datetime.now(timezone.utc).isoformat()
    questionnaire = Questionnaire(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        name=template["name"],
        description=template["description"],
        category=QuestionnaireCategory(template["category"]),
        questions=questions,
        status=QuestionnaireStatus.DRAFT,
        created_at=now,
        updated_at=now,
        created_by=current_user.id
    )
    
    await db.questionnaires.insert_one(questionnaire.model_dump())
    
    return questionnaire.model_dump()


@router.post("")
async def create_questionnaire(
    request: QuestionnaireCreate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Create a new questionnaire"""
    now = datetime.now(timezone.utc).isoformat()
    
    # Ensure all questions have IDs
    questions = []
    for i, q in enumerate(request.questions):
        if not q.id:
            q.id = str(uuid.uuid4())
        if q.order == 0:
            q.order = i
        questions.append(q)
    
    questionnaire = Questionnaire(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        name=request.name,
        description=request.description,
        category=request.category,
        questions=questions,
        is_default=request.is_default,
        thank_you_message=request.thank_you_message,
        status=QuestionnaireStatus.DRAFT,
        created_at=now,
        updated_at=now,
        created_by=current_user.id
    )
    
    await db.questionnaires.insert_one(questionnaire.model_dump())
    
    return questionnaire.model_dump()


@router.get("/{questionnaire_id}")
async def get_questionnaire(
    questionnaire_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get a specific questionnaire"""
    questionnaire = await db.questionnaires.find_one(
        {"id": questionnaire_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    
    if not questionnaire:
        raise HTTPException(status_code=404, detail="Questionnaire not found")
    
    return questionnaire


@router.put("/{questionnaire_id}")
async def update_questionnaire(
    questionnaire_id: str,
    request: QuestionnaireUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update a questionnaire"""
    questionnaire = await db.questionnaires.find_one(
        {"id": questionnaire_id, "tenant_id": current_user.tenant_id}
    )
    
    if not questionnaire:
        raise HTTPException(status_code=404, detail="Questionnaire not found")
    
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if request.name is not None:
        update_data["name"] = request.name
    if request.description is not None:
        update_data["description"] = request.description
    if request.category is not None:
        update_data["category"] = request.category.value
    if request.status is not None:
        update_data["status"] = request.status.value
    if request.is_default is not None:
        update_data["is_default"] = request.is_default
    if request.thank_you_message is not None:
        update_data["thank_you_message"] = request.thank_you_message
    if request.questions is not None:
        # Ensure all questions have IDs and proper order
        questions = []
        for i, q in enumerate(request.questions):
            q_dict = q.model_dump()
            if not q_dict.get("id"):
                q_dict["id"] = str(uuid.uuid4())
            if q_dict.get("order", 0) == 0:
                q_dict["order"] = i
            questions.append(q_dict)
        update_data["questions"] = questions
    
    await db.questionnaires.update_one(
        {"id": questionnaire_id},
        {"$set": update_data}
    )
    
    updated = await db.questionnaires.find_one(
        {"id": questionnaire_id},
        {"_id": 0}
    )
    
    return updated


@router.delete("/{questionnaire_id}")
async def delete_questionnaire(
    questionnaire_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Delete a questionnaire"""
    result = await db.questionnaires.delete_one(
        {"id": questionnaire_id, "tenant_id": current_user.tenant_id}
    )
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Questionnaire not found")
    
    return {"message": "Questionnaire deleted"}


@router.post("/{questionnaire_id}/duplicate")
async def duplicate_questionnaire(
    questionnaire_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Duplicate a questionnaire"""
    questionnaire = await db.questionnaires.find_one(
        {"id": questionnaire_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    
    if not questionnaire:
        raise HTTPException(status_code=404, detail="Questionnaire not found")
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Create new questionnaire with new IDs
    new_questionnaire = questionnaire.copy()
    new_questionnaire["id"] = str(uuid.uuid4())
    new_questionnaire["name"] = f"{questionnaire['name']} (Copy)"
    new_questionnaire["status"] = QuestionnaireStatus.DRAFT.value
    new_questionnaire["response_count"] = 0
    new_questionnaire["created_at"] = now
    new_questionnaire["updated_at"] = now
    new_questionnaire["created_by"] = current_user.id
    
    # Generate new IDs for questions
    for q in new_questionnaire.get("questions", []):
        q["id"] = str(uuid.uuid4())
    
    await db.questionnaires.insert_one(new_questionnaire)
    
    return new_questionnaire


# ============== PUBLIC QUESTIONNAIRE ACCESS ==============

@router.get("/public/{questionnaire_id}")
async def get_public_questionnaire(questionnaire_id: str):
    """Get a questionnaire for public submission (no auth required)"""
    questionnaire = await db.questionnaires.find_one(
        {"id": questionnaire_id, "status": QuestionnaireStatus.ACTIVE.value},
        {"_id": 0, "tenant_id": 0, "created_by": 0}
    )
    
    if not questionnaire:
        raise HTTPException(status_code=404, detail="Questionnaire not found or not active")
    
    return questionnaire


# ============== RESPONSE MANAGEMENT ==============

@router.post("/public/{questionnaire_id}/submit")
async def submit_questionnaire_response(
    questionnaire_id: str,
    request: QuestionnaireResponseCreate,
    req: Request
):
    """Submit a response to a questionnaire (public endpoint)"""
    questionnaire = await db.questionnaires.find_one(
        {"id": questionnaire_id, "status": QuestionnaireStatus.ACTIVE.value}
    )
    
    if not questionnaire:
        raise HTTPException(status_code=404, detail="Questionnaire not found or not active")
    
    # Validate required fields and per-field format
    import re as _re
    _EMAIL_RE = _re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
    _PHONE_RE = _re.compile(r'^[\d\s\+\-\(\)\.]{7,20}$')
    for question in questionnaire.get("questions", []):
        q_type = question.get("type", "")
        if question.get("required") and q_type not in ["heading", "paragraph"]:
            q_id = question.get("id")
            if q_id not in request.answers or not request.answers[q_id]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Required field missing: {question.get('label')}"
                )
        # Per-field format validation
        q_id = question.get("id")
        answer = request.answers.get(q_id) if request.answers else None
        if answer and q_type == "email":
            if not _EMAIL_RE.match(str(answer)):
                raise HTTPException(status_code=422, detail=f"Invalid email format for field: {question.get('label')}")
        if answer and q_type == "phone":
            if not _PHONE_RE.match(str(answer)):
                raise HTTPException(status_code=422, detail=f"Invalid phone format for field: {question.get('label')}")
    
    # Get client IP
    client_ip = req.client.host if req.client else None
    forwarded = req.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    
    now = datetime.now(timezone.utc).isoformat()
    
    response = QuestionnaireResponse(
        id=str(uuid.uuid4()),
        tenant_id=questionnaire["tenant_id"],
        questionnaire_id=questionnaire_id,
        questionnaire_name=questionnaire["name"],
        answers=request.answers,
        job_id=request.job_id,
        customer_id=request.customer_id,
        customer_name=request.customer_name,
        customer_email=request.customer_email,
        submitted_at=now,
        ip_address=client_ip
    )
    
    await db.questionnaire_responses.insert_one(response.model_dump())
    
    # Update response count
    await db.questionnaires.update_one(
        {"id": questionnaire_id},
        {"$inc": {"response_count": 1}}
    )
    
    return {
        "message": questionnaire.get("thank_you_message", "Thank you for your submission!"),
        "response_id": response.id
    }


@router.get("/{questionnaire_id}/responses")
async def get_questionnaire_responses(
    questionnaire_id: str,
    limit: int = 50,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get all responses for a questionnaire"""
    # Verify questionnaire belongs to tenant
    questionnaire = await db.questionnaires.find_one(
        {"id": questionnaire_id, "tenant_id": current_user.tenant_id}
    )
    
    if not questionnaire:
        raise HTTPException(status_code=404, detail="Questionnaire not found")
    
    responses = await db.questionnaire_responses.find(
        {"questionnaire_id": questionnaire_id},
        {"_id": 0}
    ).sort("submitted_at", -1).to_list(limit)
    
    return {
        "questionnaire_name": questionnaire["name"],
        "total_responses": questionnaire.get("response_count", len(responses)),
        "responses": responses
    }


@router.get("/responses/{response_id}")
async def get_single_response(
    response_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get a single response with full details"""
    response = await db.questionnaire_responses.find_one(
        {"id": response_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
    
    # Get the questionnaire for question labels
    questionnaire = await db.questionnaires.find_one(
        {"id": response["questionnaire_id"]},
        {"_id": 0, "questions": 1}
    )
    
    # Create a formatted response with question labels
    formatted_answers = []
    if questionnaire:
        question_map = {q["id"]: q for q in questionnaire.get("questions", [])}
        for q_id, answer in response.get("answers", {}).items():
            question = question_map.get(q_id, {})
            formatted_answers.append({
                "question_id": q_id,
                "question_label": question.get("label", "Unknown Question"),
                "question_type": question.get("type", "text"),
                "answer": answer
            })
    
    return {
        **response,
        "formatted_answers": formatted_answers
    }


@router.delete("/responses/{response_id}")
async def delete_response(
    response_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Delete a questionnaire response"""
    response = await db.questionnaire_responses.find_one(
        {"id": response_id, "tenant_id": current_user.tenant_id}
    )
    
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
    
    # Decrement response count
    await db.questionnaires.update_one(
        {"id": response["questionnaire_id"]},
        {"$inc": {"response_count": -1}}
    )
    
    await db.questionnaire_responses.delete_one({"id": response_id})
    
    return {"message": "Response deleted"}
