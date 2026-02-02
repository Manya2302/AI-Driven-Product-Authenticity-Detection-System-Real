# 🔄 Complete System Data Flow

## 1️⃣ ADMIN WORKFLOW: Adding Verified Product

```
┌─────────────────────────────────────────────────────────────────┐
│  ADMIN INTERFACE                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. Login with admin credentials                          │  │
│  │ 2. Navigate to "Add Product"                             │  │
│  │ 3. Fill form:                                            │  │
│  │    - Product Name                                        │  │
│  │    - Category                                            │  │
│  │    - Brand Name                                          │  │
│  │    - Description (optional)                              │  │
│  │ 4. Upload 8 images:                                      │  │
│  │    • Front view                                          │  │
│  │    • Back view                                           │  │
│  │    • Left side                                           │  │
│  │    • Right side                                          │  │
│  │    • Top view                                            │  │
│  │    • Bottom view                                         │  │
│  │    • Label close-up                                      │  │
│  │    • Cap/seal image                                      │  │
│  │ 5. Click "Add Product"                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  BACKEND API (POST /api/admin/products)                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. Verify JWT token → Check admin role                  │  │
│  │ 2. Validate inputs (name, category, images)             │  │
│  │ 3. Generate unique product_id                           │  │
│  │ 4. Save images to uploads/products/{product_id}/        │  │
│  │ 5. Send images to AI pipeline                           │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  AI FEATURE EXTRACTION PIPELINE                                 │
│                                                                  │
│  FOR EACH IMAGE (8 times):                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Step 1: PREPROCESSING                                    │  │
│  │   • Load image                                           │  │
│  │   • Denoise (Non-Local Means)                           │  │
│  │   • Enhance contrast (CLAHE)                            │  │
│  │   • Enhance edges (Bilateral filter)                    │  │
│  │   • Resize to 224x224                                   │  │
│  │   • Normalize (ImageNet µ, σ)                           │  │
│  │   Output: Preprocessed tensor                           │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ Step 2: VISION TRANSFORMER                              │  │
│  │   • Pass through ViT (google/vit-base-patch16-224)     │  │
│  │   • Extract CLS token embedding (768-dim)              │  │
│  │   • Extract multi-scale features (layers 3,6,9,12)     │  │
│  │   • Compute attention maps                              │  │
│  │   Output: Deep feature embeddings                       │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ Step 3: COLOR & EDGE ANALYSIS                           │  │
│  │   • Extract dominant colors (K-means)                   │  │
│  │   • Compute color histograms (RGB)                      │  │
│  │   • Canny edge detection                                │  │
│  │   • Histogram of Oriented Gradients (HOG)              │  │
│  │   Output: Color and edge features                       │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ Step 4: OCR TEXT EXTRACTION (for label/cap images)     │  │
│  │   • EasyOCR text detection                              │  │
│  │   • Extract brand name                                  │  │
│  │   • Normalize text                                      │  │
│  │   Output: Extracted text data                           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  CONSOLIDATE ALL FEATURES:                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ {                                                        │  │
│  │   "front": {vit_features, color_features, edge_features}│  │
│  │   "back": {...},                                        │  │
│  │   "left": {...},                                        │  │
│  │   ... (all 8 angles)                                    │  │
│  │   "brand_text": "Extracted brand name",                │  │
│  │   "model_version": "1.0.0"                             │  │
│  │ }                                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  DATABASE STORAGE                                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ COLLECTION: products                                     │  │
│  │ {                                                        │  │
│  │   product_id: "uuid",                                   │  │
│  │   product_name: "Bisleri Water",                       │  │
│  │   category: "beverages",                                │  │
│  │   brand_name: "Bisleri",                               │  │
│  │   images: [{type: "front", path: "..."}],              │  │
│  │   added_by: "admin@email.com",                         │  │
│  │   created_at: ISODate(),                               │  │
│  │   is_active: true                                       │  │
│  │ }                                                        │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ COLLECTION: product_features                            │  │
│  │ {                                                        │  │
│  │   product_id: "uuid",                                   │  │
│  │   visual_features: {                                    │  │
│  │     "front": {vit_features: [768 floats], ...},       │  │
│  │     "back": {...}, ...                                  │  │
│  │   },                                                     │  │
│  │   extracted_texts: {...},                              │  │
│  │   dominant_colors: {...},                              │  │
│  │   created_at: ISODate()                                │  │
│  │ }                                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    [Product Ready for Comparison]

═══════════════════════════════════════════════════════════════════

## 2️⃣ USER WORKFLOW: Scanning Product for Authenticity

```
┌─────────────────────────────────────────────────────────────────┐
│  USER INTERFACE                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. Login / Signup                                        │  │
│  │ 2. Navigate to "Scan Product"                           │  │
│  │ 3. Select product from dropdown (e.g., "Bisleri Water")│  │
│  │ 4. Upload product image from phone/camera               │  │
│  │ 5. Click "Analyze"                                      │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  BACKEND API (POST /api/analysis/scan)                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. Verify JWT token → Get user_id                       │  │
│  │ 2. Validate product_id exists                           │  │
│  │ 3. Validate uploaded image                              │  │
│  │ 4. Generate scan_id                                     │  │
│  │ 5. Save image to uploads/scans/{scan_id}/              │  │
│  │ 6. Create scan record (status: PROCESSING)             │  │
│  │ 7. Fetch reference features from database              │  │
│  │ 8. Send to Decision Engine                             │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  AI ANALYSIS PIPELINE - DECISION ENGINE                         │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ STEP 1: PREPROCESSING (same as admin flow)              │  │
│  │   Output: Preprocessed query image tensor               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ STEP 2: FEATURE EXTRACTION                              │  │
│  │   • Vision Transformer embeddings (768-dim)            │  │
│  │   • Color features                                      │  │
│  │   • Edge features                                       │  │
│  │   Output: Query feature set                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ STEP 3: VISUAL SIMILARITY (Siamese Network)            │  │
│  │   • For each reference angle:                          │  │
│  │     - Pass query features through Siamese Network     │  │
│  │     - Pass reference features through Siamese Network │  │
│  │     - Compute cosine similarity                        │  │
│  │   • Take best 3 matches                                │  │
│  │   • Average for overall similarity                     │  │
│  │   Output: Visual Similarity Score (0-1)               │  │
│  │   Example: 0.85 (85% similar)                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ STEP 4: TEXT VALIDATION (OCR + Fuzzy Matching)         │  │
│  │   • Extract text using EasyOCR                         │  │
│  │   • Normalize extracted brand name                     │  │
│  │   • Compare with reference brand:                      │  │
│  │     - Levenshtein distance                            │  │
│  │     - Fuzzy string matching (FuzzyWuzzy)              │  │
│  │     - Phonetic similarity (Soundex)                   │  │
│  │     - Character substitution check (0→O, 1→I, etc.)   │  │
│  │   • Check spelling/grammar issues                      │  │
│  │   Output: Text Validation Score (0-1)                 │  │
│  │   Example: 0.75 (75% match, minor misspelling)        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ STEP 5: ANOMALY DETECTION (Autoencoder)                │  │
│  │   • Pass image through trained autoencoder             │  │
│  │   • Reconstruct image                                  │  │
│  │   • Compute reconstruction error (MSE + SSIM)          │  │
│  │   • Detect localized anomalies                         │  │
│  │   • Identify suspicious regions                        │  │
│  │   Output: Anomaly Score (0-1, inverted for scoring)   │  │
│  │   Example: 0.30 anomaly → 0.70 authenticity           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ STEP 6: PATTERN CONSISTENCY                             │  │
│  │   • Compare color histograms                           │  │
│  │   • Compare edge patterns (HOG)                        │  │
│  │   • Overall consistency check                          │  │
│  │   Output: Pattern Score (0-1)                          │  │
│  │   Example: 0.82 (82% consistent)                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ STEP 7: WEIGHTED DECISION ENGINE                        │  │
│  │                                                          │  │
│  │   Final Score = (                                       │  │
│  │     Visual Similarity × 0.40 +                         │  │
│  │     Text Validation × 0.30 +                           │  │
│  │     Anomaly Score × 0.20 +                             │  │
│  │     Pattern Score × 0.10                               │  │
│  │   )                                                      │  │
│  │                                                          │  │
│  │   Example Calculation:                                  │  │
│  │   = 0.85 × 0.40 + 0.75 × 0.30 + 0.70 × 0.20 + 0.82 × 0.10 │
│  │   = 0.34 + 0.225 + 0.14 + 0.082                       │  │
│  │   = 0.787                                              │  │
│  │                                                          │  │
│  │   Classification:                                       │  │
│  │   IF score >= 0.75: "LIKELY REAL"                     │  │
│  │   ELIF score >= 0.40: "SUSPICIOUS"                    │  │
│  │   ELSE: "LIKELY FAKE"                                 │  │
│  │                                                          │  │
│  │   Result: LIKELY REAL (78.7% confidence)              │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ STEP 8: EXPLAINABILITY (Grad-CAM + Text Generation)    │  │
│  │   • Generate Grad-CAM heatmap (if suspicious/fake)    │  │
│  │   • Identify suspicious regions                        │  │
│  │   • Generate human-readable explanations:              │  │
│  │     - "Visual appearance closely matches (85%)"       │  │
│  │     - "Brand text shows minor discrepancy (75%)"      │  │
│  │     - "Product features align with authentic (70%)"   │  │
│  │   • Generate recommendations                           │  │
│  │   Output: Complete explanation package                │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  DATABASE STORAGE                                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ COLLECTION: scans                                        │  │
│  │ {                                                        │  │
│  │   scan_id: "uuid",                                      │  │
│  │   user_id: "user@email.com",                           │  │
│  │   product_id: "uuid",                                   │  │
│  │   image_path: "scans/uuid/uploaded.jpg",              │  │
│  │   status: "completed",                                  │  │
│  │   timestamp: ISODate()                                 │  │
│  │ }                                                        │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ COLLECTION: scan_results                                │  │
│  │ {                                                        │  │
│  │   scan_id: "uuid",                                      │  │
│  │   classification: "likely_real",                       │  │
│  │   confidence_score: 0.787,                             │  │
│  │   visual_similarity_score: 0.85,                       │  │
│  │   text_validation_score: 0.75,                         │  │
│  │   anomaly_score: 0.70,                                 │  │
│  │   pattern_consistency_score: 0.82,                     │  │
│  │   explanations: ["...", "...", "..."],                 │  │
│  │   suspicious_regions: [...],                           │  │
│  │   extracted_text: "Bisleri",                           │  │
│  │   text_issues: ["Minor spelling variation"],          │  │
│  │   analysis_timestamp: ISODate(),                       │  │
│  │   processing_time_seconds: 2.34                        │  │
│  │ }                                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  RESPONSE TO USER                                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ {                                                        │  │
│  │   "scan_id": "uuid",                                    │  │
│  │   "product_name": "Bisleri Water",                     │  │
│  │   "classification": "likely_real",                     │  │
│  │   "confidence_score": 0.787,                           │  │
│  │                                                          │  │
│  │   "verdict": "Based on comprehensive AI analysis,      │  │
│  │              this product is LIKELY AUTHENTIC          │  │
│  │              (confidence: 78.7%)",                      │  │
│  │                                                          │  │
│  │   "key_findings": [                                     │  │
│  │     "✓ Visual appearance closely matches (85%)",       │  │
│  │     "⚠ Brand text shows minor discrepancy (75%)",     │  │
│  │     "✓ Product features align with authentic (70%)",   │  │
│  │     "✓ Consistent patterns detected (82%)"            │  │
│  │   ],                                                     │  │
│  │                                                          │  │
│  │   "recommendations": [                                  │  │
│  │     "Product passed multiple authenticity checks",     │  │
│  │     "Minor text variation detected - verify with       │  │
│  │      official product if concerned"                     │  │
│  │   ],                                                     │  │
│  │                                                          │  │
│  │   "visual_similarity": 0.85,                           │  │
│  │   "text_validation": 0.75,                             │  │
│  │   "anomaly_detection": 0.70,                           │  │
│  │   "pattern_consistency": 0.82,                         │  │
│  │   "analyzed_at": "2026-02-02T10:30:45Z"              │  │
│  │ }                                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  USER INTERFACE - RESULTS DISPLAY                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  │  │
│  │  ┃  🟢 LIKELY AUTHENTIC                              ┃  │  │
│  │  ┃  Confidence: 78.7%                                 ┃  │  │
│  │  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  │  │
│  │                                                          │  │
│  │  Detailed Analysis:                                     │  │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │  │
│  │  Visual Similarity:   ████████████████░░ 85%          │  │
│  │  Text Validation:     ███████████████░░░ 75%          │  │
│  │  Anomaly Detection:   ██████████████░░░░ 70%          │  │
│  │  Pattern Match:       ████████████████░░ 82%          │  │
│  │                                                          │  │
│  │  Key Findings:                                          │  │
│  │  • ✓ Visual appearance closely matches (85%)           │  │
│  │  • ⚠ Brand text shows minor discrepancy (75%)         │  │
│  │  • ✓ Product features align with authentic (70%)      │  │
│  │  • ✓ Consistent patterns detected (82%)               │  │
│  │                                                          │  │
│  │  Recommendations:                                       │  │
│  │  • Product passed multiple authenticity checks         │  │
│  │  • Minor text variation - verify if concerned          │  │
│  │                                                          │  │
│  │  [View Full Report] [Scan Another] [Report Issue]     │  │
│  │                                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════

## 3️⃣ IF PRODUCT IS FAKE: Location Sharing Flow

```
User sees "LIKELY FAKE" result
    ↓
System prompts: "Help track fake products by sharing location?"
    ↓
User clicks "Share Location" and provides consent
    ↓
Frontend sends: POST /api/analysis/location/share
{
  scan_id: "uuid",
  country: "India",
  state: "Maharashtra",
  city: "Mumbai",
  district: "Andheri",
  consent: true
}
    ↓
Backend saves to fake_locations collection (anonymized)
    ↓
Admin can view on heatmap: Location-based distribution of fakes
```

---

**Complete Flow Duration**: 
- Admin product upload: ~30 seconds
- User scan analysis: < 3 seconds
- Real-time feedback throughout

**System Throughput**: 100+ concurrent users supported
