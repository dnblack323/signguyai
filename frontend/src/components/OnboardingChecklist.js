import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Progress } from '../components/ui/progress';
import {
  CheckCircle2, Circle, ChevronRight, X,
  Building2, Users, Calculator, Briefcase, 
  Clock, UserPlus, Palette, Sparkles, Mail,
  Store, FileText, Upload, DollarSign, Settings
} from 'lucide-react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

const checklistItems = [
  // Essential Setup
  {
    id: 'company_info',
    title: 'Set up your company info',
    description: 'Add your business name, logo, and contact details',
    link: '/settings',
    icon: Building2,
    checkKey: 'has_company_info',
    category: 'essential'
  },
  {
    id: 'pricing',
    title: 'Configure pricing calculator',
    description: 'Set your material costs, labor rates, and markups',
    link: '/pricing-calculator/settings',
    icon: Calculator,
    checkKey: 'has_pricing_config',
    category: 'essential'
  },
  {
    id: 'email_templates',
    title: 'Customize email templates',
    description: 'Personalize emails sent to your customers',
    link: '/settings/email-templates',
    icon: Mail,
    checkKey: 'has_email_templates',
    category: 'essential'
  },
  // Customer Setup
  {
    id: 'first_customer',
    title: 'Add your first customer',
    description: 'Start building your customer database',
    link: '/customers',
    icon: Users,
    checkKey: 'has_customers',
    category: 'customers'
  },
  {
    id: 'import_customers',
    title: 'Import existing customers',
    description: 'Upload a CSV to import your customer list',
    link: '/customers?import=true',
    icon: Upload,
    checkKey: 'has_imported_customers',
    category: 'customers'
  },
  // Team Setup
  {
    id: 'first_employee',
    title: 'Add an employee',
    description: 'Set up team members for time tracking and payroll',
    link: '/employees',
    icon: UserPlus,
    checkKey: 'has_employees',
    category: 'team'
  },
  // Business Operations
  {
    id: 'first_quote',
    title: 'Create your first quote',
    description: 'Use the pricing calculators to build a quote',
    link: '/quotes/new',
    icon: Briefcase,
    checkKey: 'has_quotes',
    category: 'operations'
  },
  {
    id: 'setup_webstore',
    title: 'Create a webstore',
    description: 'Set up an online store for customers or fundraisers',
    link: '/webstores',
    icon: Store,
    checkKey: 'has_webstores',
    category: 'operations'
  },
  {
    id: 'upload_documents',
    title: 'Upload document templates',
    description: 'Add contracts, forms, and templates to your library',
    link: '/documents',
    icon: FileText,
    checkKey: 'has_documents',
    category: 'operations'
  },
  // Explore Features
  {
    id: 'explore_ai',
    title: 'Try the AI tools',
    description: 'Generate logos, designs, and business content',
    link: '/ai-tools',
    icon: Sparkles,
    checkKey: 'has_used_ai',
    category: 'explore'
  }
];

export default function OnboardingChecklist({ onDismiss }) {
  const [checklist, setChecklist] = useState({});
  const [loading, setLoading] = useState(true);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    // Check if already dismissed
    const isDismissed = localStorage.getItem('onboarding_dismissed');
    if (isDismissed) {
      setDismissed(true);
      setLoading(false);
      return;
    }

    fetchChecklistStatus();
  }, []);

  const fetchChecklistStatus = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      const response = await axios.get(`${API}/api/dashboard/onboarding-status`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setChecklist(response.data);
    } catch (err) {
      console.error('Error fetching checklist status:', err);
      // Fallback to empty state
      setChecklist({});
    } finally {
      setLoading(false);
    }
  };

  const handleDismiss = () => {
    localStorage.setItem('onboarding_dismissed', 'true');
    setDismissed(true);
    onDismiss?.();
  };

  const completedCount = checklistItems.filter(item => checklist[item.checkKey]).length;
  const progress = (completedCount / checklistItems.length) * 100;

  // Don't show if dismissed or all complete
  if (dismissed || loading || progress === 100) {
    return null;
  }

  return (
    <Card className="border-2 border-blue-500/30 bg-gradient-to-br from-blue-500/5 to-purple-500/5">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <CardTitle className="text-lg" style={{ color: 'var(--text)' }}>
                Getting Started
              </CardTitle>
              <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                {completedCount} of {checklistItems.length} completed
              </p>
            </div>
          </div>
          <button
            onClick={handleDismiss}
            className="p-1 rounded-lg hover:bg-gray-100 transition"
            title="Dismiss"
          >
            <X className="w-5 h-5" style={{ color: 'var(--text-muted)' }} />
          </button>
        </div>
        <Progress value={progress} className="h-2 mt-3" />
      </CardHeader>
      <CardContent className="pt-2">
        <div className="space-y-2">
          {checklistItems.map((item) => {
            const isComplete = checklist[item.checkKey];
            const Icon = item.icon;
            
            return (
              <Link
                key={item.id}
                to={item.link}
                className={`flex items-center gap-3 p-3 rounded-lg transition group ${
                  isComplete 
                    ? 'bg-green-50 border border-green-200' 
                    : 'bg-white border border-gray-200 hover:border-blue-300 hover:shadow-sm'
                }`}
              >
                <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                  isComplete ? 'bg-green-500' : 'bg-gray-100 group-hover:bg-blue-100'
                }`}>
                  {isComplete ? (
                    <CheckCircle2 className="w-5 h-5 text-white" />
                  ) : (
                    <Icon className="w-4 h-4 text-gray-500 group-hover:text-blue-500" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className={`font-medium text-sm ${isComplete ? 'text-green-700 line-through' : 'text-gray-900'}`}>
                    {item.title}
                  </div>
                  {!isComplete && (
                    <div className="text-xs text-gray-500 truncate">
                      {item.description}
                    </div>
                  )}
                </div>
                {!isComplete && (
                  <ChevronRight className="w-4 h-4 text-gray-400 group-hover:text-blue-500" />
                )}
              </Link>
            );
          })}
        </div>

        <div className="mt-4 pt-4 border-t border-gray-200">
          <Link to="/docs/getting-started">
            <Button variant="outline" size="sm" className="w-full">
              View Full Setup Guide
              <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
