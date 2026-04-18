import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Copy, Trash2, BarChart2, ExternalLink, Check } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Card, CardContent } from "@/shared/components/ui/card";
import { Button } from "@/shared/components/ui/button";
import { Badge } from "@/shared/components/ui/badge";
import { toast } from "@/shared/hooks/useToast";
import { useLinksStore } from "../store/linksStore";
import { formatDate, formatNumber, truncateUrl } from "@/shared/lib/utils";
import type { ShortURL } from "@/types";

interface LinkCardProps {
  link: ShortURL;
}

export function LinkCard({ link }: LinkCardProps) {
  const { t } = useTranslation();
  const { deleteLink } = useLinksStore();
  const navigate = useNavigate();
  const [copied, setCopied] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(link.short_url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    toast({ title: t("linkCard.copied"), description: link.short_url });
  };

  const handleDelete = async () => {
    if (!confirm(t("linkCard.confirmDelete", { slug: link.slug }))) return;
    setDeleting(true);
    try {
      await deleteLink(link.id);
      toast({
        title: t("linkCard.linkDeleted"),
        description: t("linkCard.linkDeletedDesc", { slug: link.slug }),
      });
    } catch {
      toast({
        title: t("linkCard.error"),
        description: t("linkCard.deleteError"),
        variant: "destructive",
      });
    } finally {
      setDeleting(false);
    }
  };

  return (
    <Card className="group transition-shadow hover:shadow-md">
      <CardContent className="p-5">
        <div className="flex items-start justify-between gap-4">
          {/* Info */}
          <div className="flex-1 min-w-0 space-y-1">
            {link.title && <p className="font-medium truncate">{link.title}</p>}

            <div className="flex items-center gap-2 flex-wrap">
              <a
                href={link.short_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary font-mono text-sm hover:underline"
              >
                {link.short_url}
              </a>
              {link.is_expired && (
                <Badge variant="destructive" className="text-xs">
                  {t("badge.expired")}
                </Badge>
              )}
              {!link.is_active && (
                <Badge variant="secondary" className="text-xs">
                  {t("badge.inactive")}
                </Badge>
              )}
            </div>

            <p className="text-xs text-muted-foreground truncate">
              {truncateUrl(link.original_url, 60)}
            </p>

            <div className="flex items-center gap-4 text-xs text-muted-foreground pt-1">
              <span>{t("linkCard.clicks", { n: formatNumber(link.click_count) })}</span>
              <span>{t("linkCard.createdAt", { date: formatDate(link.created_at) })}</span>
              {link.expires_at && (
                <span>{t("linkCard.expiresAt", { date: formatDate(link.expires_at) })}</span>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-1 shrink-0">
            <Button
              variant="ghost"
              size="icon"
              onClick={handleCopy}
              title={t("linkCard.copyShortUrl")}
              aria-label={t("linkCard.copyShortUrl")}
            >
              {copied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => navigate(`/links/${link.id}/analytics`)}
              title={t("linkCard.viewAnalytics")}
              aria-label={t("linkCard.viewAnalytics")}
            >
              <BarChart2 className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              asChild
              title={t("linkCard.openOriginalUrl")}
              aria-label={t("linkCard.openOriginalUrl")}
            >
              <a href={link.original_url} target="_blank" rel="noopener noreferrer">
                <ExternalLink className="h-4 w-4" />
              </a>
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={handleDelete}
              disabled={deleting}
              title={t("linkCard.deleteLink")}
              aria-label={t("linkCard.deleteLink")}
              className="text-destructive hover:text-destructive"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
