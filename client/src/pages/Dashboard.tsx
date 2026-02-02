import { useState } from "react";
import { useProducts } from "@/hooks/use-products";
import { useCreateScan } from "@/hooks/use-scans";
import { ScanUploader } from "@/components/ScanUploader";
import { ResultCard } from "@/components/ResultCard";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useAuth } from "@/hooks/use-auth";
import { useToast } from "@/hooks/use-toast";
import { ArrowRight, Box } from "lucide-react";

export default function Dashboard() {
  const { user } = useAuth();
  const { data: products } = useProducts();
  const { mutateAsync: createScan, isPending } = useCreateScan();
  const { toast } = useToast();
  
  const [selectedProductId, setSelectedProductId] = useState<string>("");
  const [scanResult, setScanResult] = useState<any>(null);

  const handleFileUpload = async (file: File) => {
    // In a real app, upload file to storage and get URL first.
    // Here we'll simulate by reading as base64 for the API
    const reader = new FileReader();
    reader.onload = async (e) => {
      const base64 = e.target?.result as string;
      
      try {
        // Simulate AI analysis delay
        await new Promise(r => setTimeout(r, 2000));
        
        // Mock AI logic based on randomness for demo purposes
        // In reality, backend handles this via the createScan mutation
        const isFake = Math.random() > 0.7;
        const confidence = Math.floor(Math.random() * 30) + 70;
        
        const result = await createScan({
          userId: user?.id || "unknown",
          productId: selectedProductId ? parseInt(selectedProductId) : undefined,
          imageUrl: "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=800&q=80", // Placeholder for actual upload
          resultStatus: isFake ? "likely_fake" : "likely_real",
          confidenceScore: confidence,
          analysisDetails: {
            visualMatch: isFake ? 45 : 92,
            textMatch: isFake ? 60 : 98,
            anomalies: isFake ? ["Incorrect font weight on logo", "Missing serial number"] : [],
            notes: isFake 
              ? "The product shows signs of inconsistencies in the packaging print quality." 
              : "Product matches all known visual signatures of the authentic item."
          },
          locationData: {} // Empty initially
        });

        setScanResult(result);
        toast({
          title: "Analysis Complete",
          description: "The product has been successfully analyzed.",
        });

      } catch (error) {
        toast({
          title: "Analysis Failed",
          description: error instanceof Error ? error.message : "Something went wrong",
          variant: "destructive",
        });
      }
    };
    reader.readAsDataURL(file);
  };

  const handleShareLocation = () => {
    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition((position) => {
        toast({
          title: "Location Shared",
          description: "Thank you for helping us track counterfeit products.",
        });
        // Here you would update the scan with location data
      });
    }
  };

  return (
    <div className="min-h-screen bg-background pb-20">
      <div className="max-w-4xl mx-auto px-4 pt-10">
        <header className="mb-10 text-center">
          <h1 className="text-4xl md:text-5xl font-display font-bold text-white mb-4">
            Verify Authenticity
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Upload a photo of any supported product to instantly check its legitimacy using our advanced computer vision models.
          </p>
        </header>

        <div className="space-y-8">
          {/* Step 1: Select Product */}
          <div className="glass-panel rounded-2xl p-6 md:p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold">1</div>
              <h3 className="text-xl font-semibold text-white">Select Product Category</h3>
            </div>
            
            <div className="flex gap-4">
              <div className="flex-1">
                <Select value={selectedProductId} onValueChange={setSelectedProductId}>
                  <SelectTrigger className="h-12 border-white/10 bg-black/20 text-white">
                    <SelectValue placeholder="Choose a product to verify..." />
                  </SelectTrigger>
                  <SelectContent>
                    {products?.map((p) => (
                      <SelectItem key={p.id} value={p.id.toString()}>
                        {p.brand} - {p.name}
                      </SelectItem>
                    ))}
                    <SelectItem value="other">Other / Unknown</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <Button variant="outline" className="h-12 border-white/10 text-muted-foreground" disabled>
                <Box className="w-4 h-4 mr-2" />
                Browse Catalog
              </Button>
            </div>
          </div>

          {/* Step 2: Upload */}
          <div className={`glass-panel rounded-2xl p-6 md:p-8 transition-opacity duration-300 ${!selectedProductId ? 'opacity-50 pointer-events-none' : ''}`}>
             <div className="flex items-center gap-3 mb-6">
              <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold">2</div>
              <h3 className="text-xl font-semibold text-white">Upload Scan</h3>
            </div>
            
            <ScanUploader 
              onFileSelect={handleFileUpload} 
              isAnalyzing={isPending}
            />
          </div>

          {/* Step 3: Result */}
          {scanResult && (
            <div className="animate-in fade-in slide-in-from-bottom-8 duration-700">
               <div className="flex items-center gap-3 mb-6">
                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold">3</div>
                <h3 className="text-xl font-semibold text-white">Analysis Result</h3>
              </div>
              
              <ResultCard 
                status={scanResult.resultStatus as any}
                confidence={scanResult.confidenceScore}
                details={scanResult.analysisDetails}
                onShareLocation={handleShareLocation}
              />
              
              <div className="mt-8 text-center">
                 <Button 
                    variant="ghost" 
                    className="text-muted-foreground hover:text-white"
                    onClick={() => setScanResult(null)}
                  >
                    Start New Scan
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
