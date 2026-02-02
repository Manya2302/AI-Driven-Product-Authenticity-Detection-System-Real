import { useScans } from "@/hooks/use-scans";
import { format } from "date-fns";
import { CheckCircle2, XCircle, AlertTriangle, ArrowRight, Loader2 } from "lucide-react";
import { Link } from "wouter";
import { Badge } from "@/components/ui/badge";

export default function ScanHistory() {
  const { data: scans, isLoading } = useScans();

  const getStatusIcon = (status: string) => {
    switch(status) {
      case 'likely_real': return <CheckCircle2 className="w-5 h-5 text-emerald-500" />;
      case 'likely_fake': return <XCircle className="w-5 h-5 text-red-500" />;
      default: return <AlertTriangle className="w-5 h-5 text-amber-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch(status) {
      case 'likely_real': return <Badge variant="outline" className="border-emerald-500/50 text-emerald-500">Authentic</Badge>;
      case 'likely_fake': return <Badge variant="outline" className="border-red-500/50 text-red-500">Counterfeit</Badge>;
      default: return <Badge variant="outline" className="border-amber-500/50 text-amber-500">Suspicious</Badge>;
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-4 py-10">
        <header className="mb-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-display font-bold text-white mb-2">
              Scan History
            </h1>
            <p className="text-muted-foreground">
              Review your past product verifications and their results.
            </p>
          </div>
        </header>

        {isLoading ? (
          <div className="flex justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
          </div>
        ) : !scans?.length ? (
          <div className="glass-panel rounded-2xl p-12 text-center">
            <h3 className="text-xl font-semibold text-white mb-2">No scans yet</h3>
            <p className="text-muted-foreground mb-6">Start by analyzing your first product.</p>
            <Link href="/dashboard" className="text-primary hover:underline">
              Go to Dashboard
            </Link>
          </div>
        ) : (
          <div className="grid gap-4">
            {scans.map((scan) => (
              <div 
                key={scan.id}
                className="glass-panel glass-panel-hover rounded-xl p-4 flex items-center gap-4 group cursor-pointer"
              >
                <div className="h-16 w-16 rounded-lg overflow-hidden bg-black/20 flex-shrink-0">
                  <img 
                    src={scan.imageUrl} 
                    alt="Scan" 
                    className="w-full h-full object-cover"
                  />
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-semibold text-white truncate">
                      Scan #{scan.id}
                    </h3>
                    {getStatusBadge(scan.resultStatus)}
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {scan.createdAt ? format(new Date(scan.createdAt), 'MMM d, yyyy • h:mm a') : 'Unknown Date'}
                  </p>
                </div>

                <div className="hidden md:block text-right mr-4">
                  <div className="text-sm font-medium text-white">{scan.confidenceScore}% Confidence</div>
                  <div className="text-xs text-muted-foreground">AI Analysis Score</div>
                </div>

                <div className="p-2 rounded-full bg-white/5 group-hover:bg-primary group-hover:text-background transition-colors">
                  <ArrowRight className="w-4 h-4" />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
