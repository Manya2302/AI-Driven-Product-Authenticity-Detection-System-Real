/*
  LANDING PAGE
  For logged-out users. Uses Replit Auth link (/api/login).
*/
import { Link } from "wouter";
import { ShieldCheck, ScanFace, TrendingUp, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function Landing() {
  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Navbar */}
      <nav className="border-b border-white/5 bg-background/50 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-8 w-8 text-primary" />
            <span className="font-display text-xl font-bold tracking-tight bg-gradient-to-r from-white to-white/70 bg-clip-text text-transparent">
              VerifAI
            </span>
          </div>
          <div className="flex items-center gap-4">
            <Button variant="ghost" className="text-muted-foreground hover:text-white hidden sm:flex">
              Features
            </Button>
            <Button variant="ghost" className="text-muted-foreground hover:text-white hidden sm:flex">
              Enterprise
            </Button>
            <a href="/api/login">
              <Button className="bg-primary text-primary-foreground hover:bg-primary/90 font-medium">
                Sign In
              </Button>
            </a>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <main className="flex-1 flex flex-col">
        <section className="relative pt-20 pb-32 overflow-hidden">
          {/* Background Blobs */}
          <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-[128px] pointer-events-none" />
          <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-[128px] pointer-events-none" />

          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 mb-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-sm font-medium text-white/80">AI Model v2.0 Now Live</span>
            </div>

            <h1 className="text-5xl md:text-7xl font-display font-bold text-white tracking-tight mb-6 animate-in fade-in slide-in-from-bottom-8 duration-700">
              Stop Counterfeits <br/>
              <span className="bg-gradient-to-r from-primary to-purple-400 bg-clip-text text-transparent">
                Before They Sell
              </span>
            </h1>

            <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-10 animate-in fade-in slide-in-from-bottom-12 duration-1000">
              Instant authenticity verification for luxury goods, electronics, and collectibles powered by advanced computer vision.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-in fade-in slide-in-from-bottom-16 duration-1000">
              <a href="/api/login">
                <Button size="lg" className="h-14 px-8 text-lg rounded-full bg-white text-background hover:bg-white/90">
                  Start Verifying Free
                </Button>
              </a>
              <Button size="lg" variant="outline" className="h-14 px-8 text-lg rounded-full border-white/10 hover:bg-white/5">
                View Demo
              </Button>
            </div>
          </div>
        </section>

        {/* Features */}
        <section className="py-24 bg-black/20 border-t border-white/5">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid md:grid-cols-3 gap-8">
              {[
                {
                  icon: ScanFace,
                  title: "Visual AI Analysis",
                  desc: "Detects micro-inconsistencies in stitching, logos, and materials invisible to the human eye."
                },
                {
                  icon: TrendingUp,
                  title: "Trend Tracking",
                  desc: "Monitor global counterfeit hotspots and distribution patterns in real-time."
                },
                {
                  icon: CheckCircle,
                  title: "Instant Verification",
                  desc: "Get definitive pass/fail results in seconds with detailed confidence scoring."
                }
              ].map((feature, i) => (
                <div key={i} className="glass-panel p-8 rounded-2xl hover:bg-white/5 transition-colors">
                  <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary mb-6">
                    <feature.icon className="w-6 h-6" />
                  </div>
                  <h3 className="text-xl font-bold text-white mb-3">{feature.title}</h3>
                  <p className="text-muted-foreground leading-relaxed">{feature.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-white/5 py-12 bg-black/40">
        <div className="max-w-7xl mx-auto px-4 text-center text-muted-foreground text-sm">
          <p>© 2024 VerifAI Technologies. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
