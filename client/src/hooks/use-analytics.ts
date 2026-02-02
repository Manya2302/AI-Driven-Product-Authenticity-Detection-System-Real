import { useQuery } from "@tanstack/react-query";
import { api } from "@shared/routes";

export function useAnalyticsStats() {
  return useQuery({
    queryKey: [api.analytics.stats.path],
    queryFn: async () => {
      const res = await fetch(api.analytics.stats.path, { credentials: "include" });
      if (!res.ok) throw new Error("Failed to fetch analytics stats");
      return api.analytics.stats.responses[200].parse(await res.json());
    },
  });
}

export function useAnalyticsHeatmap() {
  return useQuery({
    queryKey: [api.analytics.heatmap.path],
    queryFn: async () => {
      const res = await fetch(api.analytics.heatmap.path, { credentials: "include" });
      if (!res.ok) throw new Error("Failed to fetch analytics heatmap");
      return api.analytics.heatmap.responses[200].parse(await res.json());
    },
  });
}
