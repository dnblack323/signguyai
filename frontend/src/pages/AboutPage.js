import { Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { PublicNav, PublicFooter } from '../components/PublicNav';
import {
  Heart, ArrowRight, Users, Target, Lightbulb,
  CheckCircle2, MessageSquare, Rocket, Shield, Award, Zap
} from 'lucide-react';

export default function AboutPage() {
  const values = [
    {
      icon: Heart,
      title: 'Built With Love',
      description: 'Every feature comes from real experience running a sign shop. We build what we actually need.',
    },
    {
      icon: Users,
      title: 'Community First',
      description: 'Founding members shape the product. Your feedback directly influences what we build next.',
    },
    {
      icon: Target,
      title: 'Focused on Signs',
      description: 'We\'re not trying to be everything to everyone. We\'re building the best software for sign shops, period.',
    },
    {
      icon: Lightbulb,
      title: 'Always Improving',
      description: 'New features, AI tools, and improvements ship regularly. Your subscription gets better over time.',
    },
  ];

  const timeline = [
    {
      year: '2020',
      title: 'The Frustration Begins',
      description: 'After years of using sign shop software that didn\'t quite fit, the idea for something better was born.',
    },
    {
      year: '2022',
      title: 'Building the Vision',
      description: 'Started building SignGuy AI for our own shop, focusing on what actually matters day-to-day.',
    },
    {
      year: '2024',
      title: 'AI Integration',
      description: 'Added cutting-edge AI tools that no other sign shop software has, making design and pricing easier.',
    },
    {
      year: '2025',
      title: 'Launch',
      description: 'Opening SignGuy AI to other sign shops who want software that actually understands the business.',
    },
  ];

  return (
    <div className="min-h-screen bg-[#0B0F17] text-white">
      {/* Navigation */}
      <PublicNav />

      {/* Hero */}
      <section className="pt-32 pb-16 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <Badge className="mb-6 bg-[#2F8BFB]/20 text-[#2F8BFB] border-[#2F8BFB]/30 px-4 py-2">
                <Heart className="w-4 h-4 mr-2" />
                Our Story
              </Badge>
              <h1 className="text-4xl sm:text-5xl font-bold mb-6">
                Built by a Sign Shop,<br />
                <span className="text-[#2F8BFB]">For Sign Shops</span>
              </h1>
              <p className="text-xl text-gray-400 mb-6">
                SignGuy AI wasn't built in a Silicon Valley office by people who've never touched a roll of vinyl. 
                It was built in a sign shop, by someone who got tired of software that didn't understand the business.
              </p>
              <p className="text-gray-400 mb-8">
                After years of using software that was either too complicated, too expensive, or just didn't fit how a sign shop actually works, 
                I decided to build something better. Something that actually makes sense for our industry.
              </p>
              <Link to="/register">
                <Button className="bg-[#2F8BFB] hover:bg-[#1E7AF0] text-black font-semibold">
                  Join the Revolution
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </Link>
            </div>
            <div className="relative">
              <div className="bg-gradient-to-br from-[#2F8BFB]/20 to-blue-600/20 rounded-2xl p-8 border border-white/10">
                <div className="text-center">
                  <div className="w-24 h-24 bg-[#2F8BFB]/20 rounded-full flex items-center justify-center mx-auto mb-6">
                    <Zap className="w-12 h-12 text-[#2F8BFB]" />
                  </div>
                  <h3 className="text-2xl font-bold mb-2">One Person. One Vision.</h3>
                  <p className="text-gray-400">
                    No investors. No committees. No bloat.<br />
                    Just software that works.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* The Problem */}
      <section className="py-20 px-4 bg-[#111826]">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-6">The Problem With Sign Shop Software</h2>
          <p className="text-xl text-gray-400 text-center mb-12">
            I tried them all. Here's what I found:
          </p>
          
          <div className="grid md:grid-cols-2 gap-6">
            <Card className="bg-[#0B0F17] border-red-500/30">
              <CardContent className="p-6">
                <h3 className="text-lg font-semibold text-red-400 mb-2">Too Expensive</h3>
                <p className="text-gray-400">
                  $150-300/month for software that still doesn't do everything you need? 
                  Then you're paying extra for features that should be included.
                </p>
              </CardContent>
            </Card>
            <Card className="bg-[#0B0F17] border-red-500/30">
              <CardContent className="p-6">
                <h3 className="text-lg font-semibold text-red-400 mb-2">Built by Committees</h3>
                <p className="text-gray-400">
                  Designed by people who've never run a sign shop. Features that look good in demos 
                  but don't make sense in the real world.
                </p>
              </CardContent>
            </Card>
            <Card className="bg-[#0B0F17] border-red-500/30">
              <CardContent className="p-6">
                <h3 className="text-lg font-semibold text-red-400 mb-2">Outdated Technology</h3>
                <p className="text-gray-400">
                  Software that looks like it was built in 2005. Slow, clunky interfaces that 
                  make simple tasks take forever.
                </p>
              </CardContent>
            </Card>
            <Card className="bg-[#0B0F17] border-red-500/30">
              <CardContent className="p-6">
                <h3 className="text-lg font-semibold text-red-400 mb-2">No Innovation</h3>
                <p className="text-gray-400">
                  The same features for years. No AI, no modern tools, no real improvements. 
                  Just the same old software with minor updates.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* The Solution */}
      <section className="py-20 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold mb-6">So I Built Something Better</h2>
          <p className="text-xl text-gray-400 mb-12">
            SignGuy AI is everything I wished sign shop software could be.
          </p>
          
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {values.map((value, index) => (
              <Card key={index} className="bg-[#111826] border-white/10">
                <CardContent className="p-6 text-center">
                  <div className="w-12 h-12 bg-[#2F8BFB]/20 rounded-xl flex items-center justify-center mx-auto mb-4">
                    <value.icon className="w-6 h-6 text-[#2F8BFB]" />
                  </div>
                  <h3 className="font-semibold text-white mb-2">{value.title}</h3>
                  <p className="text-gray-400 text-sm">{value.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Founder Promise */}
      <section className="py-20 px-4 bg-gradient-to-r from-[#2F8BFB]/10 to-blue-600/10">
        <div className="max-w-4xl mx-auto">
          <Card className="bg-[#0B0F17] border-[#2F8BFB]/30">
            <CardContent className="p-8 md:p-12">
              <div className="flex items-start gap-4 mb-6">
                <div className="w-12 h-12 bg-[#2F8BFB]/20 rounded-xl flex items-center justify-center flex-shrink-0">
                  <MessageSquare className="w-6 h-6 text-[#2F8BFB]" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold mb-2">The Founder Promise</h2>
                  <p className="text-[#2F8BFB]">What you get as a founding member</p>
                </div>
              </div>
              
              <div className="space-y-4 mb-8">
                <div className="flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-[#2F8BFB] mt-1 flex-shrink-0" />
                  <p className="text-gray-300">
                    <strong className="text-white">Your voice matters.</strong> Need a feature? Tell me. 
                    I read every request and build what makes sense for sign shops.
                  </p>
                </div>
                <div className="flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-[#2F8BFB] mt-1 flex-shrink-0" />
                  <p className="text-gray-300">
                    <strong className="text-white">Locked-in pricing.</strong> Founding members keep their 
                    rate forever. As the product grows, your price stays the same.
                  </p>
                </div>
                <div className="flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-[#2F8BFB] mt-1 flex-shrink-0" />
                  <p className="text-gray-300">
                    <strong className="text-white">Direct access.</strong> You're not talking to a support 
                    bot or waiting in a queue. I'm here to help.
                  </p>
                </div>
                <div className="flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-[#2F8BFB] mt-1 flex-shrink-0" />
                  <p className="text-gray-300">
                    <strong className="text-white">Constant improvement.</strong> New features and AI 
                    tools are added regularly. Your subscription keeps getting better.
                  </p>
                </div>
              </div>

              <p className="text-gray-400 italic">
                "This isn't about building a company to sell to investors. It's about building software 
                that actually helps sign shops run better. That's it."
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Timeline */}
      <section className="py-20 px-4">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">Our Journey</h2>
          
          <div className="relative">
            <div className="absolute left-1/2 top-0 bottom-0 w-px bg-white/10 -translate-x-1/2 hidden md:block" />
            
            <div className="space-y-8">
              {timeline.map((item, index) => (
                <div key={index} className={`flex items-center gap-8 ${index % 2 === 1 ? 'md:flex-row-reverse' : ''}`}>
                  <div className={`flex-1 ${index % 2 === 1 ? 'md:text-right' : ''}`}>
                    <Card className="bg-[#111826] border-white/10">
                      <CardContent className="p-6">
                        <div className="text-[#2F8BFB] font-bold mb-2">{item.year}</div>
                        <h3 className="text-lg font-semibold text-white mb-2">{item.title}</h3>
                        <p className="text-gray-400">{item.description}</p>
                      </CardContent>
                    </Card>
                  </div>
                  <div className="hidden md:flex w-4 h-4 bg-[#2F8BFB] rounded-full flex-shrink-0 relative z-10" />
                  <div className="flex-1 hidden md:block" />
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-4 bg-[#111826]">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl sm:text-4xl font-bold mb-6">
            Ready to Join the Sign Shop Revolution?
          </h2>
          <p className="text-xl text-gray-400 mb-8">
            Be part of something built by sign people, for sign people.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/register">
              <Button size="lg" className="bg-[#2F8BFB] hover:bg-[#1E7AF0] text-black font-semibold text-lg px-8 py-6 h-auto">
                Start Your Free Trial
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </Link>
            <Link to="/contact">
              <Button size="lg" variant="outline" className="border-[#2F8BFB]/30 text-[#2F8BFB] text-lg px-8 py-6 h-auto hover:bg-[#2F8BFB]/10">
                Get In Touch
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <PublicFooter />
    </div>
  );
}
