import { pgTable, text, serial, integer, boolean, timestamp, jsonb, varchar } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

// Use existing auth tables
export * from "./models/auth";
export * from "./models/chat";

// --- Products (Reference Profiles) ---
export const products = pgTable("products", {
  id: serial("id").primaryKey(),
  name: text("name").notNull(),
  category: text("category").notNull(),
  brand: text("brand").notNull(),
  description: text("description"),
  
  // Images (URLs)
  referenceImageUrls: text("reference_image_urls").array().notNull(),
  
  // AI-extracted reference features (stored as JSON)
  // Structure: { shape_vector: [], layout_vector: [], text_signature: "", ... }
  features: jsonb("features").notNull().default({}),
  
  createdBy: varchar("created_by").notNull(), // User ID
  createdAt: timestamp("created_at").defaultNow(),
});

// --- Scans (User Uploads) ---
export const scans = pgTable("scans", {
  id: serial("id").primaryKey(),
  userId: varchar("user_id").notNull(), // User ID
  productId: integer("product_id"), // Optional: if user selected a known product
  
  imageUrl: text("image_url").notNull(),
  
  // AI Results
  resultStatus: text("result_status").notNull(), // 'likely_real', 'suspicious', 'likely_fake'
  confidenceScore: integer("confidence_score").notNull(), // 0-100
  
  // Detailed explanation (visual similarity, text mismatch, etc.)
  analysisDetails: jsonb("analysis_details").notNull().default({}),
  
  // Location Data (if fake/suspicious)
  locationData: jsonb("location_data").default({}),
  
  createdAt: timestamp("created_at").defaultNow(),
});

// --- Schemas ---

export const insertProductSchema = createInsertSchema(products).omit({ 
  id: true, 
  createdAt: true 
});

export const insertScanSchema = createInsertSchema(scans).omit({ 
  id: true, 
  createdAt: true 
});

// --- Types ---

export type Product = typeof products.$inferSelect;
export type InsertProduct = z.infer<typeof insertProductSchema>;

export type Scan = typeof scans.$inferSelect;
export type InsertScan = z.infer<typeof insertScanSchema>;

// API Contract Types
export type CreateProductRequest = InsertProduct;
export type CreateScanRequest = InsertScan;

export interface ScanResponse extends Scan {
  product?: Product;
}

// Analytics Types
export interface FakeStats {
  totalScans: number;
  fakeCount: number;
  realCount: number;
  suspiciousCount: number;
}

export interface LocationHeatmapPoint {
  lat: number;
  lng: number;
  intensity: number; // 1-10 based on fake count
  locationName: string;
}
