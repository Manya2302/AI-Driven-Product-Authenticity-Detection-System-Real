import { 
  products, scans, users,
  type Product, type InsertProduct, 
  type Scan, type InsertScan,
  type User, type UpsertUser,
  type FakeStats, type LocationHeatmapPoint
} from "@shared/schema";
import { db } from "./db";
import { eq, desc, sql } from "drizzle-orm";

export interface IStorage {
  // Auth (reusing existing auth storage interface style)
  getUser(id: string): Promise<User | undefined>;
  upsertUser(user: UpsertUser): Promise<User>;
  
  // Products
  getProducts(): Promise<Product[]>;
  getProduct(id: number): Promise<Product | undefined>;
  createProduct(product: InsertProduct): Promise<Product>;
  
  // Scans
  getScans(userId?: string): Promise<Scan[]>;
  getScan(id: number): Promise<Scan | undefined>;
  createScan(scan: InsertScan): Promise<Scan>;
  
  // Analytics
  getStats(): Promise<FakeStats>;
  getHeatmap(): Promise<LocationHeatmapPoint[]>;
}

export class DatabaseStorage implements IStorage {
  // Auth
  async getUser(id: string): Promise<User | undefined> {
    const [user] = await db.select().from(users).where(eq(users.id, id));
    return user;
  }

  async upsertUser(userData: UpsertUser): Promise<User> {
    const [user] = await db
      .insert(users)
      .values(userData)
      .onConflictDoUpdate({
        target: users.id,
        set: { ...userData, updatedAt: new Date() },
      })
      .returning();
    return user;
  }

  // Products
  async getProducts(): Promise<Product[]> {
    return await db.select().from(products).orderBy(desc(products.createdAt));
  }

  async getProduct(id: number): Promise<Product | undefined> {
    const [product] = await db.select().from(products).where(eq(products.id, id));
    return product;
  }

  async createProduct(insertProduct: InsertProduct): Promise<Product> {
    const [product] = await db.insert(products).values(insertProduct).returning();
    return product;
  }

  // Scans
  async getScans(userId?: string): Promise<Scan[]> {
    if (userId) {
      return await db.select().from(scans).where(eq(scans.userId, userId)).orderBy(desc(scans.createdAt));
    }
    return await db.select().from(scans).orderBy(desc(scans.createdAt));
  }

  async getScan(id: number): Promise<Scan | undefined> {
    const [scan] = await db.select().from(scans).where(eq(scans.id, id));
    return scan;
  }

  async createScan(insertScan: InsertScan): Promise<Scan> {
    const [scan] = await db.insert(scans).values(insertScan).returning();
    return scan;
  }

  // Analytics
  async getStats(): Promise<FakeStats> {
    const allScans = await db.select().from(scans);
    return {
      totalScans: allScans.length,
      fakeCount: allScans.filter(s => s.resultStatus === 'likely_fake').length,
      realCount: allScans.filter(s => s.resultStatus === 'likely_real').length,
      suspiciousCount: allScans.filter(s => s.resultStatus === 'suspicious').length,
    };
  }

  async getHeatmap(): Promise<LocationHeatmapPoint[]> {
    const fakeScans = await db.select().from(scans).where(eq(scans.resultStatus, 'likely_fake'));
    
    // Aggregate by location (simple approximation for now)
    const heatmap: LocationHeatmapPoint[] = [];
    
    for (const scan of fakeScans) {
      const loc = scan.locationData as any;
      if (loc && loc.latitude && loc.longitude) {
        heatmap.push({
          lat: loc.latitude,
          lng: loc.longitude,
          intensity: 5, // Default intensity
          locationName: loc.city || "Unknown"
        });
      }
    }
    
    return heatmap;
  }
}

export const storage = new DatabaseStorage();
// Also export as authStorage for the integration to work
export const authStorage = storage;
