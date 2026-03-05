import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Button } from "@/shared/components/ui/button";
import { DailyClicksChart, DeviceChart } from "../components/ClickChart";
import { getAnalytics } from "../api/analyticsApi";
import type { LinkAnalytics } from "@/types";
import { formatNumber } from "@/shared/lib/utils";

export function AnalyticsPage() {
  const { linkId } = useParams<{ linkId: string }>();
  const [analytics, setAnalytics] = useState<LinkAnalytics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [days, setDays] = useState(30);

  useEffect(() => {
    if (!linkId) return;
    setIsLoading(true);
    getAnalytics(linkId, days)
      .then(setAnalytics)
      .finally(() => setIsLoading(false));
  }, [linkId, days]);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Back button */}
      <Button variant="ghost" size="sm" asChild>
        <Link to="/dashboard">
          <ArrowLeft className="mr-1 h-4 w-4" />
          Back to dashboard
        </Link>
      </Button>

      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Link Analytics</h1>
        <div className="flex gap-2">
          {[7, 30, 90].map((d) => (
            <Button key={d} size="sm" variant={days === d ? "default" : "outline"} onClick={() => setDays(d)}>
              {d}d
            </Button>
          ))}
        </div>
      </div>

      {isLoading && (
        <div className="flex justify-center py-16">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      )}

      {analytics && !isLoading && (
        <>
          {/* Summary cards */}
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
            <StatCard label="Total Clicks" value={formatNumber(analytics.total_clicks)} />
            <StatCard label={`Clicks (${days}d)`} value={formatNumber(analytics.clicks_in_period)} />
          </div>

          {/* Daily clicks chart */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Daily Clicks</CardTitle>
            </CardHeader>
            <CardContent>
              {analytics.daily_clicks.length > 0 ? (
                <DailyClicksChart data={analytics.daily_clicks} />
              ) : (
                <p className="text-sm text-muted-foreground text-center py-8">No click data for this period.</p>
              )}
            </CardContent>
          </Card>

          <div className="grid gap-4 sm:grid-cols-2">
            {/* Device breakdown */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">By Device</CardTitle>
              </CardHeader>
              <CardContent>
                <DeviceChart data={analytics.by_device} />
              </CardContent>
            </Card>

            {/* Top referrers */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Top Referrers</CardTitle>
              </CardHeader>
              <CardContent>
                {analytics.top_referrers.length === 0 ? (
                  <p className="text-sm text-muted-foreground py-8 text-center">No referrer data.</p>
                ) : (
                  <ul className="space-y-2">
                    {analytics.top_referrers.map((r) => (
                      <li key={r.referrer} className="flex items-center justify-between text-sm">
                        <span className="truncate text-muted-foreground max-w-[160px]" title={r.referrer}>
                          {r.referrer || "Direct"}
                        </span>
                        <span className="font-medium">{formatNumber(r.count)}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <Card>
      <CardContent className="p-5">
        <p className="text-sm text-muted-foreground">{label}</p>
        <p className="text-3xl font-bold mt-1">{value}</p>
      </CardContent>
    </Card>
  );
}
