import { z } from 'zod';
import { insertProductSchema, insertScanSchema, products, scans } from './schema';

export const errorSchemas = {
  validation: z.object({
    message: z.string(),
    field: z.string().optional(),
  }),
  notFound: z.object({
    message: z.string(),
  }),
  internal: z.object({
    message: z.string(),
  }),
};

export const api = {
  products: {
    list: {
      method: 'GET' as const,
      path: '/api/products',
      responses: {
        200: z.array(z.custom<typeof products.$inferSelect>()),
      },
    },
    get: {
      method: 'GET' as const,
      path: '/api/products/:id',
      responses: {
        200: z.custom<typeof products.$inferSelect>(),
        404: errorSchemas.notFound,
      },
    },
    create: {
      method: 'POST' as const,
      path: '/api/products',
      input: insertProductSchema,
      responses: {
        201: z.custom<typeof products.$inferSelect>(),
        400: errorSchemas.validation,
      },
    },
  },
  scans: {
    list: {
      method: 'GET' as const,
      path: '/api/scans', // For current user
      responses: {
        200: z.array(z.custom<typeof scans.$inferSelect>()),
      },
    },
    get: {
      method: 'GET' as const,
      path: '/api/scans/:id',
      responses: {
        200: z.custom<typeof scans.$inferSelect>(),
        404: errorSchemas.notFound,
      },
    },
    create: {
      method: 'POST' as const,
      path: '/api/scans',
      input: insertScanSchema,
      responses: {
        201: z.custom<typeof scans.$inferSelect>(),
        400: errorSchemas.validation,
      },
    },
  },
  analytics: {
    stats: {
      method: 'GET' as const,
      path: '/api/analytics/stats',
      responses: {
        200: z.object({
          totalScans: z.number(),
          fakeCount: z.number(),
          realCount: z.number(),
          suspiciousCount: z.number(),
        }),
      },
    },
    heatmap: {
      method: 'GET' as const,
      path: '/api/analytics/heatmap',
      responses: {
        200: z.array(z.object({
          lat: z.number(),
          lng: z.number(),
          intensity: z.number(),
          locationName: z.string(),
        })),
      },
    },
  },
};

export function buildUrl(path: string, params?: Record<string, string | number>): string {
  let url = path;
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (url.includes(`:${key}`)) {
        url = url.replace(`:${key}`, String(value));
      }
    });
  }
  return url;
}
