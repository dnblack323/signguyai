"""
Plan Configuration Definitions

Pre-defined configurations for all 9 plans across 3 product lines.
"""

from models.product_tiers import (
    ProductLine, PlanType, PlanConfig, PlanPricing, ProcessingFees,
    PlanFeatures, CoreModuleFeatures, CustomerPortalFeatures, WebstoreFeatures,
    AIToolsFeatures, AIAssistantFeatures, CRMFeatures,
    FeatureValue, FeatureStatus, TierLevel, plan_to_legacy_tier,
    FOUNDER_SPOTS_TOTAL
)


# ============================================================================
# PRODUCT LINE 1: SIGNGUY AI OS (SHOP MANAGEMENT)
# ============================================================================

def get_os_starter() -> PlanConfig:
    """OS Starter: Basic shop management for solo operators"""
    return PlanConfig(
        plan_type=PlanType.OS_STARTER,
        product_line=ProductLine.OS,
        display_name="Starter",
        description="Perfect for getting started. Basic shop management for solo operators.",
        pricing=PlanPricing(
            monthly=39.0,
            annual=390.0,
            founder_monthly=29.0,
            founder_annual=290.0,
        ),
        processing_fees=ProcessingFees(
            invoice_fee_percent=0.0,
            webstore_fee_percent=0.0,
            stripe_connect_enabled=False,
            online_payments_enabled=False,
        ),
        founder_eligible=True,
        show_jobs_ui=True,
        show_payroll_ui=False,
        show_time_clock_ui=True,
        show_financials_ui=False,
        show_ai_assistant_ui=True,
        features=PlanFeatures(
            core=CoreModuleFeatures(
                customers=FeatureValue(status=FeatureStatus.ON),
                jobs=FeatureValue(status=FeatureStatus.ON),
                invoices=FeatureValue(status=FeatureStatus.ON),
                online_invoice_payments=FeatureValue(status=FeatureStatus.OFF),  # NO online payments
                dashboard=FeatureValue(status=FeatureStatus.ON),
                employees=FeatureValue(status=FeatureStatus.LIMITED, limit=2),
                time_clock=FeatureValue(status=FeatureStatus.ON),  # Basic mode
                time_clock_advanced=FeatureValue(status=FeatureStatus.OFF),
                tasks=FeatureValue(status=FeatureStatus.ON),
                productivity=FeatureValue(status=FeatureStatus.ON),
                productivity_advanced=FeatureValue(status=FeatureStatus.OFF),
                payroll=FeatureValue(status=FeatureStatus.OFF),
                financials=FeatureValue(status=FeatureStatus.OFF),
                financials_advanced=FeatureValue(status=FeatureStatus.OFF),
                company_settings=FeatureValue(status=FeatureStatus.ON),
                email_templates=FeatureValue(status=FeatureStatus.ON),
            ),
            customer_portal=CustomerPortalFeatures(
                portal_access=FeatureValue(status=FeatureStatus.OFF),
                messaging=FeatureValue(status=FeatureStatus.OFF),
                artwork_approvals=FeatureValue(status=FeatureStatus.OFF),
                documents=FeatureValue(status=FeatureStatus.OFF),
                document_storage_mb=FeatureValue(status=FeatureStatus.OFF, limit=0),
            ),
            webstores=WebstoreFeatures(
                webstore_access=FeatureValue(status=FeatureStatus.OFF),
                num_stores=FeatureValue(status=FeatureStatus.OFF, limit=0),
                store_type_b2b=FeatureValue(status=FeatureStatus.OFF),
                store_type_fundraiser=FeatureValue(status=FeatureStatus.OFF),
                store_type_creator=FeatureValue(status=FeatureStatus.OFF),
                stripe_connect=FeatureValue(status=FeatureStatus.OFF),
                order_to_job_automation=FeatureValue(status=FeatureStatus.OFF),
                commission_tracking=FeatureValue(status=FeatureStatus.OFF),
                payout_tracking=FeatureValue(status=FeatureStatus.OFF),
                advanced_branding=FeatureValue(status=FeatureStatus.OFF),
                price_overrides=FeatureValue(status=FeatureStatus.OFF),
                bulk_order_tools=FeatureValue(status=FeatureStatus.OFF),
                store_analytics=FeatureValue(status=FeatureStatus.OFF),
                store_analytics_advanced=FeatureValue(status=FeatureStatus.OFF),
                fundraiser_goals=FeatureValue(status=FeatureStatus.OFF),
            ),
            ai_tools=AIToolsFeatures(
                ai_access=FeatureValue(status=FeatureStatus.ON),
                text_generation=FeatureValue(status=FeatureStatus.ON),
                image_generation=FeatureValue(status=FeatureStatus.OFF),  # NO image gen
                monthly_generations=FeatureValue(status=FeatureStatus.LIMITED, limit=25),
                branding_kit_generator=FeatureValue(status=FeatureStatus.OFF),
                campaign_builder=FeatureValue(status=FeatureStatus.OFF),
                pricing_intelligence=FeatureValue(status=FeatureStatus.OFF),
                content_calendar=FeatureValue(status=FeatureStatus.OFF),
            ),
            ai_assistant=AIAssistantFeatures(
                assistant_access=FeatureValue(status=FeatureStatus.ON),
                monthly_queries=FeatureValue(status=FeatureStatus.LIMITED, limit=10),
                business_data_aware=FeatureValue(status=FeatureStatus.OFF),  # NOT data-aware
                business_data_limited=FeatureValue(status=FeatureStatus.OFF),
            ),
            crm=CRMFeatures(
                customer_specific_pricing=FeatureValue(status=FeatureStatus.OFF),
                advanced_tagging=FeatureValue(status=FeatureStatus.OFF),
                portal_document_sharing=FeatureValue(status=FeatureStatus.OFF),
            ),
        ),
    )


def get_os_pro() -> PlanConfig:
    """OS Pro: Full-featured for growing sign shops"""
    return PlanConfig(
        plan_type=PlanType.OS_PRO,
        product_line=ProductLine.OS,
        display_name="Pro",
        description="Full-featured plan for growing sign shops with team and webstores.",
        pricing=PlanPricing(
            monthly=79.0,
            annual=790.0,
            founder_monthly=59.0,
            founder_annual=590.0,
        ),
        processing_fees=ProcessingFees(
            invoice_fee_percent=1.0,
            webstore_fee_percent=3.0,
            stripe_connect_enabled=True,
            online_payments_enabled=True,
        ),
        founder_eligible=True,
        show_jobs_ui=True,
        show_payroll_ui=True,
        show_time_clock_ui=True,
        show_financials_ui=True,
        show_ai_assistant_ui=True,
        features=PlanFeatures(
            core=CoreModuleFeatures(
                customers=FeatureValue(status=FeatureStatus.ON),
                jobs=FeatureValue(status=FeatureStatus.ON),
                invoices=FeatureValue(status=FeatureStatus.ON),
                online_invoice_payments=FeatureValue(status=FeatureStatus.ON),
                dashboard=FeatureValue(status=FeatureStatus.ON),
                employees=FeatureValue(status=FeatureStatus.LIMITED, limit=10),
                time_clock=FeatureValue(status=FeatureStatus.ON),
                time_clock_advanced=FeatureValue(status=FeatureStatus.ON),
                tasks=FeatureValue(status=FeatureStatus.ON),
                productivity=FeatureValue(status=FeatureStatus.ON),
                productivity_advanced=FeatureValue(status=FeatureStatus.ON),
                payroll=FeatureValue(status=FeatureStatus.ON),
                financials=FeatureValue(status=FeatureStatus.ON),
                financials_advanced=FeatureValue(status=FeatureStatus.OFF),
                company_settings=FeatureValue(status=FeatureStatus.ON),
                email_templates=FeatureValue(status=FeatureStatus.ON),
            ),
            customer_portal=CustomerPortalFeatures(
                portal_access=FeatureValue(status=FeatureStatus.ON),
                messaging=FeatureValue(status=FeatureStatus.ON),
                artwork_approvals=FeatureValue(status=FeatureStatus.ON),
                documents=FeatureValue(status=FeatureStatus.ON),
                document_storage_mb=FeatureValue(status=FeatureStatus.LIMITED, limit=500),
            ),
            webstores=WebstoreFeatures(
                webstore_access=FeatureValue(status=FeatureStatus.ON),
                num_stores=FeatureValue(status=FeatureStatus.LIMITED, limit=3),
                store_type_b2b=FeatureValue(status=FeatureStatus.ON),
                store_type_fundraiser=FeatureValue(status=FeatureStatus.ON),
                store_type_creator=FeatureValue(status=FeatureStatus.OFF),  # Business only
                stripe_connect=FeatureValue(status=FeatureStatus.ON),
                order_to_job_automation=FeatureValue(status=FeatureStatus.ON),
                commission_tracking=FeatureValue(status=FeatureStatus.OFF),
                payout_tracking=FeatureValue(status=FeatureStatus.OFF),
                advanced_branding=FeatureValue(status=FeatureStatus.OFF),
                price_overrides=FeatureValue(status=FeatureStatus.OFF),
                bulk_order_tools=FeatureValue(status=FeatureStatus.OFF),
                store_analytics=FeatureValue(status=FeatureStatus.ON),
                store_analytics_advanced=FeatureValue(status=FeatureStatus.OFF),
                fundraiser_goals=FeatureValue(status=FeatureStatus.ON),
            ),
            ai_tools=AIToolsFeatures(
                ai_access=FeatureValue(status=FeatureStatus.ON),
                text_generation=FeatureValue(status=FeatureStatus.ON),
                image_generation=FeatureValue(status=FeatureStatus.ON),
                monthly_generations=FeatureValue(status=FeatureStatus.LIMITED, limit=100),
                branding_kit_generator=FeatureValue(status=FeatureStatus.OFF),
                campaign_builder=FeatureValue(status=FeatureStatus.OFF),
                pricing_intelligence=FeatureValue(status=FeatureStatus.OFF),
                content_calendar=FeatureValue(status=FeatureStatus.OFF),
            ),
            ai_assistant=AIAssistantFeatures(
                assistant_access=FeatureValue(status=FeatureStatus.ON),
                monthly_queries=FeatureValue(status=FeatureStatus.LIMITED, limit=50),
                business_data_aware=FeatureValue(status=FeatureStatus.OFF),
                business_data_limited=FeatureValue(status=FeatureStatus.ON),  # Limited data access
            ),
            crm=CRMFeatures(
                customer_specific_pricing=FeatureValue(status=FeatureStatus.OFF),
                advanced_tagging=FeatureValue(status=FeatureStatus.OFF),
                portal_document_sharing=FeatureValue(status=FeatureStatus.OFF),
            ),
        ),
    )


def get_os_business() -> PlanConfig:
    """OS Business: Everything unlimited for established shops"""
    return PlanConfig(
        plan_type=PlanType.OS_BUSINESS,
        product_line=ProductLine.OS,
        display_name="Business",
        description="Unlimited everything for established sign shops and agencies.",
        pricing=PlanPricing(
            monthly=149.0,
            annual=1490.0,
            founder_monthly=99.0,
            founder_annual=990.0,
        ),
        processing_fees=ProcessingFees(
            invoice_fee_percent=1.0,
            webstore_fee_percent=2.0,
            stripe_connect_enabled=True,
            online_payments_enabled=True,
        ),
        founder_eligible=True,
        show_jobs_ui=True,
        show_payroll_ui=True,
        show_time_clock_ui=True,
        show_financials_ui=True,
        show_ai_assistant_ui=True,
        features=PlanFeatures(
            core=CoreModuleFeatures(
                customers=FeatureValue(status=FeatureStatus.ON),
                jobs=FeatureValue(status=FeatureStatus.ON),
                invoices=FeatureValue(status=FeatureStatus.ON),
                online_invoice_payments=FeatureValue(status=FeatureStatus.ON),
                dashboard=FeatureValue(status=FeatureStatus.ON),
                employees=FeatureValue(status=FeatureStatus.ON),  # Unlimited
                time_clock=FeatureValue(status=FeatureStatus.ON),
                time_clock_advanced=FeatureValue(status=FeatureStatus.ON),
                tasks=FeatureValue(status=FeatureStatus.ON),
                productivity=FeatureValue(status=FeatureStatus.ON),
                productivity_advanced=FeatureValue(status=FeatureStatus.ON),
                payroll=FeatureValue(status=FeatureStatus.ON),
                financials=FeatureValue(status=FeatureStatus.ON),
                financials_advanced=FeatureValue(status=FeatureStatus.ON),
                company_settings=FeatureValue(status=FeatureStatus.ON),
                email_templates=FeatureValue(status=FeatureStatus.ON),
            ),
            customer_portal=CustomerPortalFeatures(
                portal_access=FeatureValue(status=FeatureStatus.ON),
                messaging=FeatureValue(status=FeatureStatus.ON),
                artwork_approvals=FeatureValue(status=FeatureStatus.ON),
                documents=FeatureValue(status=FeatureStatus.ON),
                document_storage_mb=FeatureValue(status=FeatureStatus.LIMITED, limit=2048),  # 2GB
            ),
            webstores=WebstoreFeatures(
                webstore_access=FeatureValue(status=FeatureStatus.ON),
                num_stores=FeatureValue(status=FeatureStatus.ON),  # Unlimited
                store_type_b2b=FeatureValue(status=FeatureStatus.ON),
                store_type_fundraiser=FeatureValue(status=FeatureStatus.ON),
                store_type_creator=FeatureValue(status=FeatureStatus.ON),
                stripe_connect=FeatureValue(status=FeatureStatus.ON),
                order_to_job_automation=FeatureValue(status=FeatureStatus.ON),
                commission_tracking=FeatureValue(status=FeatureStatus.ON),
                payout_tracking=FeatureValue(status=FeatureStatus.ON),
                advanced_branding=FeatureValue(status=FeatureStatus.ON),
                price_overrides=FeatureValue(status=FeatureStatus.ON),
                bulk_order_tools=FeatureValue(status=FeatureStatus.ON),
                store_analytics=FeatureValue(status=FeatureStatus.ON),
                store_analytics_advanced=FeatureValue(status=FeatureStatus.ON),
                fundraiser_goals=FeatureValue(status=FeatureStatus.ON),
            ),
            ai_tools=AIToolsFeatures(
                ai_access=FeatureValue(status=FeatureStatus.ON),
                text_generation=FeatureValue(status=FeatureStatus.ON),
                image_generation=FeatureValue(status=FeatureStatus.ON),
                monthly_generations=FeatureValue(status=FeatureStatus.ON),  # Unlimited
                branding_kit_generator=FeatureValue(status=FeatureStatus.ON),
                campaign_builder=FeatureValue(status=FeatureStatus.ON),
                pricing_intelligence=FeatureValue(status=FeatureStatus.ON),
                content_calendar=FeatureValue(status=FeatureStatus.ON),
            ),
            ai_assistant=AIAssistantFeatures(
                assistant_access=FeatureValue(status=FeatureStatus.ON),
                monthly_queries=FeatureValue(status=FeatureStatus.ON),  # Unlimited
                business_data_aware=FeatureValue(status=FeatureStatus.ON),  # Full data access
                business_data_limited=FeatureValue(status=FeatureStatus.ON),
            ),
            crm=CRMFeatures(
                customer_specific_pricing=FeatureValue(status=FeatureStatus.ON),
                advanced_tagging=FeatureValue(status=FeatureStatus.ON),
                portal_document_sharing=FeatureValue(status=FeatureStatus.ON),
            ),
        ),
    )


# ============================================================================
# PRODUCT LINE 2: SIGNGUY WEBSTORES (COMMERCE-ONLY)
# ============================================================================

def get_ws_launch() -> PlanConfig:
    """Webstore Launch: Entry-level ecommerce"""
    return PlanConfig(
        plan_type=PlanType.WS_LAUNCH,
        product_line=ProductLine.WEBSTORES,
        display_name="Launch",
        description="Get started selling online with one webstore.",
        pricing=PlanPricing(
            monthly=39.0,
            annual=390.0,
            founder_monthly=None,  # No founder pricing
            founder_annual=None,
        ),
        processing_fees=ProcessingFees(
            invoice_fee_percent=0.0,
            webstore_fee_percent=3.0,
            stripe_connect_enabled=True,
            online_payments_enabled=False,  # No invoices
        ),
        founder_eligible=False,
        # Hide shop management UI
        show_jobs_ui=False,
        show_payroll_ui=False,
        show_time_clock_ui=False,
        show_financials_ui=False,
        show_ai_assistant_ui=False,
        features=PlanFeatures(
            core=CoreModuleFeatures(
                # Minimal core - backend exists but UI hidden
                customers=FeatureValue(status=FeatureStatus.ON),  # For order customers
                jobs=FeatureValue(status=FeatureStatus.OFF),
                invoices=FeatureValue(status=FeatureStatus.OFF),
                online_invoice_payments=FeatureValue(status=FeatureStatus.OFF),
                dashboard=FeatureValue(status=FeatureStatus.ON),  # Webstore dashboard
                employees=FeatureValue(status=FeatureStatus.OFF, limit=0),
                time_clock=FeatureValue(status=FeatureStatus.OFF),
                time_clock_advanced=FeatureValue(status=FeatureStatus.OFF),
                tasks=FeatureValue(status=FeatureStatus.OFF),
                productivity=FeatureValue(status=FeatureStatus.OFF),
                productivity_advanced=FeatureValue(status=FeatureStatus.OFF),
                payroll=FeatureValue(status=FeatureStatus.OFF),
                financials=FeatureValue(status=FeatureStatus.OFF),
                financials_advanced=FeatureValue(status=FeatureStatus.OFF),
                company_settings=FeatureValue(status=FeatureStatus.ON),
                email_templates=FeatureValue(status=FeatureStatus.ON),
            ),
            customer_portal=CustomerPortalFeatures(
                portal_access=FeatureValue(status=FeatureStatus.OFF),
                messaging=FeatureValue(status=FeatureStatus.OFF),
                artwork_approvals=FeatureValue(status=FeatureStatus.OFF),
                documents=FeatureValue(status=FeatureStatus.OFF),
                document_storage_mb=FeatureValue(status=FeatureStatus.OFF, limit=0),
            ),
            webstores=WebstoreFeatures(
                webstore_access=FeatureValue(status=FeatureStatus.ON),
                num_stores=FeatureValue(status=FeatureStatus.LIMITED, limit=1),
                store_type_b2b=FeatureValue(status=FeatureStatus.ON),
                store_type_fundraiser=FeatureValue(status=FeatureStatus.ON),
                store_type_creator=FeatureValue(status=FeatureStatus.OFF),
                stripe_connect=FeatureValue(status=FeatureStatus.ON),
                order_to_job_automation=FeatureValue(status=FeatureStatus.OFF),  # No jobs
                commission_tracking=FeatureValue(status=FeatureStatus.ON),
                payout_tracking=FeatureValue(status=FeatureStatus.OFF),
                advanced_branding=FeatureValue(status=FeatureStatus.OFF),
                price_overrides=FeatureValue(status=FeatureStatus.OFF),
                bulk_order_tools=FeatureValue(status=FeatureStatus.OFF),
                store_analytics=FeatureValue(status=FeatureStatus.ON),
                store_analytics_advanced=FeatureValue(status=FeatureStatus.OFF),
                fundraiser_goals=FeatureValue(status=FeatureStatus.ON),
            ),
            ai_tools=AIToolsFeatures(
                ai_access=FeatureValue(status=FeatureStatus.OFF),
                text_generation=FeatureValue(status=FeatureStatus.OFF),
                image_generation=FeatureValue(status=FeatureStatus.OFF),
                monthly_generations=FeatureValue(status=FeatureStatus.OFF, limit=0),
                branding_kit_generator=FeatureValue(status=FeatureStatus.OFF),
                campaign_builder=FeatureValue(status=FeatureStatus.OFF),
                pricing_intelligence=FeatureValue(status=FeatureStatus.OFF),
                content_calendar=FeatureValue(status=FeatureStatus.OFF),
            ),
            ai_assistant=AIAssistantFeatures(
                assistant_access=FeatureValue(status=FeatureStatus.OFF),
                monthly_queries=FeatureValue(status=FeatureStatus.OFF, limit=0),
                business_data_aware=FeatureValue(status=FeatureStatus.OFF),
                business_data_limited=FeatureValue(status=FeatureStatus.OFF),
            ),
            crm=CRMFeatures(
                customer_specific_pricing=FeatureValue(status=FeatureStatus.OFF),
                advanced_tagging=FeatureValue(status=FeatureStatus.OFF),
                portal_document_sharing=FeatureValue(status=FeatureStatus.OFF),
            ),
        ),
    )


def get_ws_growth() -> PlanConfig:
    """Webstore Growth: Multiple stores with more features"""
    return PlanConfig(
        plan_type=PlanType.WS_GROWTH,
        product_line=ProductLine.WEBSTORES,
        display_name="Growth",
        description="Scale with up to 5 stores and advanced features.",
        pricing=PlanPricing(
            monthly=59.0,
            annual=590.0,
            founder_monthly=None,
            founder_annual=None,
        ),
        processing_fees=ProcessingFees(
            invoice_fee_percent=0.0,
            webstore_fee_percent=2.5,
            stripe_connect_enabled=True,
            online_payments_enabled=False,
        ),
        founder_eligible=False,
        show_jobs_ui=False,
        show_payroll_ui=False,
        show_time_clock_ui=False,
        show_financials_ui=False,
        show_ai_assistant_ui=False,
        features=PlanFeatures(
            core=CoreModuleFeatures(
                customers=FeatureValue(status=FeatureStatus.ON),
                jobs=FeatureValue(status=FeatureStatus.OFF),
                invoices=FeatureValue(status=FeatureStatus.OFF),
                online_invoice_payments=FeatureValue(status=FeatureStatus.OFF),
                dashboard=FeatureValue(status=FeatureStatus.ON),
                employees=FeatureValue(status=FeatureStatus.OFF, limit=0),
                time_clock=FeatureValue(status=FeatureStatus.OFF),
                time_clock_advanced=FeatureValue(status=FeatureStatus.OFF),
                tasks=FeatureValue(status=FeatureStatus.OFF),
                productivity=FeatureValue(status=FeatureStatus.OFF),
                productivity_advanced=FeatureValue(status=FeatureStatus.OFF),
                payroll=FeatureValue(status=FeatureStatus.OFF),
                financials=FeatureValue(status=FeatureStatus.OFF),
                financials_advanced=FeatureValue(status=FeatureStatus.OFF),
                company_settings=FeatureValue(status=FeatureStatus.ON),
                email_templates=FeatureValue(status=FeatureStatus.ON),
            ),
            customer_portal=CustomerPortalFeatures(
                portal_access=FeatureValue(status=FeatureStatus.OFF),
                messaging=FeatureValue(status=FeatureStatus.OFF),
                artwork_approvals=FeatureValue(status=FeatureStatus.OFF),
                documents=FeatureValue(status=FeatureStatus.OFF),
                document_storage_mb=FeatureValue(status=FeatureStatus.OFF, limit=0),
            ),
            webstores=WebstoreFeatures(
                webstore_access=FeatureValue(status=FeatureStatus.ON),
                num_stores=FeatureValue(status=FeatureStatus.LIMITED, limit=5),
                store_type_b2b=FeatureValue(status=FeatureStatus.ON),
                store_type_fundraiser=FeatureValue(status=FeatureStatus.ON),
                store_type_creator=FeatureValue(status=FeatureStatus.ON),  # All types
                stripe_connect=FeatureValue(status=FeatureStatus.ON),
                order_to_job_automation=FeatureValue(status=FeatureStatus.OFF),
                commission_tracking=FeatureValue(status=FeatureStatus.ON),
                payout_tracking=FeatureValue(status=FeatureStatus.OFF),
                advanced_branding=FeatureValue(status=FeatureStatus.ON),
                price_overrides=FeatureValue(status=FeatureStatus.ON),
                bulk_order_tools=FeatureValue(status=FeatureStatus.OFF),
                store_analytics=FeatureValue(status=FeatureStatus.ON),
                store_analytics_advanced=FeatureValue(status=FeatureStatus.OFF),
                fundraiser_goals=FeatureValue(status=FeatureStatus.ON),
            ),
            ai_tools=AIToolsFeatures(
                ai_access=FeatureValue(status=FeatureStatus.OFF),
                text_generation=FeatureValue(status=FeatureStatus.OFF),
                image_generation=FeatureValue(status=FeatureStatus.OFF),
                monthly_generations=FeatureValue(status=FeatureStatus.OFF, limit=0),
                branding_kit_generator=FeatureValue(status=FeatureStatus.OFF),
                campaign_builder=FeatureValue(status=FeatureStatus.OFF),
                pricing_intelligence=FeatureValue(status=FeatureStatus.OFF),
                content_calendar=FeatureValue(status=FeatureStatus.OFF),
            ),
            ai_assistant=AIAssistantFeatures(
                assistant_access=FeatureValue(status=FeatureStatus.OFF),
                monthly_queries=FeatureValue(status=FeatureStatus.OFF, limit=0),
                business_data_aware=FeatureValue(status=FeatureStatus.OFF),
                business_data_limited=FeatureValue(status=FeatureStatus.OFF),
            ),
            crm=CRMFeatures(
                customer_specific_pricing=FeatureValue(status=FeatureStatus.OFF),
                advanced_tagging=FeatureValue(status=FeatureStatus.OFF),
                portal_document_sharing=FeatureValue(status=FeatureStatus.OFF),
            ),
        ),
    )


def get_ws_scale() -> PlanConfig:
    """Webstore Scale: Unlimited stores with full features"""
    return PlanConfig(
        plan_type=PlanType.WS_SCALE,
        product_line=ProductLine.WEBSTORES,
        display_name="Scale",
        description="Unlimited stores with advanced analytics and bulk tools.",
        pricing=PlanPricing(
            monthly=99.0,
            annual=990.0,
            founder_monthly=None,
            founder_annual=None,
        ),
        processing_fees=ProcessingFees(
            invoice_fee_percent=0.0,
            webstore_fee_percent=2.0,
            stripe_connect_enabled=True,
            online_payments_enabled=False,
        ),
        founder_eligible=False,
        show_jobs_ui=False,
        show_payroll_ui=False,
        show_time_clock_ui=False,
        show_financials_ui=False,
        show_ai_assistant_ui=False,
        features=PlanFeatures(
            core=CoreModuleFeatures(
                customers=FeatureValue(status=FeatureStatus.ON),
                jobs=FeatureValue(status=FeatureStatus.OFF),
                invoices=FeatureValue(status=FeatureStatus.OFF),
                online_invoice_payments=FeatureValue(status=FeatureStatus.OFF),
                dashboard=FeatureValue(status=FeatureStatus.ON),
                employees=FeatureValue(status=FeatureStatus.OFF, limit=0),
                time_clock=FeatureValue(status=FeatureStatus.OFF),
                time_clock_advanced=FeatureValue(status=FeatureStatus.OFF),
                tasks=FeatureValue(status=FeatureStatus.OFF),
                productivity=FeatureValue(status=FeatureStatus.OFF),
                productivity_advanced=FeatureValue(status=FeatureStatus.OFF),
                payroll=FeatureValue(status=FeatureStatus.OFF),
                financials=FeatureValue(status=FeatureStatus.OFF),
                financials_advanced=FeatureValue(status=FeatureStatus.OFF),
                company_settings=FeatureValue(status=FeatureStatus.ON),
                email_templates=FeatureValue(status=FeatureStatus.ON),
            ),
            customer_portal=CustomerPortalFeatures(
                portal_access=FeatureValue(status=FeatureStatus.OFF),
                messaging=FeatureValue(status=FeatureStatus.OFF),
                artwork_approvals=FeatureValue(status=FeatureStatus.OFF),
                documents=FeatureValue(status=FeatureStatus.OFF),
                document_storage_mb=FeatureValue(status=FeatureStatus.OFF, limit=0),
            ),
            webstores=WebstoreFeatures(
                webstore_access=FeatureValue(status=FeatureStatus.ON),
                num_stores=FeatureValue(status=FeatureStatus.ON),  # Unlimited
                store_type_b2b=FeatureValue(status=FeatureStatus.ON),
                store_type_fundraiser=FeatureValue(status=FeatureStatus.ON),
                store_type_creator=FeatureValue(status=FeatureStatus.ON),
                stripe_connect=FeatureValue(status=FeatureStatus.ON),
                order_to_job_automation=FeatureValue(status=FeatureStatus.OFF),
                commission_tracking=FeatureValue(status=FeatureStatus.ON),
                payout_tracking=FeatureValue(status=FeatureStatus.ON),
                advanced_branding=FeatureValue(status=FeatureStatus.ON),
                price_overrides=FeatureValue(status=FeatureStatus.ON),
                bulk_order_tools=FeatureValue(status=FeatureStatus.ON),
                store_analytics=FeatureValue(status=FeatureStatus.ON),
                store_analytics_advanced=FeatureValue(status=FeatureStatus.ON),
                fundraiser_goals=FeatureValue(status=FeatureStatus.ON),
            ),
            ai_tools=AIToolsFeatures(
                ai_access=FeatureValue(status=FeatureStatus.OFF),
                text_generation=FeatureValue(status=FeatureStatus.OFF),
                image_generation=FeatureValue(status=FeatureStatus.OFF),
                monthly_generations=FeatureValue(status=FeatureStatus.OFF, limit=0),
                branding_kit_generator=FeatureValue(status=FeatureStatus.OFF),
                campaign_builder=FeatureValue(status=FeatureStatus.OFF),
                pricing_intelligence=FeatureValue(status=FeatureStatus.OFF),
                content_calendar=FeatureValue(status=FeatureStatus.OFF),
            ),
            ai_assistant=AIAssistantFeatures(
                assistant_access=FeatureValue(status=FeatureStatus.OFF),
                monthly_queries=FeatureValue(status=FeatureStatus.OFF, limit=0),
                business_data_aware=FeatureValue(status=FeatureStatus.OFF),
                business_data_limited=FeatureValue(status=FeatureStatus.OFF),
            ),
            crm=CRMFeatures(
                customer_specific_pricing=FeatureValue(status=FeatureStatus.OFF),
                advanced_tagging=FeatureValue(status=FeatureStatus.OFF),
                portal_document_sharing=FeatureValue(status=FeatureStatus.OFF),
            ),
        ),
    )


# ============================================================================
# PRODUCT LINE 3: SIGNGUY AI STUDIO (AI-ONLY)
# ============================================================================

def get_ai_basic() -> PlanConfig:
    """AI Basic: Text tools only"""
    return PlanConfig(
        plan_type=PlanType.AI_BASIC,
        product_line=ProductLine.AI_STUDIO,
        display_name="AI Basic",
        description="Essential AI text tools for content creation.",
        pricing=PlanPricing(
            monthly=29.0,
            annual=290.0,
            founder_monthly=None,
            founder_annual=None,
        ),
        processing_fees=ProcessingFees(
            invoice_fee_percent=0.0,
            webstore_fee_percent=0.0,
            stripe_connect_enabled=False,
            online_payments_enabled=False,
        ),
        founder_eligible=False,
        show_jobs_ui=False,
        show_payroll_ui=False,
        show_time_clock_ui=False,
        show_financials_ui=False,
        show_ai_assistant_ui=True,
        features=PlanFeatures(
            core=CoreModuleFeatures(
                customers=FeatureValue(status=FeatureStatus.OFF),
                jobs=FeatureValue(status=FeatureStatus.OFF),
                invoices=FeatureValue(status=FeatureStatus.OFF),
                online_invoice_payments=FeatureValue(status=FeatureStatus.OFF),
                dashboard=FeatureValue(status=FeatureStatus.ON),  # AI dashboard
                employees=FeatureValue(status=FeatureStatus.OFF, limit=0),
                time_clock=FeatureValue(status=FeatureStatus.OFF),
                time_clock_advanced=FeatureValue(status=FeatureStatus.OFF),
                tasks=FeatureValue(status=FeatureStatus.OFF),
                productivity=FeatureValue(status=FeatureStatus.OFF),
                productivity_advanced=FeatureValue(status=FeatureStatus.OFF),
                payroll=FeatureValue(status=FeatureStatus.OFF),
                financials=FeatureValue(status=FeatureStatus.OFF),
                financials_advanced=FeatureValue(status=FeatureStatus.OFF),
                company_settings=FeatureValue(status=FeatureStatus.ON),
                email_templates=FeatureValue(status=FeatureStatus.OFF),
            ),
            customer_portal=CustomerPortalFeatures(
                portal_access=FeatureValue(status=FeatureStatus.OFF),
                messaging=FeatureValue(status=FeatureStatus.OFF),
                artwork_approvals=FeatureValue(status=FeatureStatus.OFF),
                documents=FeatureValue(status=FeatureStatus.OFF),
                document_storage_mb=FeatureValue(status=FeatureStatus.OFF, limit=0),
            ),
            webstores=WebstoreFeatures(
                webstore_access=FeatureValue(status=FeatureStatus.OFF),
                num_stores=FeatureValue(status=FeatureStatus.OFF, limit=0),
                store_type_b2b=FeatureValue(status=FeatureStatus.OFF),
                store_type_fundraiser=FeatureValue(status=FeatureStatus.OFF),
                store_type_creator=FeatureValue(status=FeatureStatus.OFF),
                stripe_connect=FeatureValue(status=FeatureStatus.OFF),
                order_to_job_automation=FeatureValue(status=FeatureStatus.OFF),
                commission_tracking=FeatureValue(status=FeatureStatus.OFF),
                payout_tracking=FeatureValue(status=FeatureStatus.OFF),
                advanced_branding=FeatureValue(status=FeatureStatus.OFF),
                price_overrides=FeatureValue(status=FeatureStatus.OFF),
                bulk_order_tools=FeatureValue(status=FeatureStatus.OFF),
                store_analytics=FeatureValue(status=FeatureStatus.OFF),
                store_analytics_advanced=FeatureValue(status=FeatureStatus.OFF),
                fundraiser_goals=FeatureValue(status=FeatureStatus.OFF),
            ),
            ai_tools=AIToolsFeatures(
                ai_access=FeatureValue(status=FeatureStatus.ON),
                text_generation=FeatureValue(status=FeatureStatus.ON),
                image_generation=FeatureValue(status=FeatureStatus.OFF),
                monthly_generations=FeatureValue(status=FeatureStatus.LIMITED, limit=25),
                branding_kit_generator=FeatureValue(status=FeatureStatus.OFF),
                campaign_builder=FeatureValue(status=FeatureStatus.OFF),
                pricing_intelligence=FeatureValue(status=FeatureStatus.OFF),
                content_calendar=FeatureValue(status=FeatureStatus.OFF),
            ),
            ai_assistant=AIAssistantFeatures(
                assistant_access=FeatureValue(status=FeatureStatus.ON),
                monthly_queries=FeatureValue(status=FeatureStatus.LIMITED, limit=10),
                business_data_aware=FeatureValue(status=FeatureStatus.OFF),  # NO data access
                business_data_limited=FeatureValue(status=FeatureStatus.OFF),
            ),
            crm=CRMFeatures(
                customer_specific_pricing=FeatureValue(status=FeatureStatus.OFF),
                advanced_tagging=FeatureValue(status=FeatureStatus.OFF),
                portal_document_sharing=FeatureValue(status=FeatureStatus.OFF),
            ),
        ),
    )


def get_ai_pro() -> PlanConfig:
    """AI Pro: Text + Image generation"""
    return PlanConfig(
        plan_type=PlanType.AI_PRO,
        product_line=ProductLine.AI_STUDIO,
        display_name="AI Pro",
        description="Full AI toolkit with text and image generation.",
        pricing=PlanPricing(
            monthly=59.0,
            annual=590.0,
            founder_monthly=None,
            founder_annual=None,
        ),
        processing_fees=ProcessingFees(
            invoice_fee_percent=0.0,
            webstore_fee_percent=0.0,
            stripe_connect_enabled=False,
            online_payments_enabled=False,
        ),
        founder_eligible=False,
        show_jobs_ui=False,
        show_payroll_ui=False,
        show_time_clock_ui=False,
        show_financials_ui=False,
        show_ai_assistant_ui=True,
        features=PlanFeatures(
            core=CoreModuleFeatures(
                customers=FeatureValue(status=FeatureStatus.OFF),
                jobs=FeatureValue(status=FeatureStatus.OFF),
                invoices=FeatureValue(status=FeatureStatus.OFF),
                online_invoice_payments=FeatureValue(status=FeatureStatus.OFF),
                dashboard=FeatureValue(status=FeatureStatus.ON),
                employees=FeatureValue(status=FeatureStatus.OFF, limit=0),
                time_clock=FeatureValue(status=FeatureStatus.OFF),
                time_clock_advanced=FeatureValue(status=FeatureStatus.OFF),
                tasks=FeatureValue(status=FeatureStatus.OFF),
                productivity=FeatureValue(status=FeatureStatus.OFF),
                productivity_advanced=FeatureValue(status=FeatureStatus.OFF),
                payroll=FeatureValue(status=FeatureStatus.OFF),
                financials=FeatureValue(status=FeatureStatus.OFF),
                financials_advanced=FeatureValue(status=FeatureStatus.OFF),
                company_settings=FeatureValue(status=FeatureStatus.ON),
                email_templates=FeatureValue(status=FeatureStatus.OFF),
            ),
            customer_portal=CustomerPortalFeatures(
                portal_access=FeatureValue(status=FeatureStatus.OFF),
                messaging=FeatureValue(status=FeatureStatus.OFF),
                artwork_approvals=FeatureValue(status=FeatureStatus.OFF),
                documents=FeatureValue(status=FeatureStatus.OFF),
                document_storage_mb=FeatureValue(status=FeatureStatus.OFF, limit=0),
            ),
            webstores=WebstoreFeatures(
                webstore_access=FeatureValue(status=FeatureStatus.OFF),
                num_stores=FeatureValue(status=FeatureStatus.OFF, limit=0),
                store_type_b2b=FeatureValue(status=FeatureStatus.OFF),
                store_type_fundraiser=FeatureValue(status=FeatureStatus.OFF),
                store_type_creator=FeatureValue(status=FeatureStatus.OFF),
                stripe_connect=FeatureValue(status=FeatureStatus.OFF),
                order_to_job_automation=FeatureValue(status=FeatureStatus.OFF),
                commission_tracking=FeatureValue(status=FeatureStatus.OFF),
                payout_tracking=FeatureValue(status=FeatureStatus.OFF),
                advanced_branding=FeatureValue(status=FeatureStatus.OFF),
                price_overrides=FeatureValue(status=FeatureStatus.OFF),
                bulk_order_tools=FeatureValue(status=FeatureStatus.OFF),
                store_analytics=FeatureValue(status=FeatureStatus.OFF),
                store_analytics_advanced=FeatureValue(status=FeatureStatus.OFF),
                fundraiser_goals=FeatureValue(status=FeatureStatus.OFF),
            ),
            ai_tools=AIToolsFeatures(
                ai_access=FeatureValue(status=FeatureStatus.ON),
                text_generation=FeatureValue(status=FeatureStatus.ON),
                image_generation=FeatureValue(status=FeatureStatus.ON),
                monthly_generations=FeatureValue(status=FeatureStatus.LIMITED, limit=100),
                branding_kit_generator=FeatureValue(status=FeatureStatus.OFF),
                campaign_builder=FeatureValue(status=FeatureStatus.OFF),
                pricing_intelligence=FeatureValue(status=FeatureStatus.OFF),
                content_calendar=FeatureValue(status=FeatureStatus.OFF),
            ),
            ai_assistant=AIAssistantFeatures(
                assistant_access=FeatureValue(status=FeatureStatus.ON),
                monthly_queries=FeatureValue(status=FeatureStatus.LIMITED, limit=50),
                business_data_aware=FeatureValue(status=FeatureStatus.OFF),
                business_data_limited=FeatureValue(status=FeatureStatus.OFF),
            ),
            crm=CRMFeatures(
                customer_specific_pricing=FeatureValue(status=FeatureStatus.OFF),
                advanced_tagging=FeatureValue(status=FeatureStatus.OFF),
                portal_document_sharing=FeatureValue(status=FeatureStatus.OFF),
            ),
        ),
    )


def get_ai_max() -> PlanConfig:
    """AI Max: Unlimited AI with premium tools"""
    return PlanConfig(
        plan_type=PlanType.AI_MAX,
        product_line=ProductLine.AI_STUDIO,
        display_name="AI Max",
        description="Unlimited AI with premium tools like Branding Kit and Campaign Builder.",
        pricing=PlanPricing(
            monthly=99.0,
            annual=990.0,
            founder_monthly=None,
            founder_annual=None,
        ),
        processing_fees=ProcessingFees(
            invoice_fee_percent=0.0,
            webstore_fee_percent=0.0,
            stripe_connect_enabled=False,
            online_payments_enabled=False,
        ),
        founder_eligible=False,
        show_jobs_ui=False,
        show_payroll_ui=False,
        show_time_clock_ui=False,
        show_financials_ui=False,
        show_ai_assistant_ui=True,
        features=PlanFeatures(
            core=CoreModuleFeatures(
                customers=FeatureValue(status=FeatureStatus.OFF),
                jobs=FeatureValue(status=FeatureStatus.OFF),
                invoices=FeatureValue(status=FeatureStatus.OFF),
                online_invoice_payments=FeatureValue(status=FeatureStatus.OFF),
                dashboard=FeatureValue(status=FeatureStatus.ON),
                employees=FeatureValue(status=FeatureStatus.OFF, limit=0),
                time_clock=FeatureValue(status=FeatureStatus.OFF),
                time_clock_advanced=FeatureValue(status=FeatureStatus.OFF),
                tasks=FeatureValue(status=FeatureStatus.OFF),
                productivity=FeatureValue(status=FeatureStatus.OFF),
                productivity_advanced=FeatureValue(status=FeatureStatus.OFF),
                payroll=FeatureValue(status=FeatureStatus.OFF),
                financials=FeatureValue(status=FeatureStatus.OFF),
                financials_advanced=FeatureValue(status=FeatureStatus.OFF),
                company_settings=FeatureValue(status=FeatureStatus.ON),
                email_templates=FeatureValue(status=FeatureStatus.OFF),
            ),
            customer_portal=CustomerPortalFeatures(
                portal_access=FeatureValue(status=FeatureStatus.OFF),
                messaging=FeatureValue(status=FeatureStatus.OFF),
                artwork_approvals=FeatureValue(status=FeatureStatus.OFF),
                documents=FeatureValue(status=FeatureStatus.OFF),
                document_storage_mb=FeatureValue(status=FeatureStatus.OFF, limit=0),
            ),
            webstores=WebstoreFeatures(
                webstore_access=FeatureValue(status=FeatureStatus.OFF),
                num_stores=FeatureValue(status=FeatureStatus.OFF, limit=0),
                store_type_b2b=FeatureValue(status=FeatureStatus.OFF),
                store_type_fundraiser=FeatureValue(status=FeatureStatus.OFF),
                store_type_creator=FeatureValue(status=FeatureStatus.OFF),
                stripe_connect=FeatureValue(status=FeatureStatus.OFF),
                order_to_job_automation=FeatureValue(status=FeatureStatus.OFF),
                commission_tracking=FeatureValue(status=FeatureStatus.OFF),
                payout_tracking=FeatureValue(status=FeatureStatus.OFF),
                advanced_branding=FeatureValue(status=FeatureStatus.OFF),
                price_overrides=FeatureValue(status=FeatureStatus.OFF),
                bulk_order_tools=FeatureValue(status=FeatureStatus.OFF),
                store_analytics=FeatureValue(status=FeatureStatus.OFF),
                store_analytics_advanced=FeatureValue(status=FeatureStatus.OFF),
                fundraiser_goals=FeatureValue(status=FeatureStatus.OFF),
            ),
            ai_tools=AIToolsFeatures(
                ai_access=FeatureValue(status=FeatureStatus.ON),
                text_generation=FeatureValue(status=FeatureStatus.ON),
                image_generation=FeatureValue(status=FeatureStatus.ON),
                monthly_generations=FeatureValue(status=FeatureStatus.ON),  # Unlimited
                branding_kit_generator=FeatureValue(status=FeatureStatus.ON),
                campaign_builder=FeatureValue(status=FeatureStatus.ON),
                pricing_intelligence=FeatureValue(status=FeatureStatus.ON),
                content_calendar=FeatureValue(status=FeatureStatus.ON),
            ),
            ai_assistant=AIAssistantFeatures(
                assistant_access=FeatureValue(status=FeatureStatus.ON),
                monthly_queries=FeatureValue(status=FeatureStatus.ON),  # Unlimited
                business_data_aware=FeatureValue(status=FeatureStatus.OFF),  # Still NO data access
                business_data_limited=FeatureValue(status=FeatureStatus.OFF),
            ),
            crm=CRMFeatures(
                customer_specific_pricing=FeatureValue(status=FeatureStatus.OFF),
                advanced_tagging=FeatureValue(status=FeatureStatus.OFF),
                portal_document_sharing=FeatureValue(status=FeatureStatus.OFF),
            ),
        ),
    )


# ============================================================================
# PLAN REGISTRY
# ============================================================================

PLAN_CONFIGS = {
    # OS Plans
    PlanType.OS_STARTER: get_os_starter,
    PlanType.OS_PRO: get_os_pro,
    PlanType.OS_BUSINESS: get_os_business,
    # Webstore Plans
    PlanType.WS_LAUNCH: get_ws_launch,
    PlanType.WS_GROWTH: get_ws_growth,
    PlanType.WS_SCALE: get_ws_scale,
    # AI Studio Plans
    PlanType.AI_BASIC: get_ai_basic,
    PlanType.AI_PRO: get_ai_pro,
    PlanType.AI_MAX: get_ai_max,
}


def get_plan_config(plan_type: PlanType) -> PlanConfig:
    """Get configuration for a specific plan"""
    return PLAN_CONFIGS[plan_type]()


def get_all_plans() -> list[PlanConfig]:
    """Get all plan configurations"""
    return [func() for func in PLAN_CONFIGS.values()]


def get_plans_by_product_line(product_line: ProductLine) -> list[PlanConfig]:
    """Get all plans for a specific product line"""
    return [
        config for config in get_all_plans()
        if config.product_line == product_line
    ]


def get_founder_eligible_plans() -> list[PlanConfig]:
    """Get all plans eligible for founder pricing"""
    return [
        config for config in get_all_plans()
        if config.founder_eligible
    ]


# ============================================================================
# LEGACY COMPATIBILITY
# ============================================================================

def legacy_tier_to_plan(tier: str, is_founder: bool = False) -> PlanType:
    """
    Map legacy tier names to new plan types.
    Legacy tiers map to OS plans.
    """
    mapping = {
        "starter": PlanType.OS_STARTER,
        "pro": PlanType.OS_PRO,
        "business": PlanType.OS_BUSINESS,
        "tier_1": PlanType.OS_STARTER,
        "tier_2": PlanType.OS_PRO,
        "tier_3": PlanType.OS_BUSINESS,
        "founders_edition": PlanType.OS_BUSINESS,
        "free_trial": PlanType.OS_STARTER,
    }
    return mapping.get(tier.lower(), PlanType.OS_STARTER)
