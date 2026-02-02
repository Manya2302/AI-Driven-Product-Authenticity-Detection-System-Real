import { motion } from "framer-motion";
import { CheckCircle2, AlertTriangle, XCircle, ChevronDown, MapPin } from "lucide-react";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Button } from "@/components/ui/button";

interface AnalysisDetails {
  visualMatch?: number;
  textMatch?: number;
  anomalies?: string[];
  notes?: string;
}

interface ResultCardProps {
  status: 'likely_real' | 'suspicious' | 'likely_fake';
  confidence: number;
  details: AnalysisDetails;
  onShareLocation?: () => void;
}

const statusConfig = {
  likely_real: {
    color: "text-emerald-500",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/20",
    icon: CheckCircle2,
    label: "Authentic Product",
    description: "High confidence match with verified manufacturer profiles."
  },
  suspicious: {
    color: "text-amber-500",
    bg: "bg-amber-500/10",
    border: "border-amber-500/20",
    icon: AlertTriangle,
    label: "Suspicious",
    description: "Several anomalies detected. Requires manual verification."
  },
  likely_fake: {
    color: "text-red-500",
    bg: "bg-red-500/10",
    border: "border-red-500/20",
    icon: XCircle,
    label: "Likely Counterfeit",
    description: "Critical mismatches found in packaging and visual signatures."
  }
};

export function ResultCard({ status, confidence, details, onShareLocation }: ResultCardProps) {
  const config = statusConfig[status];
  const Icon = config.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`rounded-2xl border ${config.border} ${config.bg} overflow-hidden`}
    >
      <div className="p-6 md:p-8">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div className={`p-3 rounded-full bg-background/50 backdrop-blur-sm ${config.color}`}>
              <Icon className="w-8 h-8" />
            </div>
            <div>
              <h2 className={`text-2xl font-display font-bold ${config.color}`}>
                {config.label}
              </h2>
              <p className="text-white/70 mt-1">
                {config.description}
              </p>
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm text-muted-foreground uppercase tracking-wider font-medium">
              Confidence
            </div>
            <div className="text-3xl font-display font-bold text-white">
              {confidence}%
            </div>
          </div>
        </div>

        <div className="mt-8 grid gap-4 md:grid-cols-3">
          <div className="bg-background/40 rounded-xl p-4 border border-white/5">
            <div className="text-sm text-muted-foreground mb-1">Visual Match</div>
            <div className="text-xl font-bold text-white">{details.visualMatch || 0}%</div>
            <div className="w-full bg-white/10 h-1.5 rounded-full mt-2 overflow-hidden">
              <div 
                className="bg-primary h-full rounded-full transition-all duration-1000" 
                style={{ width: `${details.visualMatch || 0}%` }}
              />
            </div>
          </div>
          <div className="bg-background/40 rounded-xl p-4 border border-white/5">
            <div className="text-sm text-muted-foreground mb-1">Text Consistency</div>
            <div className="text-xl font-bold text-white">{details.textMatch || 0}%</div>
            <div className="w-full bg-white/10 h-1.5 rounded-full mt-2 overflow-hidden">
              <div 
                className="bg-primary h-full rounded-full transition-all duration-1000" 
                style={{ width: `${details.textMatch || 0}%` }}
              />
            </div>
          </div>
          <div className="bg-background/40 rounded-xl p-4 border border-white/5">
            <div className="text-sm text-muted-foreground mb-1">Anomalies</div>
            <div className="text-xl font-bold text-white">{details.anomalies?.length || 0} Found</div>
            <div className="w-full bg-white/10 h-1.5 rounded-full mt-2 overflow-hidden">
              <div 
                className={`h-full rounded-full transition-all duration-1000 ${
                  (details.anomalies?.length || 0) > 0 ? 'bg-red-500' : 'bg-emerald-500'
                }`}
                style={{ width: '100%' }}
              />
            </div>
          </div>
        </div>

        <Accordion type="single" collapsible className="mt-6">
          <AccordionItem value="details" className="border-white/10">
            <AccordionTrigger className="text-white hover:text-primary">
              View Detailed Analysis
            </AccordionTrigger>
            <AccordionContent className="text-muted-foreground">
              {details.notes || "No additional notes provided by the AI analysis system."}
              
              {details.anomalies && details.anomalies.length > 0 && (
                <ul className="mt-4 space-y-2">
                  {details.anomalies.map((anomaly, idx) => (
                    <li key={idx} className="flex items-center gap-2 text-red-400">
                      <AlertTriangle className="w-4 h-4" />
                      {anomaly}
                    </li>
                  ))}
                </ul>
              )}
            </AccordionContent>
          </AccordionItem>
        </Accordion>

        {(status === 'likely_fake' || status === 'suspicious') && onShareLocation && (
          <div className="mt-6 pt-6 border-t border-white/10 flex items-center justify-between">
            <div className="text-sm text-muted-foreground">
              Help us track counterfeit distribution by sharing the location of this scan.
            </div>
            <Button 
              variant="outline" 
              onClick={onShareLocation}
              className="gap-2 border-white/10 hover:bg-white/5"
            >
              <MapPin className="w-4 h-4" />
              Report Location
            </Button>
          </div>
        )}
      </div>
    </motion.div>
  );
}
