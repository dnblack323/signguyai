"""
Facebook AI Classification & Order Extraction Service

Uses Claude Sonnet (via emergentintegrations) to:
1. Classify incoming Facebook Messenger messages by type
2. Extract structured sign/wrap order details when relevant
3. Generate a suggested staff reply

The provider and model are read from environment variables so they can be
changed without touching this file.
"""

import os
import json
import uuid
import logging
from typing import Any, Dict, Optional

from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

# ── Model configuration (swappable via env) ───────────────────────────────────
AI_PROVIDER = os.environ.get("FB_AI_PROVIDER", "anthropic")
AI_MODEL = os.environ.get("FB_AI_MODEL", "claude-4-sonnet-20250514")
AI_API_KEY = os.environ.get("EMERGENT_LLM_KEY", "")

# ── Classification labels ─────────────────────────────────────────────────────
CLASSIFICATION_LABELS = [
    "new_quote_request",
    "new_order_request",
    "vehicle_wrap_request",
    "artwork_submission",
    "revision_request",
    "price_question",
    "pickup_or_delivery_question",
    "payment_question",
    "complaint_or_issue",
    "general_question",
    "spam_or_unrelated",
    "unknown",
]

# ── System prompts ────────────────────────────────────────────────────────────
CLASSIFICATION_SYSTEM = """You are an AI assistant for a professional sign shop and graphics company.
Your job is to analyze incoming Facebook Messenger messages from potential customers and classify them.

Respond ONLY with a valid JSON object. No prose, no markdown fences. Just the raw JSON.

JSON schema:
{
  "classification": "<one of the labels>",
  "confidence": <0.0-1.0>,
  "urgency": "<low|medium|high>",
  "should_create_draft": <true|false>,
  "suggested_action": "<short internal action note for staff>",
  "suggested_reply": "<short professional customer reply, no price quotes, no completion promises, do NOT mention AI>",
  "missing_info": ["<list of missing info needed to quote>"]
}

Classification labels:
new_quote_request, new_order_request, vehicle_wrap_request, artwork_submission,
revision_request, price_question, pickup_or_delivery_question, payment_question,
complaint_or_issue, general_question, spam_or_unrelated, unknown

Rules:
- should_create_draft is true only for: new_quote_request, new_order_request, vehicle_wrap_request
- suggested_reply must be brief (2-3 sentences max), professional, and never mention AI or automation
- urgency is high if the customer mentions a deadline within a week or uses urgent language
"""

EXTRACTION_SYSTEM = """You are an AI assistant for a professional sign shop and graphics company.
Extract structured order details from a customer's Facebook Messenger message.

Respond ONLY with a valid JSON object. No prose, no markdown fences. Just the raw JSON.

JSON schema:
{
  "customer_name": null,
  "product_type": null,
  "quantity": null,
  "size": null,
  "material": null,
  "double_sided": null,
  "colors_design_notes": null,
  "artwork_provided": false,
  "attachment_present": false,
  "requested_deadline": null,
  "budget_mentioned": null,
  "phone_number": null,
  "email_address": null,
  "address_location": null,
  "delivery_preference": null,
  "install_needed": null,
  "vehicle_year": null,
  "vehicle_make": null,
  "vehicle_model": null,
  "vehicle_type": null,
  "wrap_type": null,
  "fleet_quantity": null,
  "lead_type": null,
  "missing_information": ["<list items>"],
  "confidence_score": <0.0-1.0>,
  "suggested_next_step": "<short internal note>",
  "suggested_reply": "<short professional customer reply>"
}

Product categories: yard signs, banners, rigid signs, aluminum signs, ACM/composite signs,
coroplast signs, PVC signs, acrylic/lexan signs, decals/stickers, window graphics, storefront signs,
vehicle lettering, partial vehicle wrap, full vehicle wrap, box truck wrap, trailer wrap,
fleet graphics, race car graphics, apparel, business cards, promotional items, design service, other

Return null for unknown fields. Do not guess values that are not in the message.
"""


# ── Public API ────────────────────────────────────────────────────────────────
async def classify_message(message_text: str) -> Dict[str, Any]:
    """Classify a Facebook message and return structured result.

    Returns a dict matching the classification JSON schema above.
    On any failure, returns a safe default with classification='unknown'.
    """
    if not message_text or not message_text.strip():
        return _default_classification()

    try:
        session_id = f"fb_classify_{uuid.uuid4().hex[:12]}"
        chat = LlmChat(
            api_key=AI_API_KEY,
            session_id=session_id,
            system_message=CLASSIFICATION_SYSTEM,
        ).with_model(AI_PROVIDER, AI_MODEL)

        prompt = f"Classify this customer message:\n\n{message_text[:3000]}"
        response = await chat.send_message(UserMessage(text=prompt))
        return _parse_json_response(response, _default_classification())

    except Exception as exc:
        logger.warning(f"classify_message failed: {exc}")
        return _default_classification()


async def extract_order_details(message_text: str) -> Dict[str, Any]:
    """Extract structured sign/wrap order details from a message.

    Returns a dict matching the extraction JSON schema above.
    On failure, returns a safe default with empty fields.
    """
    if not message_text or not message_text.strip():
        return _default_extraction()

    try:
        session_id = f"fb_extract_{uuid.uuid4().hex[:12]}"
        chat = LlmChat(
            api_key=AI_API_KEY,
            session_id=session_id,
            system_message=EXTRACTION_SYSTEM,
        ).with_model(AI_PROVIDER, AI_MODEL)

        prompt = f"Extract order details from this customer message:\n\n{message_text[:3000]}"
        response = await chat.send_message(UserMessage(text=prompt))
        return _parse_json_response(response, _default_extraction())

    except Exception as exc:
        logger.warning(f"extract_order_details failed: {exc}")
        return _default_extraction()


# ── Internal helpers ──────────────────────────────────────────────────────────
def _parse_json_response(raw: Any, fallback: Dict) -> Dict[str, Any]:
    """Parse a raw LLM response string to dict, falling back on parse failure."""
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str):
        return fallback
    text = raw.strip()
    # Strip any accidental markdown fences
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        # Try to extract JSON from surrounding text
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except Exception:
                pass
    return fallback


def _default_classification() -> Dict[str, Any]:
    return {
        "classification": "unknown",
        "confidence": 0.0,
        "urgency": "low",
        "should_create_draft": False,
        "suggested_action": "Manual review needed",
        "suggested_reply": "",
        "missing_info": [],
    }


def _default_extraction() -> Dict[str, Any]:
    return {
        "customer_name": None,
        "product_type": None,
        "quantity": None,
        "size": None,
        "material": None,
        "double_sided": None,
        "colors_design_notes": None,
        "artwork_provided": False,
        "attachment_present": False,
        "requested_deadline": None,
        "budget_mentioned": None,
        "phone_number": None,
        "email_address": None,
        "address_location": None,
        "delivery_preference": None,
        "install_needed": None,
        "vehicle_year": None,
        "vehicle_make": None,
        "vehicle_model": None,
        "vehicle_type": None,
        "wrap_type": None,
        "fleet_quantity": None,
        "lead_type": None,
        "missing_information": [],
        "confidence_score": 0.0,
        "suggested_next_step": "",
        "suggested_reply": "",
    }
