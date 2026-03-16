import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AppProvider } from "./context/AppContext";
import { ThemeProvider } from "./context/ThemeContext";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { TierProvider } from "./context/TierContext";
import { PlanProvider } from "./contexts/PlanContext";
import { MainLayout } from "./components/MainLayout";
import { UpgradeModal } from "./components/UpgradeModal";
import { TrialLockout } from "./components/TrialLockout";
import ScrollToTop from "./components/ScrollToTop";
import { Toaster } from "./components/ui/sonner";
import { Loader2 } from "lucide-react";

// Pages
import Dashboard from "./pages/Dashboard";
import Customers from "./pages/Customers";
// Quotes page deprecated - quotes are now jobs with status=quote
import Jobs, { JobDetails } from "./pages/Jobs";
import Invoices from "./pages/Invoices";
import TimeClock from "./pages/TimeClock";
import Payroll from "./pages/Payroll";
import Productivity from "./pages/Productivity";
import Financials from "./pages/Financials";
import ProfitMarginAnalytics from "./pages/ProfitMarginAnalytics";
import AITools from "./pages/AITools";
import AIAssistant from "./pages/AIAssistant";
import Webstores from "./pages/Webstores";
import Products from "./pages/Products";
import Storefront from "./pages/Storefront";
import Approvals from "./pages/Approvals";
import Documents from "./pages/Documents/Documents";
import Login from "./pages/Login";
import UserManagement from "./pages/UserManagement";
import Pricing from "./pages/Pricing";
import PricingSettings from "./pages/PricingSettings";
import PricingSetup from "./pages/PricingSetup";
import OnboardingHub from "./pages/OnboardingHub";
import CompanySettings from "./pages/CompanySettings";
import ProductionSettings from "./pages/settings/ProductionSettings";
import BackupRestore from "./pages/settings/BackupRestore";
import CommunityHub from "./pages/CommunityHub";
import PromoCodes from "./pages/PromoCodes";
import EmailTemplates from "./pages/EmailTemplates";
import PaymentSettings from "./pages/Admin/PaymentSettings";

// Customer Portal Pages
import PortalLogin from "./pages/PortalLogin";
import PortalDashboard from "./pages/PortalDashboard";
import { PortalOrders, PortalOrderDetail } from "./pages/PortalOrders";
import { PortalProofs, PortalProofDetail } from "./pages/PortalProofs";
import { PortalMessages, PortalConversation } from "./pages/PortalMessages";
import PortalProfile from "./pages/PortalProfile";
import PortalDocuments from "./pages/PortalDocuments";
import { PortalQuotes, PortalInvoices, PortalAppointments } from "./pages/PortalPages";
import { PortalForms, PortalFormDetail } from "./pages/PortalForms";

// Employee Portal Pages
import EmployeePortalLogin from "./pages/EmployeePortalLogin";
import EmployeePortalDashboard from "./pages/EmployeePortalDashboard";
import EmployeePortalJob from "./pages/EmployeePortalJob";
import EmployeePortalPay from "./pages/EmployeePortalPay";
import EmployeePortalTasks from "./pages/EmployeePortalTasks";
import EmployeePortalProfile from "./pages/EmployeePortalProfile";

// Admin Portal (Communications Hub)
import AdminPortal from "./pages/AdminPortal";

// Billing Pages
import PricingPage from "./pages/PricingPage";
import PricingPlansV2 from "./pages/PricingPlansV2";
import BillingSuccess from "./pages/BillingSuccess";
import BillingCancel from "./pages/BillingCancel";
import BillingManagement from "./pages/BillingManagement";

// Questionnaires
import Questionnaires from "./pages/Questionnaires";
import PublicQuestionnaire from "./pages/PublicQuestionnaire";

// Public Pages
import LandingPage from "./pages/LandingPage";
import FeaturesPage from "./pages/FeaturesPage";
import PricingPagePublic from "./pages/PricingPagePublic";
import FoundersEditionPricing from "./pages/FoundersEditionPricing";
import WhyFounderPage from "./pages/WhyFounderPage";
import AboutPage from "./pages/AboutPage";
import ContactPage from "./pages/ContactPage";

// Marketing Pages - Product Overviews
import {
  PlatformPage,
  WebstoresPage as WebstoresMarketingPage,
  AIStudioPage,
  StarterPlanPage,
  ProPlanPage,
  BusinessPlanPage,
  WebstoreLaunchPage,
  WebstoreGrowthPage,
  WebstoreScalePage,
  AIBasicPage,
  AIProPage,
  AIMaxPage
} from "./pages/marketing";

// Documentation Pages
import DocsLayout from "./components/DocsLayout";
import DocsOverview from "./pages/docs/DocsOverview";
import GettingStarted from "./pages/docs/GettingStarted";
import DocsCustomers from "./pages/docs/DocsCustomers";
import DocsQuotesJobs from "./pages/docs/DocsQuotesJobs";
import DocsInvoicing from "./pages/docs/DocsInvoicing";
import DocsPricingCalculator from "./pages/docs/DocsPricingCalculator";
import DocsAITools from "./pages/docs/DocsAITools";
import DocsTimeTracking from "./pages/docs/DocsTimeTracking";
import DocsEmployees from "./pages/docs/DocsEmployees";
import DocsFAQ from "./pages/docs/DocsFAQ";
import DocsWebstores from "./pages/docs/DocsWebstores";
import DocsCustomerPortal from "./pages/docs/DocsCustomerPortal";
import DocsFinancials from "./pages/docs/DocsFinancials";
import DocsProductivity from "./pages/docs/DocsProductivity";

import "./App.css";

// Loading Screen Component
function LoadingScreen() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--bg-primary)]">
      <div className="flex flex-col items-center gap-4">
        <Loader2 className="h-8 w-8 animate-spin text-teal-500" />
        <p className="text-[var(--text-secondary)]">Loading...</p>
      </div>
    </div>
  );
}

// Protected Route Wrapper
function ProtectedRoutes() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <TrialLockout>
      <MainLayout>
        <Routes>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/customers" element={<Customers />} />
          {/* Quotes redirect to Jobs with filter - quotes are now jobs with status=quote */}
          <Route path="/quotes" element={<Navigate to="/jobs?filter=quotes" replace />} />
          <Route path="/jobs" element={<Jobs />} />
          <Route path="/jobs/:id" element={<JobDetails />} />
          <Route path="/invoices" element={<Invoices />} />
          <Route path="/approvals" element={<Approvals />} />
          <Route path="/admin-portal" element={<AdminPortal />} />
          <Route path="/documents" element={<Documents />} />
          <Route path="/timeclock" element={<TimeClock />} />
          <Route path="/payroll" element={<Payroll />} />
          <Route path="/productivity" element={<Productivity />} />
          <Route path="/financials" element={<Financials />} />
          <Route path="/reports/profit-margin" element={<ProfitMarginAnalytics />} />
          <Route path="/ai-tools" element={<AITools />} />
          <Route path="/ai-assistant" element={<AIAssistant />} />
          <Route path="/webstores" element={<Webstores />} />
          <Route path="/products" element={<Products />} />
          <Route path="/users" element={<UserManagement />} />
          <Route path="/onboarding" element={<OnboardingHub />} />
          <Route path="/settings" element={<CompanySettings />} />
          <Route path="/settings/pricing-setup" element={<PricingSetup />} />
          <Route path="/settings/email-templates" element={<EmailTemplates />} />
          <Route path="/settings/production" element={<ProductionSettings />} />
          <Route path="/settings/backup" element={<BackupRestore />} />
          <Route path="/community" element={<CommunityHub />} />
          <Route path="/admin/payments" element={<PaymentSettings />} />
          <Route path="/promo-codes" element={<PromoCodes />} />
          <Route path="/pricing-calculator" element={<Pricing />} />
          <Route path="/pricing-calculator/settings" element={<PricingSettings />} />
          <Route path="/billing" element={<BillingManagement />} />
          <Route path="/questionnaires" element={<Questionnaires />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </MainLayout>
    </TrialLockout>
  );
}

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <TierProvider>
          <PlanProvider>
          <AppProvider>
            <BrowserRouter>
              <ScrollToTop />
              <Routes>
                {/* Public Landing Page - ROOT URL shows marketing site */}
                <Route path="/" element={<LandingPage />} />
                <Route path="/home" element={<LandingPage />} />
                <Route path="/features" element={<FeaturesPage />} />
                <Route path="/pricing" element={<FoundersEditionPricing />} />
                <Route path="/pricing-legacy" element={<PricingPagePublic />} />
                <Route path="/founders" element={<FoundersEditionPricing />} />
                <Route path="/why-founder" element={<WhyFounderPage />} />
                <Route path="/about" element={<AboutPage />} />
                <Route path="/contact" element={<ContactPage />} />
                
                {/* Marketing - Product Overview Pages */}
                <Route path="/platform" element={<PlatformPage />} />
                <Route path="/webstores-overview" element={<WebstoresMarketingPage />} />
                <Route path="/ai-studio" element={<AIStudioPage />} />
                
                {/* Marketing - OS Plan Detail Pages */}
                <Route path="/starter" element={<StarterPlanPage />} />
                <Route path="/pro" element={<ProPlanPage />} />
                <Route path="/business" element={<BusinessPlanPage />} />
                
                {/* Marketing - Webstore Plan Detail Pages */}
                <Route path="/webstore-launch" element={<WebstoreLaunchPage />} />
                <Route path="/webstore-growth" element={<WebstoreGrowthPage />} />
                <Route path="/webstore-scale" element={<WebstoreScalePage />} />
                
                {/* Marketing - AI Studio Plan Detail Pages */}
                <Route path="/ai-basic" element={<AIBasicPage />} />
                <Route path="/ai-pro" element={<AIProPage />} />
                <Route path="/ai-max" element={<AIMaxPage />} />
                
                {/* Auth Routes - Public */}
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Navigate to="/login?register=true" replace />} />
                
                {/* Documentation Routes */}
                <Route path="/docs" element={<DocsLayout />}>
                  <Route index element={<DocsOverview />} />
                  <Route path="getting-started" element={<GettingStarted />} />
                  <Route path="customers" element={<DocsCustomers />} />
                  <Route path="quotes-jobs" element={<DocsQuotesJobs />} />
                  <Route path="invoicing" element={<DocsInvoicing />} />
                  <Route path="pricing-calculator" element={<DocsPricingCalculator />} />
                  <Route path="ai-tools" element={<DocsAITools />} />
                  <Route path="time-tracking" element={<DocsTimeTracking />} />
                  <Route path="employees" element={<DocsEmployees />} />
                  <Route path="webstores" element={<DocsWebstores />} />
                  <Route path="customer-portal" element={<DocsCustomerPortal />} />
                  <Route path="financials" element={<DocsFinancials />} />
                  <Route path="productivity" element={<DocsProductivity />} />
                  <Route path="faq" element={<DocsFAQ />} />
                </Route>
                
                {/* Public Storefront - No Auth Required */}
                <Route path="/store/:storeId" element={<Storefront />} />
                
                {/* Public Questionnaire - No Auth Required */}
                <Route path="/questionnaire/:questionnaireId" element={<PublicQuestionnaire />} />
                
                {/* Public Pricing Page - New Multi-Product Version */}
                <Route path="/pricing-plans" element={<PricingPlansV2 />} />
                <Route path="/pricing-plans-old" element={<PricingPage />} />
                
                {/* Billing Routes */}
                <Route path="/billing/success" element={<BillingSuccess />} />
                <Route path="/billing/cancel" element={<BillingCancel />} />
                
                {/* Customer Portal Routes - Separate Auth */}
                <Route path="/customer-portal/login" element={<PortalLogin />} />
                <Route path="/customer-portal" element={<PortalDashboard />} />
                <Route path="/customer-portal/orders" element={<PortalOrders />} />
                <Route path="/customer-portal/orders/:orderId" element={<PortalOrderDetail />} />
                <Route path="/customer-portal/forms" element={<PortalForms />} />
                <Route path="/customer-portal/forms/:requestId" element={<PortalFormDetail />} />
                <Route path="/customer-portal/quotes" element={<PortalQuotes />} />
                <Route path="/customer-portal/invoices" element={<PortalInvoices />} />
                <Route path="/customer-portal/documents" element={<PortalDocuments />} />
                <Route path="/customer-portal/messages" element={<PortalMessages />} />
                <Route path="/customer-portal/messages/:conversationId" element={<PortalConversation />} />
                <Route path="/customer-portal/proofs" element={<PortalProofs />} />
                <Route path="/customer-portal/proofs/:proofId" element={<PortalProofDetail />} />
                <Route path="/customer-portal/appointments" element={<PortalAppointments />} />
                <Route path="/customer-portal/profile" element={<PortalProfile />} />
                
                {/* Employee Portal Routes - Separate Auth */}
                <Route path="/employee-portal/login" element={<EmployeePortalLogin />} />
                <Route path="/employee-portal" element={<EmployeePortalDashboard />} />
                <Route path="/employee-portal/jobs/:jobId" element={<EmployeePortalJob />} />
                <Route path="/employee-portal/pay" element={<EmployeePortalPay />} />
                <Route path="/employee-portal/tasks" element={<EmployeePortalTasks />} />
                <Route path="/employee-portal/profile" element={<EmployeePortalProfile />} />
                
                {/* Protected Admin Routes */}
                <Route path="/*" element={<ProtectedRoutes />} />
              </Routes>
              <UpgradeModal />
              <Toaster position="top-right" richColors />
            </BrowserRouter>
          </AppProvider>
        </PlanProvider>
      </TierProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
