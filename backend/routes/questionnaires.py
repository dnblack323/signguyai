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


# ============== SUBMISSION VALIDATION HELPERS ==============

# Question types that never collect an answer and are exempt from required checks.
_NON_INPUT_QUESTION_TYPES = {"heading", "paragraph"}


def iter_questionnaire_questions(questionnaire: dict):
    """Yield every question in a questionnaire.

    Walks both the top-level ``questions`` list and any nested
    ``sections[*].questions`` so section-based templates are validated
    with the same rigor as flat templates.
    """
    for q in questionnaire.get("questions", []) or []:
        if isinstance(q, dict):
            yield q
    for section in questionnaire.get("sections", []) or []:
        if not isinstance(section, dict):
            continue
        for q in section.get("questions", []) or []:
            if isinstance(q, dict):
                yield q


def _answer_is_empty(answer) -> bool:
    """True when an answer carries no usable value (None, blank, or empty list)."""
    if answer is None:
        return True
    if isinstance(answer, str):
        return answer.strip() == ""
    if isinstance(answer, (list, tuple, set, dict)):
        return len(answer) == 0
    return False


def _question_is_visible(question: dict, answers: dict) -> bool:
    """Evaluate a question's conditional rule against the submitted answers.

    Mirrors the storefront show/hide logic so the backend never enforces a
    required field that the respondent could not see. Questions without a
    conditional are always visible.
    """
    cond = question.get("conditional")
    if not cond or not isinstance(cond, dict):
        return True
    depends_on = cond.get("depends_on")
    if not depends_on:
        return True
    operator = (cond.get("operator") or "equals").lower()
    expected = cond.get("value")
    actual = (answers or {}).get(depends_on)

    def _as_float(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    if operator == "equals":
        return str(actual) == str(expected)
    if operator == "not_equals":
        return str(actual) != str(expected)
    if operator == "contains":
        if isinstance(actual, (list, tuple, set)):
            return expected in actual or str(expected) in [str(a) for a in actual]
        return str(expected) in str(actual or "")
    if operator in ("greater_than", "less_than"):
        a, e = _as_float(actual), _as_float(expected)
        if a is None or e is None:
            return False
        return a > e if operator == "greater_than" else a < e
    # Unknown operator → fail open (visible) so we never silently drop a field.
    return True


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
    
    # Validate required fields and per-field format.
    # Walks top-level questions AND nested sections[*].questions, respects
    # conditional visibility, and skips locked (provider-set) fields.
    import re as _re
    _EMAIL_RE = _re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
    _PHONE_RE = _re.compile(r'^[\d\s\+\-\(\)\.]{7,20}$')
    answers = request.answers or {}
    locked_ids = set(questionnaire.get("locked_answer_ids") or [])

    for question in iter_questionnaire_questions(questionnaire):
        q_type = question.get("type", "")
        q_id = question.get("id")

        if q_type in _NON_INPUT_QUESTION_TYPES:
            continue
        # Provider-locked fields are populated server-side via prefill — never
        # block the respondent on them.
        if q_id in locked_ids:
            continue
        # Hidden-by-condition questions are not required.
        if not _question_is_visible(question, answers):
            continue

        answer = answers.get(q_id)
        if question.get("required") and _answer_is_empty(answer):
            raise HTTPException(
                status_code=400,
                detail=f"Required field missing: {question.get('label')}"
            )

        # Per-field format validation (only when a value is present).
        if not _answer_is_empty(answer):
            if q_type == "email" and not _EMAIL_RE.match(str(answer)):
                raise HTTPException(status_code=422, detail=f"Invalid email format for field: {question.get('label')}")
            if q_type == "phone" and not _PHONE_RE.match(str(answer)):
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
        webstore_id=request.webstore_id,
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
        {"_id": 0, "questions": 1, "sections": 1}
    )
    
    # Create a formatted response with question labels
    formatted_answers = []
    if questionnaire:
        question_map = {q["id"]: q for q in iter_questionnaire_questions(questionnaire) if q.get("id")}
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


# ============== SEND VIA EMAIL ==============

from pydantic import BaseModel, EmailStr


class SendQuestionnaireEmail(BaseModel):
    email: EmailStr
    customer_name: Optional[str] = None
    public_url: Optional[str] = None  # frontend origin (e.g. https://signguy-ai.com)
    message: Optional[str] = None


@router.post("/{questionnaire_id}/send-email")
async def send_questionnaire_via_email(
    questionnaire_id: str,
    payload: SendQuestionnaireEmail,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Email a questionnaire link to a customer."""
    from services.email_service import email_service

    questionnaire = await db.questionnaires.find_one(
        {"id": questionnaire_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if not questionnaire:
        raise HTTPException(status_code=404, detail="Questionnaire not found")

    if questionnaire.get("status") != QuestionnaireStatus.ACTIVE.value:
        raise HTTPException(
            status_code=400,
            detail="Questionnaire must be Active before it can be sent. Publish it first."
        )

    # Build the public link. Prefer frontend-supplied origin, fall back to env, then a relative path.
    origin = (payload.public_url or os.environ.get("META_PUBLIC_URL", "") or "").rstrip("/")
    link = f"{origin}/questionnaire/{questionnaire_id}" if origin else f"/questionnaire/{questionnaire_id}"

    # Tenant branding (company name)
    tenant = await db.tenants.find_one({"id": current_user.tenant_id}, {"_id": 0})
    company_name = (tenant or {}).get("company_name") or (tenant or {}).get("name") or "SignGuy AI"

    # Customer greeting
    greeting_name = (payload.customer_name or "").strip() or "there"
    intro = payload.message or (
        "We need a few details to get started on your project. "
        "Please take a moment to complete the questionnaire below."
    )

    subject = f"Please complete: {questionnaire['name']}"
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; color: #0F172A;">
      <h2 style="color: #0F172A; margin-bottom: 8px;">{questionnaire['name']}</h2>
      <p style="color: #475569; margin-top: 0;">From {company_name}</p>
      <p>Hi {greeting_name},</p>
      <p>{intro}</p>
      <p style="margin: 28px 0;">
        <a href="{link}"
           style="background:#2F8BFB;color:#ffffff;padding:12px 24px;border-radius:8px;
                  text-decoration:none;display:inline-block;font-weight:600;">
          Open Questionnaire
        </a>
      </p>
      <p style="color:#475569;font-size:13px;">
        Or copy &amp; paste this link into your browser:<br/>
        <a href="{link}" style="color:#2F8BFB;">{link}</a>
      </p>
      <hr style="border:none;border-top:1px solid #E2E8F0;margin:24px 0;"/>
      <p style="color:#94A3B8;font-size:12px;">Sent by {company_name}</p>
    </div>
    """
    plain_content = (
        f"{questionnaire['name']}\n\n"
        f"Hi {greeting_name},\n\n"
        f"{intro}\n\n"
        f"Open the questionnaire here:\n{link}\n\n"
        f"— {company_name}"
    )

    result = await email_service.send_email(
        to_email=payload.email,
        subject=subject,
        html_content=html_content,
        plain_content=plain_content,
        tenant_id=current_user.tenant_id
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=502,
            detail=result.get("error") or "Failed to send email. Check that SendGrid is configured."
        )

    # Log activity on the questionnaire
    await db.questionnaires.update_one(
        {"id": questionnaire_id},
        {"$set": {"updated_at": datetime.now(timezone.utc).isoformat()}}
    )

    return {
        "success": True,
        "message": f"Questionnaire sent to {payload.email}",
        "link": link,
    }
