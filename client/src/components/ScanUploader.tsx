import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, X, ScanSearch, AlertCircle } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";

interface ScanUploaderProps {
  onFileSelect: (file: File) => void;
  isAnalyzing: boolean;
}

export function ScanUploader({ onFileSelect, isAnalyzing }: ScanUploaderProps) {
  const [preview, setPreview] = useState<string | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (file) {
      setPreview(URL.createObjectURL(file));
      onFileSelect(file);
    }
  }, [onFileSelect]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': [] },
    maxFiles: 1,
    disabled: isAnalyzing
  });

  const removeFile = (e: React.MouseEvent) => {
    e.stopPropagation();
    setPreview(null);
  };

  return (
    <div className="w-full">
      <AnimatePresence mode="wait">
        {!preview ? (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            {...getRootProps()}
            className={`
              relative overflow-hidden rounded-2xl border-2 border-dashed
              transition-all duration-300 cursor-pointer group
              min-h-[300px] flex flex-col items-center justify-center p-8
              ${isDragActive 
                ? 'border-primary bg-primary/5' 
                : 'border-white/10 hover:border-primary/50 hover:bg-white/5'
              }
            `}
          >
            <input {...getInputProps()} />
            
            <div className="relative z-10 flex flex-col items-center text-center space-y-4">
              <div className={`
                w-20 h-20 rounded-full flex items-center justify-center
                transition-transform duration-500 group-hover:scale-110
                ${isDragActive ? 'bg-primary text-background' : 'bg-white/5 text-primary'}
              `}>
                <Upload className="w-10 h-10" />
              </div>
              
              <div className="space-y-2">
                <h3 className="text-xl font-display font-semibold text-white">
                  {isDragActive ? "Drop to analyze" : "Upload Product Image"}
                </h3>
                <p className="text-muted-foreground max-w-xs mx-auto">
                  Drag and drop a clear photo of the product, or click to browse files.
                </p>
              </div>

              <div className="flex items-center gap-2 text-xs text-muted-foreground/50 pt-4">
                <AlertCircle className="w-4 h-4" />
                <span>Supports JPG, PNG, WEBP up to 10MB</span>
              </div>
            </div>

            {/* Background decoration */}
            <div className="absolute inset-0 bg-gradient-to-tr from-primary/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
          </motion.div>
        ) : (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="relative rounded-2xl overflow-hidden border border-white/10 bg-black/40"
          >
            <div className="aspect-video w-full relative group">
              <img 
                src={preview} 
                alt="Scan preview" 
                className="w-full h-full object-contain"
              />
              
              {!isAnalyzing && (
                <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                  <Button 
                    variant="destructive" 
                    size="lg"
                    onClick={removeFile}
                    className="gap-2"
                  >
                    <X className="w-4 h-4" />
                    Remove Image
                  </Button>
                </div>
              )}

              {isAnalyzing && (
                <div className="absolute inset-0 bg-black/60 flex flex-col items-center justify-center">
                  <div className="relative w-24 h-24 mb-6">
                    {/* Scanner animation */}
                    <motion.div 
                      className="absolute inset-0 border-t-2 border-primary shadow-[0_0_20px_rgba(var(--primary),0.5)]"
                      animate={{ top: ["0%", "100%", "0%"] }}
                      transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                    />
                    <ScanSearch className="w-full h-full text-white/20" />
                  </div>
                  <h3 className="text-xl font-display font-semibold text-white animate-pulse">
                    Analyzing Authenticity...
                  </h3>
                  <p className="text-sm text-muted-foreground mt-2">
                    Checking visual patterns & text signatures
                  </p>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
