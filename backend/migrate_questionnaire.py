"""
Migration script: Update existing event store questionnaire (46d4751b-28cb-45a9-b581-29219485b893)
with the latest question fixes:
  - Remove "Any specific pricing requirements or profit per item?" [37]
  - Add conditional to "Design style preferences" [33]
  - Remove "Do you want to review and approve..." [63] and "Do you want a private preview link..." [65]
  - Rename "Who should review and approve..." [64] to "Who should receive the pre-launch review packet?"
  - Add hint descriptions to Event Name [7] and Event Date [8]
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

QUESTIONNAIRE_ID = "46d4751b-28cb-45a9-b581-29219485b893"
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME   = os.environ.get("DB_NAME", "signguy_ai")


async def run():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    q = await db.questionnaires.find_one({"id": QUESTIONNAIRE_ID}, {"_id": 0})
    if not q:
        print(f"Questionnaire {QUESTIONNAIRE_ID} not found")
        return

    questions = q.get("questions", [])
    print(f"Loaded {len(questions)} questions")

    new_questions = []
    removed = []

    LABELS_TO_REMOVE = {
        "Any specific pricing requirements or profit per item?",
        "Do you want to review and approve products and mockups before launch?",
        "Do you want a private preview link to see the store before launch?",
    }

    for q_item in questions:
        label = q_item.get("label", "")

        # Remove these questions entirely
        if label in LABELS_TO_REMOVE:
            removed.append(label)
            continue

        # Add hint descriptions
        if label == "Event Name":
            q_item["description"] = "Leave blank if this doesn't apply to your group or event"
            print(f"  Updated: Event Name description")

        elif label == "Event Date":
            q_item["description"] = "Leave blank if there is no specific event date"
            print(f"  Updated: Event Date description")

        # Add conditional to Design style preferences
        elif label == "Design style preferences":
            q_item["conditional"] = {
                "depends_on_label": "Do you already have finished artwork?",
                "operator": "not_equals",
                "value": "yes"
            }
            print(f"  Updated: Design style preferences conditional")

        # Rename review question
        elif label in ("Who should review and approve the store before launch?",
                       "Who should review and approve the products and store before launch?"):
            q_item["label"] = "Who should receive the pre-launch review packet?"
            q_item["description"] = "Name and email if different from your contact info above."
            print(f"  Renamed: {label} → Who should receive the pre-launch review packet?")

        new_questions.append(q_item)

    print(f"\nRemoved {len(removed)} questions: {removed}")
    print(f"Kept {len(new_questions)} questions")

    result = await db.questionnaires.update_one(
        {"id": QUESTIONNAIRE_ID},
        {"$set": {"questions": new_questions}}
    )
    print(f"\nMongoDB update: matched={result.matched_count}, modified={result.modified_count}")
    client.close()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(run())
