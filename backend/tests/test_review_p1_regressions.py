import asyncio
import os
import runpy
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


class SMSServiceImportTests(unittest.TestCase):
    def test_sms_service_loads_and_disables_sms_without_twilio(self):
        module_path = BACKEND_DIR / "services" / "sms_service.py"
        env = {
            "TWILIO_ACCOUNT_SID": "AC123",
            "TWILIO_AUTH_TOKEN": "secret",
            "TWILIO_FROM_NUMBER": "+15551234567",
        }

        with patch.dict(os.environ, env), patch.dict(
            sys.modules,
            {
                "twilio": None,
                "twilio.rest": None,
                "twilio.base": None,
                "twilio.base.exceptions": None,
            },
        ):
            module_globals = runpy.run_path(str(module_path))

        service = module_globals["SMSService"]()

        self.assertIsNone(service._client)
        result = asyncio.run(service.send("+15551234567", "Test"))
        self.assertEqual(result, {"success": False, "error": "SMS not configured"})


class PublicQuoteSerializerTests(unittest.TestCase):
    def test_only_returns_customer_safe_fields(self):
        from services.public_quote import serialize_public_quote

        quote = {
            "id": "quote-1",
            "quote_number": "Q-1001",
            "status": "sent",
            "tenant_id": "tenant-1",
            "customer_id": "customer-1",
            "total": 1250.0,
            "notes": "Customer-visible note",
            "internal_notes": "Do not disclose",
            "production_cost": 600.0,
            "profit_amount": 650.0,
            "profit_margin_percent": 52.0,
            "created_at": "2026-06-01T00:00:00+00:00",
            "expiration_date": "2026-06-08",
            "line_items": [
                {
                    "description": "Banner",
                    "quantity": 2,
                    "unit_price": 625.0,
                    "total": 1250.0,
                    "pricing_category": "banners",
                    "pricing_data": {"markup": 2.0, "cost": 600.0},
                    "cost_snapshot": {"materials": 250.0, "labor": 350.0},
                }
            ],
        }

        public_quote = serialize_public_quote(quote)

        self.assertEqual(
            public_quote,
            {
                "id": "quote-1",
                "quote_number": "Q-1001",
                "status": "sent",
                "total": 1250.0,
                "notes": "Customer-visible note",
                "created_at": "2026-06-01T00:00:00+00:00",
                "expiration_date": "2026-06-08",
                "line_items": [
                    {
                        "description": "Banner",
                        "quantity": 2,
                        "unit_price": 625.0,
                        "total": 1250.0,
                    }
                ],
            },
        )

    def test_does_not_pass_through_future_fields(self):
        from services.public_quote import serialize_public_quote

        quote = {
            "id": "quote-1",
            "total": 50,
            "new_internal_margin_field": "secret",
            "line_items": [
                {
                    "description": "Decal",
                    "total": 50,
                    "future_cost_breakdown": {"vinyl": 10},
                }
            ],
        }

        public_quote = serialize_public_quote(quote)

        self.assertNotIn("new_internal_margin_field", public_quote)
        self.assertNotIn("future_cost_breakdown", public_quote["line_items"][0])


class MagicLinkResponseTests(unittest.TestCase):
    def test_public_endpoint_uses_customer_safe_quote(self):
        quote = {
            "id": "quote-1",
            "tenant_id": "tenant-1",
            "customer_id": "customer-1",
            "quote_number": "Q-1001",
            "total": 1250.0,
            "production_cost": 600.0,
            "line_items": [
                {
                    "description": "Banner",
                    "quantity": 2,
                    "unit_price": 625.0,
                    "total": 1250.0,
                    "pricing_data": {"markup": 2.0},
                    "cost_snapshot": {"labor": 350.0},
                }
            ],
        }
        link = {
            "token": "token",
            "resource_type": "quote",
            "resource_id": "quote-1",
            "tenant_id": "tenant-1",
            "expires_at": "2099-01-01T00:00:00+00:00",
        }
        customer = {"name": "Customer", "email": "customer@example.com"}
        tenant = {"name": "Shop", "email": "shop@example.com"}

        class FakeCollection:
            def __init__(self, value):
                self.value = value

            async def find_one(self, *_args, **_kwargs):
                return self.value

        fake_db = types.SimpleNamespace(
            magic_links=FakeCollection(link),
            quotes=FakeCollection(quote),
            order_quotes=FakeCollection(None),
            customers=FakeCollection(customer),
            tenants=FakeCollection(tenant),
        )
        fake_server = types.SimpleNamespace(
            db=fake_db,
            logger=types.SimpleNamespace(info=lambda *args, **kwargs: None),
            get_current_active_user=lambda: None,
        )
        fake_models = types.SimpleNamespace(UserInDB=object)

        class FakeHTTPException(Exception):
            def __init__(self, status_code, detail):
                super().__init__(detail)
                self.status_code = status_code
                self.detail = detail

        class FakeAPIRouter:
            def __init__(self, *_args, **_kwargs):
                pass

            def get(self, *_args, **_kwargs):
                return lambda func: func

            def post(self, *_args, **_kwargs):
                return lambda func: func

        fake_fastapi = types.SimpleNamespace(
            APIRouter=FakeAPIRouter,
            HTTPException=FakeHTTPException,
            Depends=lambda dependency=None, **_kwargs: dependency,
            Query=lambda default=None, **_kwargs: default,
        )
        fake_pydantic = types.SimpleNamespace(BaseModel=object)

        for module_name in ("routes.magic_links", "backend.routes.magic_links"):
            sys.modules.pop(module_name, None)

        with patch.dict(
            sys.modules,
            {
                "server": fake_server,
                "models": fake_models,
                "fastapi": fake_fastapi,
                "pydantic": fake_pydantic,
            },
        ):
            import routes.magic_links as magic_links
            from services.public_quote import serialize_public_quote

        response = asyncio.run(magic_links.view_via_magic_link("token"))

        self.assertEqual(response["resource"], serialize_public_quote(quote))
        self.assertNotIn("production_cost", response["resource"])
        self.assertNotIn("pricing_data", response["resource"]["line_items"][0])
        self.assertNotIn("cost_snapshot", response["resource"]["line_items"][0])


if __name__ == "__main__":
    unittest.main()
