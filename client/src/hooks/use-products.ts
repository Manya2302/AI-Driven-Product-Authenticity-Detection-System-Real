import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, buildUrl } from "@shared/routes";
import { products, type CreateProductRequest } from "@shared/schema";
import { z } from "zod";

export function useProducts() {
  return useQuery({
    queryKey: [api.products.list.path],
    queryFn: async () => {
      const res = await fetch(api.products.list.path, { credentials: "include" });
      if (!res.ok) throw new Error("Failed to fetch products");
      return api.products.list.responses[200].parse(await res.json());
    },
  });
}

export function useProduct(id: number) {
  return useQuery({
    queryKey: [api.products.get.path, id],
    queryFn: async () => {
      const url = buildUrl(api.products.get.path, { id });
      const res = await fetch(url, { credentials: "include" });
      if (res.status === 404) return null;
      if (!res.ok) throw new Error("Failed to fetch product");
      return api.products.get.responses[200].parse(await res.json());
    },
    enabled: !!id,
  });
}

export function useCreateProduct() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: CreateProductRequest) => {
      // Ensure arrays are initialized if undefined (though schema usually handles this)
      const payload = { ...data, features: data.features || {} };
      
      const res = await fetch(api.products.create.path, {
        method: api.products.create.method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        credentials: "include",
      });
      
      if (!res.ok) {
        if (res.status === 400) {
          const error = await res.json();
          throw new Error(error.message || "Validation failed");
        }
        throw new Error("Failed to create product");
      }
      return api.products.create.responses[201].parse(await res.json());
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [api.products.list.path] });
    },
  });
}
