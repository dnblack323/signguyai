import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { PublicNav, PublicFooter } from '../components/PublicNav';
import {
  Mail, Phone, MessageSquare, ArrowRight,
  Send, Clock, CheckCircle2, MapPin
} from 'lucide-react';
import { toast } from 'sonner';
import { Checkbox } from '../components/ui/checkbox';

const API = process.env.REACT_APP_BACKEND_URL;
const SUPPORT_EMAIL = 'support@signguy-ai.com';
const MAILING_ADDRESS = '413 S Pittsburgh St, Connellsville, PA 15425';
const SMS_DISCLOSURE_VERSION = 'signguy_ai_sms_v1';

export default function ContactPage() {
  if (typeof document !== 'undefined') {
    document.title = 'Contact SignGuy AI | Operated by SignTists Lab';
  }
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    company: '',
    phone: '',
    sms_opt_in: false,
    subject: '',
    message: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    try {
      const payload = {
        name: formData.name,
        email: formData.email,
        company: formData.company || null,
        phone: formData.phone || null,
        sms_opt_in: !!formData.sms_opt_in,
        subject: formData.subject,
        message: formData.message,
      };
      const response = await fetch(`${API}/api/public/contact`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || 'Unable to send message');
      setSubmitted(true);
      toast.success('Message sent! We\'ll get back to you soon.');
    } catch (err) {
      toast.error(err.message || 'Unable to send message');
    } finally {
      setIsSubmitting(false);
    }
  };

  const contactMethods = [
    {
      icon: Mail,
      title: 'Email',
      description: 'Send us an email anytime',
      value: SUPPORT_EMAIL,
      action: `mailto:${SUPPORT_EMAIL}`,
    },
    {
      icon: MapPin,
      title: 'Mailing Address',
      description: 'Business mailing address',
      value: MAILING_ADDRESS,
      action: null,
    },
    {
      icon: MessageSquare,
      title: 'Live Chat',
      description: 'Chat with us during business hours',
      value: 'Available 9am-5pm EST',
      action: null,
    },
    {
      icon: Clock,
      title: 'Response Time',
      description: 'We typically respond within',
      value: '24 hours or less',
      action: null,
    },
  ];

  const faqs = [
    {
      question: 'How do I get started?',
      answer: 'Sign up for a free trial - no credit card required. You\'ll have full access to explore all features.',
    },
    {
      question: 'Can I import my existing data?',
      answer: 'Yes! We support CSV imports for customers and can help migrate from other systems.',
    },
    {
      question: 'What if I need help setting up?',
      answer: 'We offer onboarding assistance for all plans. Just reach out and we\'ll help you get started.',
    },
  ];

  return (
    <div className="min-h-screen bg-[#0B0F17] text-white">
      {/* Navigation */}
      <PublicNav />

      {/* Hero */}
      <section className="pt-32 pb-12 px-4">
        <div className="max-w-7xl mx-auto text-center">
          <Badge className="mb-6 bg-[#2F8BFB]/20 text-[#2F8BFB] border-[#2F8BFB]/30 px-4 py-2">
            <MessageSquare className="w-4 h-4 mr-2" />
            Get In Touch
          </Badge>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold mb-6">
            We&apos;d Love to <span className="text-[#2F8BFB]">Hear From You</span>
          </h1>
          <p className="text-xl text-gray-400 max-w-3xl mx-auto">
            Have a question, feature request, or just want to say hi? 
            We&apos;re real people who actually respond.
          </p>
          <p className="text-sm text-gray-400 max-w-3xl mx-auto mt-4" data-testid="contact-identity-text">
            SignGuy AI is operated by SignTists Lab, a sole proprietorship owned by Donnell Nicole Black.
          </p>
        </div>
      </section>

      {/* Contact Methods */}
      <section className="px-4 pb-12">
        <div className="max-w-5xl mx-auto">
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {contactMethods.map((method, index) => (
              <Card key={index} className="bg-[#111826] border-white/10">
                <CardContent className="p-6 text-center">
                  <div className="w-12 h-12 bg-[#2F8BFB]/20 rounded-xl flex items-center justify-center mx-auto mb-4">
                    <method.icon className="w-6 h-6 text-[#2F8BFB]" />
                  </div>
                  <h3 className="font-semibold text-white mb-1">{method.title}</h3>
                  <p className="text-gray-500 text-sm mb-2">{method.description}</p>
                  {method.action ? (
                    <a href={method.action} className="text-[#2F8BFB] hover:underline">
                      {method.value}
                    </a>
                  ) : (
                    <span className="text-[#2F8BFB]">{method.value}</span>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Contact Form */}
      <section className="px-4 pb-20">
        <div className="max-w-5xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-12">
            <div>
              <h2 className="text-2xl font-bold mb-6">Send Us a Message</h2>
              
              {submitted ? (
                <Card className="bg-[#111826] text-white border-green-500/30">
                  <CardContent className="p-8 text-center">
                    <div className="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                      <CheckCircle2 className="w-8 h-8 text-green-400" />
                    </div>
                    <h3 className="text-xl font-bold text-white mb-2">Message Sent!</h3>
                    <p className="text-gray-400 mb-6">
                      Thanks for reaching out. We&apos;ll get back to you within 24 hours.
                    </p>
                    <Button 
                      variant="outline" 
                      onClick={() => {
                        setSubmitted(false);
                        setFormData({ name: '', email: '', company: '', phone: '', sms_opt_in: false, subject: '', message: '' });
                      }}
                      className="border-white/20 !text-white hover:bg-white/10 hover:!text-white bg-transparent"
                    >
                      Send Another Message
                    </Button>
                  </CardContent>
                </Card>
              ) : (
                <Card className="bg-[#111826] text-white border-white/10">
                  <CardContent className="p-6">
                    <form onSubmit={handleSubmit} className="space-y-6">
                      <div className="grid sm:grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label htmlFor="name">Your Name *</Label>
                          <Input
                            id="name"
                            required
                            value={formData.name}
                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                            placeholder="John Smith"
                            className="bg-[#0B0F17] border-white/20"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="email">Email Address *</Label>
                          <Input
                            id="email"
                            type="email"
                            required
                            value={formData.email}
                            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                            placeholder="john@signshop.com"
                            className="bg-[#0B0F17] border-white/20"
                          />
                        </div>
                      </div>
                      
                      <div className="grid sm:grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label htmlFor="company">Company Name</Label>
                          <Input
                            id="company"
                            value={formData.company}
                            onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                            placeholder="Your Sign Shop"
                            className="bg-[#0B0F17] border-white/20"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="phone">Mobile Number (optional)</Label>
                          <Input
                            id="phone"
                            data-testid="contact-phone-input"
                            value={formData.phone}
                            onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                            placeholder="(555) 555-5555"
                            className="bg-[#0B0F17] border-white/20"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="subject">Subject *</Label>
                          <Input
                            id="subject"
                            required
                            value={formData.subject}
                            onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                            placeholder="Question about..."
                            className="bg-[#0B0F17] border-white/20"
                          />
                        </div>
                      </div>
                      
                      <div className="space-y-2">
                        <Label htmlFor="message">Message *</Label>
                        <Textarea
                          id="message"
                          required
                          rows={6}
                          value={formData.message}
                          onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                          placeholder="Tell us what's on your mind..."
                          className="bg-[#0B0F17] border-white/20 resize-none"
                        />
                      </div>

                      <div className="rounded-lg border border-white/10 p-3 bg-[#0B0F17]" data-testid="contact-sms-consent-block">
                        <div className="flex items-start gap-2">
                          <Checkbox
                            id="contact-sms-optin"
                            data-testid="contact-sms-optin-checkbox"
                            checked={formData.sms_opt_in}
                            onCheckedChange={(checked) => setFormData({ ...formData, sms_opt_in: !!checked })}
                          />
                          <div className="text-xs text-slate-300 leading-relaxed">
                            <Label htmlFor="contact-sms-optin" className="cursor-pointer font-medium text-slate-200">
                              By checking this box, you agree to receive SMS/MMS messages from SignGuy AI, operated by SignTists Lab, about your account, platform access, billing, support, and service notifications. Message frequency varies. Message and data rates may apply. Reply STOP to opt out and HELP for help. Consent is not a condition of purchase. View our <Link to="/privacy" className="underline text-[#8bc4ff]">Privacy Policy</Link> and <Link to="/terms" className="underline text-[#8bc4ff]">Terms</Link>.
                            </Label>
                            <p className="text-[11px] text-slate-500 mt-1" data-testid="contact-sms-disclosure-version">Disclosure version: {SMS_DISCLOSURE_VERSION}</p>
                          </div>
                        </div>
                      </div>
                      
                      <Button 
                        type="submit" 
                        className="w-full bg-[#2F8BFB] hover:bg-[#1E7AF0] text-black font-semibold"
                        disabled={isSubmitting}
                      >
                        {isSubmitting ? (
                          'Sending...'
                        ) : (
                          <>
                            Send Message
                            <Send className="w-4 h-4 ml-2" />
                          </>
                        )}
                      </Button>
                    </form>
                  </CardContent>
                </Card>
              )}
            </div>
            
            <div>
              <h2 className="text-2xl font-bold mb-6">Common Questions</h2>
              <div className="space-y-4">
                {faqs.map((faq, index) => (
                  <Card key={index} className="bg-[#111826] border-white/10">
                    <CardContent className="p-6">
                      <h3 className="font-semibold text-white mb-2">{faq.question}</h3>
                      <p className="text-gray-400">{faq.answer}</p>
                    </CardContent>
                  </Card>
                ))}
              </div>
              
              <Card className="bg-gradient-to-r from-[#2F8BFB]/10 to-blue-600/10 text-white border-[#2F8BFB]/30 mt-6">
                <CardContent className="p-6">
                  <h3 className="font-semibold text-white mb-2">Feature Request?</h3>
                  <p className="text-gray-400 mb-4">
                    As a founding member, your feature requests get priority attention. 
                    We actually build what our users need.
                  </p>
                  <p className="text-[#2F8BFB] text-sm">
                    Just mention &quot;Feature Request&quot; in your message subject.
                  </p>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-4 bg-[#111826]">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl sm:text-4xl font-bold mb-6">
            Ready to Get Started?
          </h2>
          <p className="text-xl text-gray-400 mb-8">
            Skip the form and jump right in with a free trial.
          </p>
          <Link to="/login">
            <Button size="lg" className="bg-[#2F8BFB] hover:bg-[#1E7AF0] text-white font-semibold text-lg px-8 py-6 h-auto">
              Start Your Free Trial
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <PublicFooter />
    </div>
  );
}
