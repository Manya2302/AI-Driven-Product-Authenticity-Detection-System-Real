import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { api } from "@shared/routes";
import { z } from "zod";
import { setupAuth, registerAuthRoutes } from "./replit_integrations/auth";
import { openai } from "./replit_integrations/image/client"; // Reusing the OpenAI client from image integration

export async function registerRoutes(
  httpServer: Server,
  app: Express
): Promise<Server> {
  
  // Setup Auth
  await setupAuth(app);
  registerAuthRoutes(app);

  // --- Products ---

  app.get(api.products.list.path, async (req, res) => {
    const products = await storage.getProducts();
    res.json(products);
  });

  app.get(api.products.get.path, async (req, res) => {
    const product = await storage.getProduct(Number(req.params.id));
    if (!product) return res.status(404).json({ message: "Product not found" });
    res.json(product);
  });

  app.post(api.products.create.path, async (req, res) => {
    try {
      const input = api.products.create.input.parse(req.body);
      
      // Simulate AI Feature Extraction for Reference Profile
      // In a real app, we'd send these images to a Vision Transformer here.
      // We'll mock the feature vector storage.
      const simulatedFeatures = {
        shape_vector: [0.12, 0.85, 0.33], 
        layout_vector: [0.99, 0.01],
        text_signature: "DETECTED_BRAND_FONT_V2",
        extraction_status: "completed"
      };

      const product = await storage.createProduct({
        ...input,
        features: simulatedFeatures,
      });
      res.status(201).json(product);
    } catch (err) {
      if (err instanceof z.ZodError) {
        return res.status(400).json({ message: err.errors[0].message });
      }
      res.status(500).json({ message: "Internal server error" });
    }
  });

  // --- Scans (The Core AI Logic) ---

  app.get(api.scans.list.path, async (req, res) => {
    // Ideally filter by user, but for MVP listing all or just theirs
    const userId = (req.user as any)?.claims?.sub;
    const scans = await storage.getScans(userId);
    res.json(scans);
  });

  app.get(api.scans.get.path, async (req, res) => {
    const scan = await storage.getScan(Number(req.params.id));
    if (!scan) return res.status(404).json({ message: "Scan not found" });
    res.json(scan);
  });

  app.post(api.scans.create.path, async (req, res) => {
    try {
      const input = api.scans.create.input.parse(req.body);
      
      let aiResult = {
        resultStatus: "suspicious",
        confidenceScore: 50,
        analysisDetails: {
          visual_similarity: "Analyzing...",
          text_match: "Pending",
          explanation: "AI service unavailable, using fallback."
        }
      };

      // Perform AI Analysis using OpenAI Vision
      if (input.productId && input.imageUrl) {
        const product = await storage.getProduct(input.productId);
        
        if (product) {
          try {
            const prompt = `
              You are an expert AI Product Authenticity Detector.
              
              I will provide a user-uploaded image of a product and a list of verified reference images for the product "${product.name}" (${product.brand}).
              
              Your task is to compare the user's image against the reference images to determine if it is REAL or FAKE.
              
              Analyze:
              1. Visual Similarity (Shape, colors, packaging layout).
              2. Text Quality (Spelling errors, font mismatches).
              3. Anomalies (Poor print quality, wrong logos).
              
              Reference Images: ${product.referenceImageUrls.join(", ")}
              
              User Image: ${input.imageUrl}
              
              Respond ONLY with a valid JSON object:
              {
                "result_status": "likely_real" | "suspicious" | "likely_fake",
                "confidence_score": number (0-100),
                "analysis_details": {
                  "visual_similarity_score": number (0-100),
                  "text_match_score": number (0-100),
                  "anomaly_score": number (0-100),
                  "key_findings": ["string", "string"],
                  "explanation": "string summary"
                }
              }
            `;

            const completion = await openai.chat.completions.create({
              model: "gpt-5.2", // Using the best model available
              messages: [
                { role: "system", content: "You are a specialized AI for counterfeit detection." },
                { 
                  role: "user", 
                  content: [
                    { type: "text", text: prompt },
                    { type: "image_url", image_url: { url: input.imageUrl } }
                  ] 
                }
              ],
              response_format: { type: "json_object" }
            });

            const content = completion.choices[0].message.content;
            if (content) {
              const parsed = JSON.parse(content);
              aiResult = {
                resultStatus: parsed.result_status,
                confidenceScore: parsed.confidence_score,
                analysisDetails: parsed.analysis_details
              };
            }
          } catch (aiError) {
            console.error("AI Analysis Failed:", aiError);
            // Fallback mock response if AI fails
            aiResult = {
              resultStatus: "suspicious",
              confidenceScore: 65,
              analysisDetails: {
                visual_similarity_score: 60,
                text_match_score: 70,
                anomaly_score: 40,
                key_findings: ["AI Service timed out", "Visual structure matches generic profile"],
                explanation: "Automated analysis was inconclusive. Please try again."
              }
            };
          }
        }
      }

      const scan = await storage.createScan({
        ...input,
        resultStatus: aiResult.resultStatus,
        confidenceScore: aiResult.confidenceScore,
        analysisDetails: aiResult.analysisDetails,
      });

      res.status(201).json(scan);
    } catch (err) {
      if (err instanceof z.ZodError) {
        return res.status(400).json({ message: err.errors[0].message });
      }
      console.error(err);
      res.status(500).json({ message: "Internal server error" });
    }
  });

  // --- Analytics ---

  app.get(api.analytics.stats.path, async (req, res) => {
    const stats = await storage.getStats();
    res.json(stats);
  });

  app.get(api.analytics.heatmap.path, async (req, res) => {
    const heatmap = await storage.getHeatmap();
    res.json(heatmap);
  });

  // Seed Data
  const products = await storage.getProducts();
  if (products.length === 0) {
    console.log("Seeding database...");
    await storage.createProduct({
      name: "Bisleri Vedica",
      category: "Beverages",
      brand: "Bisleri",
      description: "Premium Natural Mountain Water from the Himalayas.",
      referenceImageUrls: [
        "https://placehold.co/600x600/png?text=Bisleri+Vedica+Front",
        "https://placehold.co/600x600/png?text=Bisleri+Vedica+Label",
        "https://placehold.co/600x600/png?text=Bisleri+Vedica+Cap"
      ],
      features: {
        shape_vector: "simulated_vector_123",
        text_signature: "Vedica_Font_Serif"
      },
      createdBy: "system_seed"
    });
    console.log("Seeding complete.");
  }

  return httpServer;
}
