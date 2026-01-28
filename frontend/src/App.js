import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AppProvider } from "./context/AppContext";
import { MainLayout } from "./components/MainLayout";
import { Toaster } from "./components/ui/sonner";

// Pages
import Dashboard from "./pages/Dashboard";
import Customers from "./pages/Customers";
import Quotes from "./pages/Quotes";
import Jobs, { JobDetails } from "./pages/Jobs";
import Invoices from "./pages/Invoices";
import TimeClock from "./pages/TimeClock";
import Payroll from "./pages/Payroll";
import Productivity from "./pages/Productivity";
import Financials from "./pages/Financials";
import AITools from "./pages/AITools";
import Webstores from "./pages/Webstores";

import "./App.css";

function App() {
  return (
    <AppProvider>
      <BrowserRouter>
        <MainLayout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/customers" element={<Customers />} />
            <Route path="/quotes" element={<Quotes />} />
            <Route path="/jobs" element={<Jobs />} />
            <Route path="/jobs/:id" element={<JobDetails />} />
            <Route path="/invoices" element={<Invoices />} />
            <Route path="/timeclock" element={<TimeClock />} />
            <Route path="/payroll" element={<Payroll />} />
            <Route path="/productivity" element={<Productivity />} />
            <Route path="/financials" element={<Financials />} />
            <Route path="/ai-tools" element={<AITools />} />
            <Route path="/webstores" element={<Webstores />} />
          </Routes>
        </MainLayout>
        <Toaster position="top-right" richColors />
      </BrowserRouter>
    </AppProvider>
  );
}

export default App;
