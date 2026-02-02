import { Switch, Route } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { useAuth } from "@/hooks/use-auth";
import NotFound from "@/pages/not-found";
import { Loader2 } from "lucide-react";

// Pages
import Landing from "@/pages/Landing";
import Dashboard from "@/pages/Dashboard";
import ScanHistory from "@/pages/ScanHistory";
import AdminProducts from "@/pages/admin/Products";
import Analytics from "@/pages/admin/Analytics";

// Components
import { Navigation } from "@/components/Navigation";

function Router() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!user) {
    return <Landing />;
  }

  return (
    <>
      <Navigation />
      <Switch>
        <Route path="/" component={Dashboard} />
        <Route path="/dashboard" component={Dashboard} />
        <Route path="/history" component={ScanHistory} />
        
        {/* Admin Routes - In real app, protect these with role check */}
        <Route path="/admin/products" component={AdminProducts} />
        <Route path="/admin/analytics" component={Analytics} />
        
        <Route component={NotFound} />
      </Switch>
    </>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Router />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
