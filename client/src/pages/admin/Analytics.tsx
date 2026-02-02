import { useAnalyticsStats, useAnalyticsHeatmap } from "@/hooks/use-analytics";
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  PieChart, 
  Pie, 
  Cell 
} from "recharts";
import { Loader2, TrendingUp, AlertOctagon, ShieldCheck, MapPin } from "lucide-react";

const COLORS = ['#10b981', '#f59e0b', '#ef4444']; // Emerald, Amber, Red

export default function Analytics() {
  const { data: stats, isLoading: statsLoading } = useAnalyticsStats();
  const { data: heatmap, isLoading: heatmapLoading } = useAnalyticsHeatmap();

  if (statsLoading || heatmapLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  const pieData = [
    { name: 'Authentic', value: stats?.realCount || 0 },
    { name: 'Suspicious', value: stats?.suspiciousCount || 0 },
    { name: 'Fake', value: stats?.fakeCount || 0 },
  ];

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-4 py-10">
        <header className="mb-10">
          <h1 className="text-3xl font-display font-bold text-white mb-2">
            Global Analytics
          </h1>
          <p className="text-muted-foreground">
            Monitor counterfeit trends and distribution hotspots.
          </p>
        </header>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
          <div className="glass-panel rounded-2xl p-6">
            <div className="flex items-center gap-4 mb-4">
              <div className="p-3 rounded-xl bg-primary/10 text-primary">
                <TrendingUp className="w-6 h-6" />
              </div>
              <h3 className="text-muted-foreground font-medium">Total Scans</h3>
            </div>
            <div className="text-4xl font-display font-bold text-white">
              {stats?.totalScans || 0}
            </div>
          </div>
          
          <div className="glass-panel rounded-2xl p-6">
            <div className="flex items-center gap-4 mb-4">
              <div className="p-3 rounded-xl bg-emerald-500/10 text-emerald-500">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <h3 className="text-muted-foreground font-medium">Authentic</h3>
            </div>
            <div className="text-4xl font-display font-bold text-white">
              {stats?.realCount || 0}
            </div>
          </div>

          <div className="glass-panel rounded-2xl p-6">
            <div className="flex items-center gap-4 mb-4">
              <div className="p-3 rounded-xl bg-red-500/10 text-red-500">
                <AlertOctagon className="w-6 h-6" />
              </div>
              <h3 className="text-muted-foreground font-medium">Confirmed Fakes</h3>
            </div>
            <div className="text-4xl font-display font-bold text-white">
              {stats?.fakeCount || 0}
            </div>
          </div>
          
          <div className="glass-panel rounded-2xl p-6">
             <div className="flex items-center gap-4 mb-4">
              <div className="p-3 rounded-xl bg-purple-500/10 text-purple-500">
                <MapPin className="w-6 h-6" />
              </div>
              <h3 className="text-muted-foreground font-medium">Hotspots</h3>
            </div>
            <div className="text-4xl font-display font-bold text-white">
              {heatmap?.length || 0}
            </div>
          </div>
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-10">
          <div className="glass-panel rounded-2xl p-8">
            <h3 className="text-lg font-bold text-white mb-6">Authenticity Distribution</h3>
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1e293b', borderColor: 'rgba(255,255,255,0.1)', color: '#fff' }}
                    itemStyle={{ color: '#fff' }}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex justify-center gap-6 mt-4">
                {pieData.map((entry, index) => (
                  <div key={index} className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[index] }} />
                    <span className="text-sm text-muted-foreground">{entry.name}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="glass-panel rounded-2xl p-8">
            <h3 className="text-lg font-bold text-white mb-6">Geographic Hotspots</h3>
            <div className="space-y-4 max-h-[300px] overflow-y-auto pr-2 custom-scrollbar">
              {heatmap?.map((point, i) => (
                <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/5">
                  <div className="flex items-center gap-3">
                    <MapPin className="w-4 h-4 text-primary" />
                    <span className="text-white font-medium">{point.locationName}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground">Intensity</span>
                    <div className="flex gap-0.5">
                      {Array.from({ length: 5 }).map((_, idx) => (
                        <div 
                          key={idx} 
                          className={`w-1.5 h-4 rounded-sm ${idx < (point.intensity / 2) ? 'bg-red-500' : 'bg-white/10'}`} 
                        />
                      ))}
                    </div>
                  </div>
                </div>
              ))}
              {!heatmap?.length && (
                <p className="text-center text-muted-foreground py-10">No location data available yet.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
