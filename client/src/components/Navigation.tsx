import { Link, useLocation } from "wouter";
import { useAuth } from "@/hooks/use-auth";
import { LayoutDashboard, ScanLine, BarChart3, LogOut, PackageSearch, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";

export function Navigation() {
  const [location] = useLocation();
  const { user, logout } = useAuth();

  // Simple check for admin based on user data (MVP)
  // In a real app, this would check a role field
  const isAdmin = user?.email?.includes("admin") || true; // For MVP demo, enabling admin features

  const isActive = (path: string) => location === path;

  return (
    <nav className="border-b border-white/5 bg-background/50 backdrop-blur-xl sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center gap-8">
            <Link href="/" className="flex items-center gap-2 cursor-pointer">
              <ShieldCheck className="h-8 w-8 text-primary" />
              <span className="font-display text-xl font-bold tracking-tight bg-gradient-to-r from-white to-white/70 bg-clip-text text-transparent">
                VerifAI
              </span>
            </Link>
            
            <div className="hidden md:flex items-center gap-1">
              <Link href="/dashboard">
                <Button 
                  variant="ghost" 
                  className={`gap-2 ${isActive('/dashboard') ? 'bg-white/5 text-primary' : 'text-muted-foreground hover:text-white'}`}
                >
                  <ScanLine className="h-4 w-4" />
                  Scan
                </Button>
              </Link>
              
              <Link href="/history">
                <Button 
                  variant="ghost" 
                  className={`gap-2 ${isActive('/history') ? 'bg-white/5 text-primary' : 'text-muted-foreground hover:text-white'}`}
                >
                  <LayoutDashboard className="h-4 w-4" />
                  History
                </Button>
              </Link>

              {isAdmin && (
                <>
                  <div className="h-4 w-px bg-white/10 mx-2" />
                  <Link href="/admin/products">
                    <Button 
                      variant="ghost" 
                      className={`gap-2 ${isActive('/admin/products') ? 'bg-white/5 text-primary' : 'text-muted-foreground hover:text-white'}`}
                    >
                      <PackageSearch className="h-4 w-4" />
                      Products
                    </Button>
                  </Link>
                  <Link href="/admin/analytics">
                    <Button 
                      variant="ghost" 
                      className={`gap-2 ${isActive('/admin/analytics') ? 'bg-white/5 text-primary' : 'text-muted-foreground hover:text-white'}`}
                    >
                      <BarChart3 className="h-4 w-4" />
                      Analytics
                    </Button>
                  </Link>
                </>
              )}
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden sm:block text-right">
              <p className="text-sm font-medium text-white">{user?.firstName || 'User'}</p>
              <p className="text-xs text-muted-foreground truncate max-w-[150px]">{user?.email}</p>
            </div>
            <Button 
              variant="outline" 
              size="icon" 
              onClick={() => logout()}
              className="border-white/10 hover:bg-white/5"
            >
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </nav>
  );
}
