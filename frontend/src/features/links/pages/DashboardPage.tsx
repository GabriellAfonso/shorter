import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Link2, MousePointerClick, TrendingUp } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useAuthStore } from "@/features/auth/store/authStore";
import { useLinksStore } from "../store/linksStore";
import { CreateLinkForm } from "../components/CreateLinkForm";
import { LinkCard } from "../components/LinkCard";
import { Card, CardContent } from "@/shared/components/ui/card";
import { Button } from "@/shared/components/ui/button";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { formatNumber } from "@/shared/lib/utils";

function StatCard({
  label,
  value,
  icon: Icon,
  isLoading,
}: {
  label: string;
  value: string;
  icon: React.ElementType;
  isLoading: boolean;
}) {
  return (
    <Card>
      <CardContent className="p-5 flex items-center gap-4">
        <div className="p-2 rounded-md bg-primary/10">
          <Icon className="h-5 w-5 text-primary" />
        </div>
        <div>
          <p className="text-xs text-muted-foreground uppercase tracking-wide">{label}</p>
          {isLoading ? (
            <Skeleton className="h-7 w-16 mt-1" />
          ) : (
            <p className="text-2xl font-bold">{value}</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export function DashboardPage() {
  const { t } = useTranslation();
  const { user } = useAuthStore();
  const { links, pagination, stats, isLoading, fetchLinks } = useLinksStore();
  const [justLoggedIn] = useState(() => sessionStorage.getItem("just_logged_in") === "1");
  useEffect(() => {
    sessionStorage.removeItem("just_logged_in");
  }, []);
  useEffect(() => {
    fetchLinks(1);
  }, [fetchLinks]);

  const recentLinks = links.slice(0, 5);

  return (
    <div className="space-y-8 max-w-3xl mx-auto">
      {/* Welcome header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">
          {justLoggedIn && user?.first_name
            ? t("dashboard.welcomeBack", { name: user.first_name })
            : t("dashboard.title")}
        </h1>
        <p className="text-muted-foreground mt-1">{t("dashboard.overview")}</p>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        <StatCard
          label={t("dashboard.totalLinks")}
          value={formatNumber(pagination?.count ?? links.length)}
          icon={Link2}
          isLoading={isLoading}
        />
        <StatCard
          label={t("dashboard.activeLinks")}
          value={formatNumber(stats?.active_count ?? 0)}
          icon={TrendingUp}
          isLoading={isLoading}
        />
        <StatCard
          label={t("dashboard.totalClicks")}
          value={formatNumber(stats?.total_clicks ?? 0)}
          icon={MousePointerClick}
          isLoading={isLoading}
        />
      </div>

      {/* Create form */}
      <CreateLinkForm />

      {/* Recent links */}
      <section aria-label={t("dashboard.recentLinks")}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">{t("dashboard.recentLinks")}</h2>
          <Button variant="ghost" size="sm" asChild>
            <Link to="/links">
              {t("dashboard.viewAll")}
              <ArrowRight className="ml-1 h-4 w-4" />
            </Link>
          </Button>
        </div>

        {isLoading && recentLinks.length === 0 && (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-24 w-full" />
            ))}
          </div>
        )}

        {!isLoading && recentLinks.length === 0 && (
          <p className="text-center text-muted-foreground py-8">{t("dashboard.noLinks")}</p>
        )}

        <div className="space-y-3">
          {recentLinks.map((link) => (
            <LinkCard key={link.id} link={link} />
          ))}
        </div>
      </section>
    </div>
  );
}
