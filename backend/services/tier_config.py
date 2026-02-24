"""
Tier Configuration Definitions

Pre-defined configurations for each subscription tier based on product requirements.
"""

from models.tiers import (
    TierLevel, TierConfig, TierFeatures, FeatureValue, FeatureStatus,
    CustomerPortalFeatures, WebstoreFeatures, WebstorePaymentFeatures,
    B2BFeatures, CreatorAffiliateFeatures, OrderManagementFeatures,
    PricingFeatures, AnalyticsFeatures, AIToolsFeatures, AIBusinessAssistantFeatures,
    TeamFeatures, CoreModuleFeatures, CommunicationsFeatures, IntegrationsFeatures,
    DataFeatures
)


def get_starter_tier() -> TierConfig:
    """Starter Tier: Hook small shops without giving away crown jewels"""
    return TierConfig(
        name="starter",
        level=TierLevel.STARTER,
        display_name="Starter",
        description="Perfect for getting started. Basic features for small sign shops.",
        price_monthly=0,
        price_yearly=0,
        features=TierFeatures(
            customer_portal=CustomerPortalFeatures(
                portal_access=FeatureValue(status=FeatureStatus.ON),
                dashboard=FeatureValue(status=FeatureStatus.ON),
                view_orders=FeatureValue(status=FeatureStatus.ON),
                view_quotes=FeatureValue(status=FeatureStatus.ON),
                view_invoices=FeatureValue(status=FeatureStatus.ON),
                messaging=FeatureValue(status=FeatureStatus.OFF),
                artwork_approvals=FeatureValue(status=FeatureStatus.ON),
                appointments=FeatureValue(status=FeatureStatus.OFF),
                profile_management=FeatureValue(status=FeatureStatus.ON),
                tax_exempt_status=FeatureValue(status=FeatureStatus.OFF),
                notification_preferences=FeatureValue(status=FeatureStatus.OFF),
                payment_history=FeatureValue(status=FeatureStatus.ON),
                online_payments=FeatureValue(status=FeatureStatus.ON),
                bnpl_options=FeatureValue(status=FeatureStatus.OFF),
            ),
            webstores=WebstoreFeatures(
                webstore_access=FeatureValue(status=FeatureStatus.ON),
                num_stores=FeatureValue(status=FeatureStatus.LIMITED, limit=1),
                business_stores=FeatureValue(status=FeatureStatus.OFF),
                fundraiser_stores=FeatureValue(status=FeatureStatus.ON),
                creator_stores=FeatureValue(status=FeatureStatus.OFF),
                event_stores=FeatureValue(status=FeatureStatus.ON),
                branding_basic=FeatureValue(status=FeatureStatus.ON),
                branding_logo=FeatureValue(status=FeatureStatus.ON),
                branding_colors=FeatureValue(status=FeatureStatus.OFF),
                branding_banner=FeatureValue(status=FeatureStatus.OFF),
                custom_domain=FeatureValue(status=FeatureStatus.OFF),
                product_variants=FeatureValue(status=FeatureStatus.ON),
                product_images=FeatureValue(status=FeatureStatus.LIMITED, limit=3),
                price_overrides=FeatureValue(status=FeatureStatus.OFF),
                personalization_fields=FeatureValue(status=FeatureStatus.ON),
                product_bundles=FeatureValue(status=FeatureStatus.OFF),
                minimum_order_qty=FeatureValue(status=FeatureStatus.OFF),
                bulk_import=FeatureValue(status=FeatureStatus.OFF),
                discount_codes=FeatureValue(status=FeatureStatus.ON),
                tax_calculation=FeatureValue(status=FeatureStatus.ON),
                shipping_basic=FeatureValue(status=FeatureStatus.ON),
                calculated_shipping=FeatureValue(status=FeatureStatus.OFF),
                free_shipping_threshold=FeatureValue(status=FeatureStatus.OFF),
                guest_checkout=FeatureValue(status=FeatureStatus.ON),
                customer_accounts=FeatureValue(status=FeatureStatus.ON),
                order_notes=FeatureValue(status=FeatureStatus.ON),
                confirmation_email=FeatureValue(status=FeatureStatus.ON),
                analytics_basic=FeatureValue(status=FeatureStatus.ON),
                analytics_advanced=FeatureValue(status=FeatureStatus.OFF),
                external_dashboard=FeatureValue(status=FeatureStatus.OFF),
                payout_tracking=FeatureValue(status=FeatureStatus.OFF),
                social_sharing=FeatureValue(status=FeatureStatus.ON),
                countdown_timer=FeatureValue(status=FeatureStatus.ON),
                progress_bar=FeatureValue(status=FeatureStatus.ON),
                leaderboard=FeatureValue(status=FeatureStatus.OFF),
            ),
            webstore_payments=WebstorePaymentFeatures(
                cash_check=FeatureValue(status=FeatureStatus.ON),
                stripe=FeatureValue(status=FeatureStatus.ON),
                paypal=FeatureValue(status=FeatureStatus.OFF),
                affirm=FeatureValue(status=FeatureStatus.OFF),
                klarna=FeatureValue(status=FeatureStatus.OFF),
                store_credit=FeatureValue(status=FeatureStatus.OFF),
            ),
            b2b=B2BFeatures(
                b2b_access=FeatureValue(status=FeatureStatus.OFF),
                volume_discounts=FeatureValue(status=FeatureStatus.OFF),
                net_terms=FeatureValue(status=FeatureStatus.OFF),
                budget_limits=FeatureValue(status=FeatureStatus.OFF),
                purchase_orders=FeatureValue(status=FeatureStatus.OFF),
                approval_workflows=FeatureValue(status=FeatureStatus.OFF),
            ),
            creator_affiliate=CreatorAffiliateFeatures(
                creator_access=FeatureValue(status=FeatureStatus.OFF),
                commission_tracking=FeatureValue(status=FeatureStatus.OFF),
                affiliate_links=FeatureValue(status=FeatureStatus.OFF),
                payout_management=FeatureValue(status=FeatureStatus.OFF),
            ),
            order_management=OrderManagementFeatures(
                order_list=FeatureValue(status=FeatureStatus.ON),
                filters=FeatureValue(status=FeatureStatus.ON),
                detail_view=FeatureValue(status=FeatureStatus.ON),
                status_updates=FeatureValue(status=FeatureStatus.ON),
                convert_to_job=FeatureValue(status=FeatureStatus.ON),
                packing_slips=FeatureValue(status=FeatureStatus.ON),
                bulk_updates=FeatureValue(status=FeatureStatus.OFF),
                search=FeatureValue(status=FeatureStatus.ON),
                internal_notes=FeatureValue(status=FeatureStatus.ON),
                refund=FeatureValue(status=FeatureStatus.ON),
                partial_fulfillment=FeatureValue(status=FeatureStatus.OFF),
                tracking_entry=FeatureValue(status=FeatureStatus.ON),
            ),
            pricing=PricingFeatures(
                basic_pricing=FeatureValue(status=FeatureStatus.ON),
                pricing_calculator=FeatureValue(status=FeatureStatus.ON),
                cost_tracking=FeatureValue(status=FeatureStatus.OFF),
                profit_margin_display=FeatureValue(status=FeatureStatus.OFF),
                price_templates=FeatureValue(status=FeatureStatus.ON),
                ai_price_suggestions=FeatureValue(status=FeatureStatus.OFF),
                local_market_analysis=FeatureValue(status=FeatureStatus.OFF),
                profit_optimization=FeatureValue(status=FeatureStatus.OFF),
                historical_trends=FeatureValue(status=FeatureStatus.OFF),
                quote_templates=FeatureValue(status=FeatureStatus.ON),
            ),
            analytics=AnalyticsFeatures(
                basic_summary=FeatureValue(status=FeatureStatus.ON),
                category_breakdown=FeatureValue(status=FeatureStatus.OFF),
                monthly_reports=FeatureValue(status=FeatureStatus.ON),
                profit_analysis=FeatureValue(status=FeatureStatus.OFF),
                customer_insights=FeatureValue(status=FeatureStatus.OFF),
                trend_analysis=FeatureValue(status=FeatureStatus.OFF),
                export_reports=FeatureValue(status=FeatureStatus.OFF),
                custom_reports=FeatureValue(status=FeatureStatus.OFF),
                scheduled_reports=FeatureValue(status=FeatureStatus.OFF),
                cash_flow_projections=FeatureValue(status=FeatureStatus.OFF),
            ),
            ai_tools=AIToolsFeatures(
                ai_access=FeatureValue(status=FeatureStatus.ON),
                monthly_generations=FeatureValue(status=FeatureStatus.LIMITED, limit=25),
                text_tools=FeatureValue(status=FeatureStatus.ON),
                image_generation=FeatureValue(status=FeatureStatus.OFF),
                image_analysis=FeatureValue(status=FeatureStatus.ON),
                ai_history=FeatureValue(status=FeatureStatus.ON),
                save_to_job=FeatureValue(status=FeatureStatus.OFF),
            ),
            ai_assistant=AIBusinessAssistantFeatures(
                chat=FeatureValue(status=FeatureStatus.ON),
                revenue_queries=FeatureValue(status=FeatureStatus.OFF),
                customer_queries=FeatureValue(status=FeatureStatus.OFF),
                job_queries=FeatureValue(status=FeatureStatus.OFF),
                product_queries=FeatureValue(status=FeatureStatus.OFF),
                trend_queries=FeatureValue(status=FeatureStatus.OFF),
                comparison_queries=FeatureValue(status=FeatureStatus.OFF),
                natural_language=FeatureValue(status=FeatureStatus.LIMITED, limit=10),
                export_insights=FeatureValue(status=FeatureStatus.OFF),
            ),
            team=TeamFeatures(
                team_members=FeatureValue(status=FeatureStatus.LIMITED, limit=1),
                role_management=FeatureValue(status=FeatureStatus.OFF),
                custom_roles=FeatureValue(status=FeatureStatus.OFF),
                activity_logs=FeatureValue(status=FeatureStatus.OFF),
                permissions=FeatureValue(status=FeatureStatus.OFF),
            ),
            core_modules=CoreModuleFeatures(
                customers=FeatureValue(status=FeatureStatus.ON),
                quotes=FeatureValue(status=FeatureStatus.ON),
                jobs=FeatureValue(status=FeatureStatus.ON),
                active_jobs=FeatureValue(status=FeatureStatus.ON),
                line_items=FeatureValue(status=FeatureStatus.ON),
                kanban=FeatureValue(status=FeatureStatus.OFF),
                job_log=FeatureValue(status=FeatureStatus.OFF),
                invoices=FeatureValue(status=FeatureStatus.ON),
                time_clock=FeatureValue(status=FeatureStatus.OFF),
                payroll=FeatureValue(status=FeatureStatus.OFF),
                tasks=FeatureValue(status=FeatureStatus.ON),
                calendar=FeatureValue(status=FeatureStatus.OFF),
                financial_tracking=FeatureValue(status=FeatureStatus.OFF),
            ),
            communications=CommunicationsFeatures(
                email_notifications=FeatureValue(status=FeatureStatus.ON),
                new_order_alerts=FeatureValue(status=FeatureStatus.ON),
                order_status_emails=FeatureValue(status=FeatureStatus.ON),
                proof_alerts=FeatureValue(status=FeatureStatus.ON),
                payment_alerts=FeatureValue(status=FeatureStatus.ON),
                low_stock_alerts=FeatureValue(status=FeatureStatus.OFF),
                abandoned_cart=FeatureValue(status=FeatureStatus.OFF),
                marketing_emails=FeatureValue(status=FeatureStatus.OFF),
                sms=FeatureValue(status=FeatureStatus.OFF),
                in_app_notifications=FeatureValue(status=FeatureStatus.ON),
            ),
            integrations=IntegrationsFeatures(
                sendgrid=FeatureValue(status=FeatureStatus.ON),
                stripe=FeatureValue(status=FeatureStatus.ON),
                paypal=FeatureValue(status=FeatureStatus.OFF),
                affirm=FeatureValue(status=FeatureStatus.OFF),
                klarna=FeatureValue(status=FeatureStatus.OFF),
                twilio=FeatureValue(status=FeatureStatus.OFF),
                quickbooks=FeatureValue(status=FeatureStatus.OFF),
                google_analytics=FeatureValue(status=FeatureStatus.OFF),
                facebook_pixel=FeatureValue(status=FeatureStatus.OFF),
                zapier=FeatureValue(status=FeatureStatus.OFF),
                mailchimp=FeatureValue(status=FeatureStatus.OFF),
            ),
            data=DataFeatures(
                storage_mb=FeatureValue(status=FeatureStatus.LIMITED, limit=100),
                data_export=FeatureValue(status=FeatureStatus.OFF),
                retention_years=FeatureValue(status=FeatureStatus.LIMITED, limit=1),
                backup=FeatureValue(status=FeatureStatus.OFF),
            ),
        )
    )


def get_pro_tier() -> TierConfig:
    """Pro Tier: Where real shops live"""
    return TierConfig(
        name="pro",
        level=TierLevel.PRO,
        display_name="Pro",
        description="Full-featured plan for growing sign shops. Everything you need to scale.",
        price_monthly=49,
        price_yearly=490,
        features=TierFeatures(
            customer_portal=CustomerPortalFeatures(
                portal_access=FeatureValue(status=FeatureStatus.ON),
                dashboard=FeatureValue(status=FeatureStatus.ON),
                view_orders=FeatureValue(status=FeatureStatus.ON),
                view_quotes=FeatureValue(status=FeatureStatus.ON),
                view_invoices=FeatureValue(status=FeatureStatus.ON),
                messaging=FeatureValue(status=FeatureStatus.ON),  # PRO
                artwork_approvals=FeatureValue(status=FeatureStatus.ON),
                appointments=FeatureValue(status=FeatureStatus.ON),  # PRO
                profile_management=FeatureValue(status=FeatureStatus.ON),
                tax_exempt_status=FeatureValue(status=FeatureStatus.ON),  # PRO
                notification_preferences=FeatureValue(status=FeatureStatus.ON),  # PRO
                payment_history=FeatureValue(status=FeatureStatus.ON),
                online_payments=FeatureValue(status=FeatureStatus.ON),
                bnpl_options=FeatureValue(status=FeatureStatus.OFF),  # BUSINESS only
            ),
            webstores=WebstoreFeatures(
                webstore_access=FeatureValue(status=FeatureStatus.ON),
                num_stores=FeatureValue(status=FeatureStatus.LIMITED, limit=5),  # PRO: 5 stores
                business_stores=FeatureValue(status=FeatureStatus.ON),  # PRO
                fundraiser_stores=FeatureValue(status=FeatureStatus.ON),
                creator_stores=FeatureValue(status=FeatureStatus.OFF),  # BUSINESS only
                event_stores=FeatureValue(status=FeatureStatus.ON),
                branding_basic=FeatureValue(status=FeatureStatus.ON),
                branding_logo=FeatureValue(status=FeatureStatus.ON),
                branding_colors=FeatureValue(status=FeatureStatus.ON),  # PRO
                branding_banner=FeatureValue(status=FeatureStatus.ON),  # PRO
                custom_domain=FeatureValue(status=FeatureStatus.OFF),  # BUSINESS only
                product_variants=FeatureValue(status=FeatureStatus.ON),
                product_images=FeatureValue(status=FeatureStatus.LIMITED, limit=10),  # PRO: 10 images
                price_overrides=FeatureValue(status=FeatureStatus.ON),  # PRO
                personalization_fields=FeatureValue(status=FeatureStatus.ON),
                product_bundles=FeatureValue(status=FeatureStatus.ON),  # PRO
                minimum_order_qty=FeatureValue(status=FeatureStatus.ON),  # PRO
                bulk_import=FeatureValue(status=FeatureStatus.ON),  # PRO
                discount_codes=FeatureValue(status=FeatureStatus.ON),
                tax_calculation=FeatureValue(status=FeatureStatus.ON),
                shipping_basic=FeatureValue(status=FeatureStatus.ON),
                calculated_shipping=FeatureValue(status=FeatureStatus.ON),  # PRO
                free_shipping_threshold=FeatureValue(status=FeatureStatus.ON),  # PRO
                guest_checkout=FeatureValue(status=FeatureStatus.ON),
                customer_accounts=FeatureValue(status=FeatureStatus.ON),
                order_notes=FeatureValue(status=FeatureStatus.ON),
                confirmation_email=FeatureValue(status=FeatureStatus.ON),
                analytics_basic=FeatureValue(status=FeatureStatus.ON),
                analytics_advanced=FeatureValue(status=FeatureStatus.ON),  # PRO
                external_dashboard=FeatureValue(status=FeatureStatus.ON),  # PRO
                payout_tracking=FeatureValue(status=FeatureStatus.OFF),  # BUSINESS only
                social_sharing=FeatureValue(status=FeatureStatus.ON),
                countdown_timer=FeatureValue(status=FeatureStatus.ON),
                progress_bar=FeatureValue(status=FeatureStatus.ON),
                leaderboard=FeatureValue(status=FeatureStatus.OFF),  # BUSINESS only
            ),
            webstore_payments=WebstorePaymentFeatures(
                cash_check=FeatureValue(status=FeatureStatus.ON),
                stripe=FeatureValue(status=FeatureStatus.ON),
                paypal=FeatureValue(status=FeatureStatus.ON),  # PRO
                affirm=FeatureValue(status=FeatureStatus.OFF),  # BUSINESS only
                klarna=FeatureValue(status=FeatureStatus.OFF),  # BUSINESS only
                store_credit=FeatureValue(status=FeatureStatus.ON),  # PRO
            ),
            b2b=B2BFeatures(
                b2b_access=FeatureValue(status=FeatureStatus.OFF),  # BUSINESS only
                volume_discounts=FeatureValue(status=FeatureStatus.OFF),
                net_terms=FeatureValue(status=FeatureStatus.OFF),
                budget_limits=FeatureValue(status=FeatureStatus.OFF),
                purchase_orders=FeatureValue(status=FeatureStatus.OFF),
                approval_workflows=FeatureValue(status=FeatureStatus.OFF),
            ),
            creator_affiliate=CreatorAffiliateFeatures(
                creator_access=FeatureValue(status=FeatureStatus.OFF),  # BUSINESS only
                commission_tracking=FeatureValue(status=FeatureStatus.OFF),
                affiliate_links=FeatureValue(status=FeatureStatus.OFF),
                payout_management=FeatureValue(status=FeatureStatus.OFF),
            ),
            order_management=OrderManagementFeatures(
                order_list=FeatureValue(status=FeatureStatus.ON),
                filters=FeatureValue(status=FeatureStatus.ON),
                detail_view=FeatureValue(status=FeatureStatus.ON),
                status_updates=FeatureValue(status=FeatureStatus.ON),
                convert_to_job=FeatureValue(status=FeatureStatus.ON),
                packing_slips=FeatureValue(status=FeatureStatus.ON),
                bulk_updates=FeatureValue(status=FeatureStatus.ON),  # PRO
                search=FeatureValue(status=FeatureStatus.ON),
                internal_notes=FeatureValue(status=FeatureStatus.ON),
                refund=FeatureValue(status=FeatureStatus.ON),
                partial_fulfillment=FeatureValue(status=FeatureStatus.ON),  # PRO
                tracking_entry=FeatureValue(status=FeatureStatus.ON),
            ),
            pricing=PricingFeatures(
                basic_pricing=FeatureValue(status=FeatureStatus.ON),
                pricing_calculator=FeatureValue(status=FeatureStatus.ON),
                cost_tracking=FeatureValue(status=FeatureStatus.ON),  # PRO
                profit_margin_display=FeatureValue(status=FeatureStatus.ON),  # PRO
                price_templates=FeatureValue(status=FeatureStatus.ON),
                ai_price_suggestions=FeatureValue(status=FeatureStatus.ON),  # PRO
                local_market_analysis=FeatureValue(status=FeatureStatus.OFF),  # BUSINESS only
                profit_optimization=FeatureValue(status=FeatureStatus.OFF),  # BUSINESS only
                historical_trends=FeatureValue(status=FeatureStatus.OFF),  # BUSINESS only
                quote_templates=FeatureValue(status=FeatureStatus.ON),
            ),
            analytics=AnalyticsFeatures(
                basic_summary=FeatureValue(status=FeatureStatus.ON),
                category_breakdown=FeatureValue(status=FeatureStatus.ON),  # PRO
                monthly_reports=FeatureValue(status=FeatureStatus.ON),
                profit_analysis=FeatureValue(status=FeatureStatus.ON),  # PRO
                customer_insights=FeatureValue(status=FeatureStatus.ON),  # PRO
                trend_analysis=FeatureValue(status=FeatureStatus.ON),  # PRO
                export_reports=FeatureValue(status=FeatureStatus.ON),  # PRO
                custom_reports=FeatureValue(status=FeatureStatus.OFF),  # BUSINESS only
                scheduled_reports=FeatureValue(status=FeatureStatus.OFF),  # BUSINESS only
                cash_flow_projections=FeatureValue(status=FeatureStatus.OFF),  # BUSINESS only
            ),
            ai_tools=AIToolsFeatures(
                ai_access=FeatureValue(status=FeatureStatus.ON),
                monthly_generations=FeatureValue(status=FeatureStatus.LIMITED, limit=100),  # PRO: 100
                text_tools=FeatureValue(status=FeatureStatus.ON),
                image_generation=FeatureValue(status=FeatureStatus.ON),  # PRO
                image_analysis=FeatureValue(status=FeatureStatus.ON),
                ai_history=FeatureValue(status=FeatureStatus.ON),
                save_to_job=FeatureValue(status=FeatureStatus.ON),  # PRO
            ),
            ai_assistant=AIBusinessAssistantFeatures(
                chat=FeatureValue(status=FeatureStatus.ON),
                revenue_queries=FeatureValue(status=FeatureStatus.ON),  # PRO
                customer_queries=FeatureValue(status=FeatureStatus.ON),  # PRO
                job_queries=FeatureValue(status=FeatureStatus.ON),  # PRO
                product_queries=FeatureValue(status=FeatureStatus.ON),  # PRO
                trend_queries=FeatureValue(status=FeatureStatus.ON),  # PRO
                comparison_queries=FeatureValue(status=FeatureStatus.ON),  # PRO
                natural_language=FeatureValue(status=FeatureStatus.LIMITED, limit=50),  # PRO: 50
                export_insights=FeatureValue(status=FeatureStatus.OFF),  # BUSINESS only
            ),
            team=TeamFeatures(
                team_members=FeatureValue(status=FeatureStatus.LIMITED, limit=5),  # PRO: 5 members
                role_management=FeatureValue(status=FeatureStatus.ON),  # PRO
                custom_roles=FeatureValue(status=FeatureStatus.OFF),  # BUSINESS only
                activity_logs=FeatureValue(status=FeatureStatus.ON),  # PRO
                permissions=FeatureValue(status=FeatureStatus.ON),  # PRO
            ),
            core_modules=CoreModuleFeatures(
                customers=FeatureValue(status=FeatureStatus.ON),
                quotes=FeatureValue(status=FeatureStatus.ON),
                jobs=FeatureValue(status=FeatureStatus.ON),
                active_jobs=FeatureValue(status=FeatureStatus.ON),
                line_items=FeatureValue(status=FeatureStatus.ON),
                kanban=FeatureValue(status=FeatureStatus.ON),  # PRO
                job_log=FeatureValue(status=FeatureStatus.ON),  # PRO
                invoices=FeatureValue(status=FeatureStatus.ON),
                time_clock=FeatureValue(status=FeatureStatus.ON),  # PRO
                payroll=FeatureValue(status=FeatureStatus.ON),  # PRO
                tasks=FeatureValue(status=FeatureStatus.ON),
                calendar=FeatureValue(status=FeatureStatus.ON),  # PRO
                financial_tracking=FeatureValue(status=FeatureStatus.ON),  # PRO
            ),
            communications=CommunicationsFeatures(
                email_notifications=FeatureValue(status=FeatureStatus.ON),
                new_order_alerts=FeatureValue(status=FeatureStatus.ON),
                order_status_emails=FeatureValue(status=FeatureStatus.ON),
                proof_alerts=FeatureValue(status=FeatureStatus.ON),
                payment_alerts=FeatureValue(status=FeatureStatus.ON),
                low_stock_alerts=FeatureValue(status=FeatureStatus.ON),  # PRO
                abandoned_cart=FeatureValue(status=FeatureStatus.ON),  # PRO
                marketing_emails=FeatureValue(status=FeatureStatus.OFF),  # BUSINESS only
                sms=FeatureValue(status=FeatureStatus.OFF),  # BUSINESS only
                in_app_notifications=FeatureValue(status=FeatureStatus.ON),
            ),
            integrations=IntegrationsFeatures(
                sendgrid=FeatureValue(status=FeatureStatus.ON),
                stripe=FeatureValue(status=FeatureStatus.ON),
                paypal=FeatureValue(status=FeatureStatus.ON),  # PRO
                affirm=FeatureValue(status=FeatureStatus.OFF),  # BUSINESS only
                klarna=FeatureValue(status=FeatureStatus.OFF),  # BUSINESS only
                twilio=FeatureValue(status=FeatureStatus.OFF),  # BUSINESS only
                quickbooks=FeatureValue(status=FeatureStatus.ON),  # PRO
                google_analytics=FeatureValue(status=FeatureStatus.ON),  # PRO
                facebook_pixel=FeatureValue(status=FeatureStatus.ON),  # PRO
                zapier=FeatureValue(status=FeatureStatus.OFF),  # BUSINESS only
                mailchimp=FeatureValue(status=FeatureStatus.OFF),  # BUSINESS only
            ),
            data=DataFeatures(
                storage_mb=FeatureValue(status=FeatureStatus.LIMITED, limit=1024),  # PRO: 1GB
                data_export=FeatureValue(status=FeatureStatus.ON),  # PRO
                retention_years=FeatureValue(status=FeatureStatus.LIMITED, limit=3),  # PRO: 3 years
                backup=FeatureValue(status=FeatureStatus.ON),  # PRO
            ),
        )
    )


def get_business_tier() -> TierConfig:
    """Tier 3 - Business: Everything ON. For shops that outgrew everyone else."""
    return TierConfig(
        name="business",
        level=TierLevel.BUSINESS,
        display_name="Business",
        description="Unlimited everything. For established shops that need it all.",
        price_monthly=149,
        price_yearly=1490,
        features=TierFeatures(
            customer_portal=CustomerPortalFeatures(
                portal_access=FeatureValue(status=FeatureStatus.ON),
                dashboard=FeatureValue(status=FeatureStatus.ON),
                view_orders=FeatureValue(status=FeatureStatus.ON),
                view_quotes=FeatureValue(status=FeatureStatus.ON),
                view_invoices=FeatureValue(status=FeatureStatus.ON),
                messaging=FeatureValue(status=FeatureStatus.ON),
                artwork_approvals=FeatureValue(status=FeatureStatus.ON),
                appointments=FeatureValue(status=FeatureStatus.ON),
                profile_management=FeatureValue(status=FeatureStatus.ON),
                tax_exempt_status=FeatureValue(status=FeatureStatus.ON),
                notification_preferences=FeatureValue(status=FeatureStatus.ON),
                payment_history=FeatureValue(status=FeatureStatus.ON),
                online_payments=FeatureValue(status=FeatureStatus.ON),
                bnpl_options=FeatureValue(status=FeatureStatus.ON),  # BUSINESS
            ),
            webstores=WebstoreFeatures(
                webstore_access=FeatureValue(status=FeatureStatus.ON),
                num_stores=FeatureValue(status=FeatureStatus.ON),  # BUSINESS: Unlimited
                business_stores=FeatureValue(status=FeatureStatus.ON),
                fundraiser_stores=FeatureValue(status=FeatureStatus.ON),
                creator_stores=FeatureValue(status=FeatureStatus.ON),  # BUSINESS
                event_stores=FeatureValue(status=FeatureStatus.ON),
                branding_basic=FeatureValue(status=FeatureStatus.ON),
                branding_logo=FeatureValue(status=FeatureStatus.ON),
                branding_colors=FeatureValue(status=FeatureStatus.ON),
                branding_banner=FeatureValue(status=FeatureStatus.ON),
                custom_domain=FeatureValue(status=FeatureStatus.ON),  # BUSINESS
                product_variants=FeatureValue(status=FeatureStatus.ON),
                product_images=FeatureValue(status=FeatureStatus.ON),  # BUSINESS: Unlimited
                price_overrides=FeatureValue(status=FeatureStatus.ON),
                personalization_fields=FeatureValue(status=FeatureStatus.ON),
                product_bundles=FeatureValue(status=FeatureStatus.ON),
                minimum_order_qty=FeatureValue(status=FeatureStatus.ON),
                bulk_import=FeatureValue(status=FeatureStatus.ON),
                discount_codes=FeatureValue(status=FeatureStatus.ON),
                tax_calculation=FeatureValue(status=FeatureStatus.ON),
                shipping_basic=FeatureValue(status=FeatureStatus.ON),
                calculated_shipping=FeatureValue(status=FeatureStatus.ON),
                free_shipping_threshold=FeatureValue(status=FeatureStatus.ON),
                guest_checkout=FeatureValue(status=FeatureStatus.ON),
                customer_accounts=FeatureValue(status=FeatureStatus.ON),
                order_notes=FeatureValue(status=FeatureStatus.ON),
                confirmation_email=FeatureValue(status=FeatureStatus.ON),
                analytics_basic=FeatureValue(status=FeatureStatus.ON),
                analytics_advanced=FeatureValue(status=FeatureStatus.ON),
                external_dashboard=FeatureValue(status=FeatureStatus.ON),
                payout_tracking=FeatureValue(status=FeatureStatus.ON),  # BUSINESS
                social_sharing=FeatureValue(status=FeatureStatus.ON),
                countdown_timer=FeatureValue(status=FeatureStatus.ON),
                progress_bar=FeatureValue(status=FeatureStatus.ON),
                leaderboard=FeatureValue(status=FeatureStatus.ON),  # BUSINESS
            ),
            webstore_payments=WebstorePaymentFeatures(
                cash_check=FeatureValue(status=FeatureStatus.ON),
                stripe=FeatureValue(status=FeatureStatus.ON),
                paypal=FeatureValue(status=FeatureStatus.ON),
                affirm=FeatureValue(status=FeatureStatus.ON),  # BUSINESS
                klarna=FeatureValue(status=FeatureStatus.ON),  # BUSINESS
                store_credit=FeatureValue(status=FeatureStatus.ON),
            ),
            b2b=B2BFeatures(
                b2b_access=FeatureValue(status=FeatureStatus.ON),  # BUSINESS
                volume_discounts=FeatureValue(status=FeatureStatus.ON),  # BUSINESS
                net_terms=FeatureValue(status=FeatureStatus.ON),  # BUSINESS
                budget_limits=FeatureValue(status=FeatureStatus.ON),  # BUSINESS
                purchase_orders=FeatureValue(status=FeatureStatus.ON),  # BUSINESS
                approval_workflows=FeatureValue(status=FeatureStatus.ON),  # BUSINESS
            ),
            creator_affiliate=CreatorAffiliateFeatures(
                creator_access=FeatureValue(status=FeatureStatus.ON),  # BUSINESS
                commission_tracking=FeatureValue(status=FeatureStatus.ON),  # BUSINESS
                affiliate_links=FeatureValue(status=FeatureStatus.ON),  # BUSINESS
                payout_management=FeatureValue(status=FeatureStatus.ON),  # BUSINESS
            ),
            order_management=OrderManagementFeatures(
                order_list=FeatureValue(status=FeatureStatus.ON),
                filters=FeatureValue(status=FeatureStatus.ON),
                detail_view=FeatureValue(status=FeatureStatus.ON),
                status_updates=FeatureValue(status=FeatureStatus.ON),
                convert_to_job=FeatureValue(status=FeatureStatus.ON),
                packing_slips=FeatureValue(status=FeatureStatus.ON),
                bulk_updates=FeatureValue(status=FeatureStatus.ON),
                search=FeatureValue(status=FeatureStatus.ON),
                internal_notes=FeatureValue(status=FeatureStatus.ON),
                refund=FeatureValue(status=FeatureStatus.ON),
                partial_fulfillment=FeatureValue(status=FeatureStatus.ON),
                tracking_entry=FeatureValue(status=FeatureStatus.ON),
            ),
            pricing=PricingFeatures(
                basic_pricing=FeatureValue(status=FeatureStatus.ON),
                pricing_calculator=FeatureValue(status=FeatureStatus.ON),
                cost_tracking=FeatureValue(status=FeatureStatus.ON),
                profit_margin_display=FeatureValue(status=FeatureStatus.ON),
                price_templates=FeatureValue(status=FeatureStatus.ON),
                ai_price_suggestions=FeatureValue(status=FeatureStatus.ON),
                local_market_analysis=FeatureValue(status=FeatureStatus.ON),  # BUSINESS
                profit_optimization=FeatureValue(status=FeatureStatus.ON),  # BUSINESS
                historical_trends=FeatureValue(status=FeatureStatus.ON),  # BUSINESS
                quote_templates=FeatureValue(status=FeatureStatus.ON),
            ),
            analytics=AnalyticsFeatures(
                basic_summary=FeatureValue(status=FeatureStatus.ON),
                category_breakdown=FeatureValue(status=FeatureStatus.ON),
                monthly_reports=FeatureValue(status=FeatureStatus.ON),
                profit_analysis=FeatureValue(status=FeatureStatus.ON),
                customer_insights=FeatureValue(status=FeatureStatus.ON),
                trend_analysis=FeatureValue(status=FeatureStatus.ON),
                export_reports=FeatureValue(status=FeatureStatus.ON),
                custom_reports=FeatureValue(status=FeatureStatus.ON),  # BUSINESS
                scheduled_reports=FeatureValue(status=FeatureStatus.ON),  # BUSINESS
                cash_flow_projections=FeatureValue(status=FeatureStatus.ON),  # BUSINESS
            ),
            ai_tools=AIToolsFeatures(
                ai_access=FeatureValue(status=FeatureStatus.ON),
                monthly_generations=FeatureValue(status=FeatureStatus.ON),  # BUSINESS: Unlimited
                text_tools=FeatureValue(status=FeatureStatus.ON),
                image_generation=FeatureValue(status=FeatureStatus.ON),
                image_analysis=FeatureValue(status=FeatureStatus.ON),
                ai_history=FeatureValue(status=FeatureStatus.ON),
                save_to_job=FeatureValue(status=FeatureStatus.ON),
            ),
            ai_assistant=AIBusinessAssistantFeatures(
                chat=FeatureValue(status=FeatureStatus.ON),
                revenue_queries=FeatureValue(status=FeatureStatus.ON),
                customer_queries=FeatureValue(status=FeatureStatus.ON),
                job_queries=FeatureValue(status=FeatureStatus.ON),
                product_queries=FeatureValue(status=FeatureStatus.ON),
                trend_queries=FeatureValue(status=FeatureStatus.ON),
                comparison_queries=FeatureValue(status=FeatureStatus.ON),
                natural_language=FeatureValue(status=FeatureStatus.ON),  # BUSINESS: Unlimited
                export_insights=FeatureValue(status=FeatureStatus.ON),  # BUSINESS
            ),
            team=TeamFeatures(
                team_members=FeatureValue(status=FeatureStatus.ON),  # BUSINESS: Unlimited
                role_management=FeatureValue(status=FeatureStatus.ON),
                custom_roles=FeatureValue(status=FeatureStatus.ON),  # BUSINESS
                activity_logs=FeatureValue(status=FeatureStatus.ON),
                permissions=FeatureValue(status=FeatureStatus.ON),
            ),
            core_modules=CoreModuleFeatures(
                customers=FeatureValue(status=FeatureStatus.ON),
                quotes=FeatureValue(status=FeatureStatus.ON),
                jobs=FeatureValue(status=FeatureStatus.ON),
                active_jobs=FeatureValue(status=FeatureStatus.ON),
                line_items=FeatureValue(status=FeatureStatus.ON),
                kanban=FeatureValue(status=FeatureStatus.ON),
                job_log=FeatureValue(status=FeatureStatus.ON),
                invoices=FeatureValue(status=FeatureStatus.ON),
                time_clock=FeatureValue(status=FeatureStatus.ON),
                payroll=FeatureValue(status=FeatureStatus.ON),
                tasks=FeatureValue(status=FeatureStatus.ON),
                calendar=FeatureValue(status=FeatureStatus.ON),
                financial_tracking=FeatureValue(status=FeatureStatus.ON),
            ),
            communications=CommunicationsFeatures(
                email_notifications=FeatureValue(status=FeatureStatus.ON),
                new_order_alerts=FeatureValue(status=FeatureStatus.ON),
                order_status_emails=FeatureValue(status=FeatureStatus.ON),
                proof_alerts=FeatureValue(status=FeatureStatus.ON),
                payment_alerts=FeatureValue(status=FeatureStatus.ON),
                low_stock_alerts=FeatureValue(status=FeatureStatus.ON),
                abandoned_cart=FeatureValue(status=FeatureStatus.ON),
                marketing_emails=FeatureValue(status=FeatureStatus.ON),  # BUSINESS
                sms=FeatureValue(status=FeatureStatus.ON),  # BUSINESS
                in_app_notifications=FeatureValue(status=FeatureStatus.ON),
            ),
            integrations=IntegrationsFeatures(
                sendgrid=FeatureValue(status=FeatureStatus.ON),
                stripe=FeatureValue(status=FeatureStatus.ON),
                paypal=FeatureValue(status=FeatureStatus.ON),
                affirm=FeatureValue(status=FeatureStatus.ON),  # BUSINESS
                klarna=FeatureValue(status=FeatureStatus.ON),  # BUSINESS
                twilio=FeatureValue(status=FeatureStatus.ON),  # BUSINESS
                quickbooks=FeatureValue(status=FeatureStatus.ON),
                google_analytics=FeatureValue(status=FeatureStatus.ON),
                facebook_pixel=FeatureValue(status=FeatureStatus.ON),
                zapier=FeatureValue(status=FeatureStatus.ON),  # BUSINESS
                mailchimp=FeatureValue(status=FeatureStatus.ON),  # BUSINESS
            ),
            data=DataFeatures(
                storage_mb=FeatureValue(status=FeatureStatus.LIMITED, limit=5120),  # BUSINESS: 5GB
                data_export=FeatureValue(status=FeatureStatus.ON),
                retention_years=FeatureValue(status=FeatureStatus.ON),  # BUSINESS: Unlimited
                backup=FeatureValue(status=FeatureStatus.ON),
            ),
        )
    )


# All tiers
TIER_CONFIGS = {
    TierLevel.STARTER: get_starter_tier,
    TierLevel.PRO: get_pro_tier,
    TierLevel.BUSINESS: get_business_tier,
}


def get_tier_config(tier: TierLevel) -> TierConfig:
    """Get the configuration for a specific tier"""
    return TIER_CONFIGS[tier]()


def get_all_tiers() -> list[TierConfig]:
    """Get all tier configurations"""
    return [get_starter_tier(), get_pro_tier(), get_business_tier()]
