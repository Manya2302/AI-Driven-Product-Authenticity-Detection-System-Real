import { useState } from "react";
import { useProducts, useCreateProduct } from "@/hooks/use-products";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { useToast } from "@/hooks/use-toast";
import { Plus, Package, Loader2 } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";

export default function AdminProducts() {
  const { user } = useAuth();
  const { data: products, isLoading } = useProducts();
  const { mutateAsync: createProduct, isPending } = useCreateProduct();
  const { toast } = useToast();
  const [isOpen, setIsOpen] = useState(false);

  // Form State
  const [formData, setFormData] = useState({
    name: "",
    brand: "",
    category: "",
    description: "",
    referenceImageUrls: [""],
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createProduct({
        ...formData,
        createdBy: user?.id || "admin",
        referenceImageUrls: formData.referenceImageUrls.filter(u => u.length > 0),
        features: {} // AI would extract features here in real app
      });
      
      toast({ title: "Product Created", description: "The product has been added to the database." });
      setIsOpen(false);
      setFormData({
        name: "",
        brand: "",
        category: "",
        description: "",
        referenceImageUrls: [""],
      });
    } catch (error) {
      toast({ 
        title: "Error", 
        description: "Failed to create product.", 
        variant: "destructive" 
      });
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-4 py-10">
        <header className="mb-10 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-display font-bold text-white mb-2">
              Product Registry
            </h1>
            <p className="text-muted-foreground">
              Manage verified products and reference images for AI training.
            </p>
          </div>
          
          <Dialog open={isOpen} onOpenChange={setIsOpen}>
            <DialogTrigger asChild>
              <Button className="gap-2 bg-primary text-primary-foreground hover:bg-primary/90">
                <Plus className="w-4 h-4" />
                Add Product
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-card border-white/10 text-white sm:max-w-lg">
              <DialogHeader>
                <DialogTitle>Add Verified Product</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                <div className="space-y-2">
                  <Label>Product Name</Label>
                  <Input 
                    value={formData.name}
                    onChange={e => setFormData({...formData, name: e.target.value})}
                    placeholder="e.g. Air Jordan 1 High OG"
                    required
                    className="bg-black/20 border-white/10"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Brand</Label>
                    <Input 
                      value={formData.brand}
                      onChange={e => setFormData({...formData, brand: e.target.value})}
                      placeholder="e.g. Nike"
                      required
                      className="bg-black/20 border-white/10"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Category</Label>
                    <Input 
                      value={formData.category}
                      onChange={e => setFormData({...formData, category: e.target.value})}
                      placeholder="e.g. Footwear"
                      required
                      className="bg-black/20 border-white/10"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Description</Label>
                  <Textarea 
                    value={formData.description}
                    onChange={e => setFormData({...formData, description: e.target.value})}
                    placeholder="Key visual identifiers..."
                    className="bg-black/20 border-white/10"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Reference Image URL</Label>
                  <Input 
                    value={formData.referenceImageUrls[0]}
                    onChange={e => setFormData({...formData, referenceImageUrls: [e.target.value]})}
                    placeholder="https://..."
                    required
                    className="bg-black/20 border-white/10"
                  />
                </div>
                <Button type="submit" className="w-full" disabled={isPending}>
                  {isPending ? "Creating..." : "Save Product"}
                </Button>
              </form>
            </DialogContent>
          </Dialog>
        </header>

        {isLoading ? (
          <div className="flex justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {products?.map((product) => (
              <div 
                key={product.id}
                className="glass-panel rounded-xl overflow-hidden group hover:border-primary/50 transition-colors"
              >
                <div className="aspect-[4/3] relative bg-black/40">
                  {product.referenceImageUrls[0] ? (
                    <img 
                      src={product.referenceImageUrls[0]} 
                      alt={product.name}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-muted-foreground">
                      <Package className="w-10 h-10 opacity-20" />
                    </div>
                  )}
                  <div className="absolute top-4 left-4">
                    <span className="bg-black/60 backdrop-blur-md text-white text-xs px-2 py-1 rounded font-medium">
                      {product.brand}
                    </span>
                  </div>
                </div>
                <div className="p-5">
                  <h3 className="text-lg font-bold text-white mb-1">{product.name}</h3>
                  <p className="text-sm text-muted-foreground mb-4">{product.category}</p>
                  <div className="flex items-center justify-between pt-4 border-t border-white/5">
                    <span className="text-xs text-muted-foreground">ID: {product.id}</span>
                    <Button variant="ghost" size="sm" className="h-8 text-primary hover:text-primary">
                      Edit Profile
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
