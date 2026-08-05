import { useState } from 'react';
import { Link } from 'react-router-dom';
import { PublicNav, PublicFooter } from '../components/PublicNav';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Checkbox } from '../components/ui/checkbox';
import { LifeBuoy, Mail, MapPin, ArrowRight, Send } from 'lucide-react';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;
const SUPPORT_EMAIL = 'support@signguy-ai.com';
const MAILING_ADDRESS = '413 S Pittsburgh St, Connellsville, PA 15425';
const SMS_DISCLOSURE_VERSION = 'signguy_ai_sms_v1';

export default function SupportPage() {
  const [form, setForm] = useState({
    name: '',
    email: '',
    company: '',
    subject: '',
    message: '',
    phone: '',
    sms_opt_in: false,
  });
  const [sending, setSending] = useState(false);

  const onSubmit = async (e) => {
    e.preventDefault();
    setSending(true);
    try {
      const payload = {
        name: form.name,
        email: form.email,
        company: form.company || null,
        subject: form.subject,
        message: form.message,
        phone: form.phone || null,
        sms_opt_in: !!form.sms_opt_in,
      };
      const res = await fetch(`${API}/api/public/support`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || 'Unable to submit support request');
      toast.success('Support request sent. We will reply soon.');
      setForm({ name: '', email: '', company: '', subject: '', message: '', phone: '', sms_opt_in: false });
    } catch (err) {
      toast.error(err.message || 'Unable to submit support request');
    } finally {
      setSending(false);
    }
  };

  const topics = [
    'Account access and login help',
    'Billing and subscription questions',
    'Platform onboarding and setup guidance',
    'Technical issues and bug reports',
  ];

  return (
    <div className="min-h-screen bg-[#0B0F17] text-white">
      <PublicNav />

      <main className="pt-28 pb-16 px-4" data-testid="support-page">
        <div className="max-w-6xl mx-auto grid lg:grid-cols-5 gap-8">
          <div className="lg:col-span-2 space-y-5">
            <div className="inline-flex items-center gap-2 text-sm px-3 py-1 rounded-full border border-[#2F8BFB]/30 text-[#8bc4ff]">
              <LifeBuoy className="h-4 w-4" />
              Public Support
            </div>
            <h1 className="text-4xl sm:text-5xl font-bold" data-testid="support-page-title">Support</h1>
            <p className="text-slate-300 leading-relaxed" data-testid="support-legal-identity">
              SignGuy AI is operated by SignTists Lab, a sole proprietorship owned by Donnell Nicole Black.
            </p>
            <div className="space-y-3 text-sm">
              <div className="flex items-start gap-2 text-slate-300" data-testid="support-email-row">
                <Mail className="h-4 w-4 mt-0.5 text-[#2F8BFB]" />
                <a href={`mailto:${SUPPORT_EMAIL}`} className="hover:underline">{SUPPORT_EMAIL}</a>
              </div>
              <div className="flex items-start gap-2 text-slate-300" data-testid="support-address-row">
                <MapPin className="h-4 w-4 mt-0.5 text-[#2F8BFB]" />
                <span>{MAILING_ADDRESS}</span>
              </div>
            </div>

            <Card className="bg-[#111826] border-white/10">
              <CardHeader>
                <CardTitle className="text-white text-lg">Common Help Topics</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm text-slate-300" data-testid="support-topics-list">
                  {topics.map((topic) => (
                    <li key={topic} className="flex items-start gap-2">
                      <span className="mt-1 h-1.5 w-1.5 rounded-full bg-[#2F8BFB]" />
                      {topic}
                    </li>
                  ))}
                </ul>
                <Link to="/contact" className="inline-flex items-center gap-1 mt-4 text-[#8bc4ff] hover:underline text-sm" data-testid="support-go-contact-link">
                  Need general inquiries? Visit Contact <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              </CardContent>
            </Card>
          </div>

          <div className="lg:col-span-3">
            <Card className="bg-[#111826] border-white/10">
              <CardHeader>
                <CardTitle className="text-white text-xl">Submit a Support Request</CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={onSubmit} className="space-y-4" data-testid="support-form">
                  <div className="grid sm:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="support-name">Name *</Label>
                      <Input id="support-name" data-testid="support-name-input" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="mt-1 bg-[#0B0F17] border-white/20" />
                    </div>
                    <div>
                      <Label htmlFor="support-email">Email *</Label>
                      <Input id="support-email" type="email" data-testid="support-email-input" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="mt-1 bg-[#0B0F17] border-white/20" />
                    </div>
                  </div>

                  <div className="grid sm:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="support-company">Company</Label>
                      <Input id="support-company" data-testid="support-company-input" value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} className="mt-1 bg-[#0B0F17] border-white/20" />
                    </div>
                    <div>
                      <Label htmlFor="support-phone">Mobile Number (optional)</Label>
                      <Input id="support-phone" data-testid="support-phone-input" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} className="mt-1 bg-[#0B0F17] border-white/20" placeholder="(555) 555-5555" />
                    </div>
                  </div>

                  <div>
                    <Label htmlFor="support-subject">Subject *</Label>
                    <Input id="support-subject" data-testid="support-subject-input" required value={form.subject} onChange={(e) => setForm({ ...form, subject: e.target.value })} className="mt-1 bg-[#0B0F17] border-white/20" />
                  </div>

                  <div>
                    <Label htmlFor="support-message">Message *</Label>
                    <Textarea id="support-message" data-testid="support-message-input" required rows={6} value={form.message} onChange={(e) => setForm({ ...form, message: e.target.value })} className="mt-1 bg-[#0B0F17] border-white/20" />
                  </div>

                  <div className="rounded-lg border border-white/10 p-3 bg-[#0B0F17]" data-testid="support-sms-consent-block">
                    <div className="flex items-start gap-2">
                      <Checkbox
                        id="support-sms-optin"
                        data-testid="support-sms-optin-checkbox"
                        checked={form.sms_opt_in}
                        onCheckedChange={(checked) => setForm({ ...form, sms_opt_in: !!checked })}
                      />
                      <div className="text-xs text-slate-300 leading-relaxed">
                        <Label htmlFor="support-sms-optin" className="cursor-pointer font-medium text-slate-200">
                          By checking this box, you agree to receive SMS/MMS messages from SignGuy AI, operated by SignTists Lab, about your account, platform access, billing, support, and service notifications. Message frequency varies. Message and data rates may apply. Reply STOP to opt out and HELP for help. Consent is not a condition of purchase. View our <Link to="/privacy" className="underline text-[#8bc4ff]">Privacy Policy</Link> and <Link to="/terms" className="underline text-[#8bc4ff]">Terms</Link>.
                        </Label>
                        <p className="text-[11px] text-slate-500 mt-1" data-testid="support-sms-disclosure-version">Disclosure version: {SMS_DISCLOSURE_VERSION}</p>
                      </div>
                    </div>
                  </div>

                  <Button type="submit" disabled={sending} className="w-full bg-[#2F8BFB] hover:bg-[#1E7AF0]" data-testid="support-submit-button">
                    {sending ? 'Sending...' : <>Send Support Request <Send className="h-4 w-4 ml-2" /></>}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>

      <PublicFooter />
    </div>
  );
}
