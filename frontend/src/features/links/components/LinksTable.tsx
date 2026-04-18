/**
 * LinksTable — data table view for /links page.
 * Shows all user links with sortable columns and inline actions.
 */
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Copy, Trash2, BarChart2, ExternalLink, Check, ArrowUpDown } from "lucide-react";
import { useTranslation } from "react-i18next";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/components/ui/table";
import { Button } from "@/shared/components/ui/button";
import { Badge } from "@/shared/components/ui/badge";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { toast } from "@/shared/hooks/useToast";
import { useLinksStore } from "../store/linksStore";
import { formatDate, formatNumber, truncateUrl } from "@/shared/lib/utils";
import type { ShortURL } from "@/types";

type SortKey = "created_at" | "click_count" | "title";
type SortDir = "asc" | "desc";

function sortLinks(links: ShortURL[], key: SortKey, dir: SortDir): ShortURL[] {
  return [...links].sort((a, b) => {
    let av: string | number = a[key] ?? "";
    let bv: string | number = b[key] ?? "";
    if (key === "click_count") {
      av = Number(av);
      bv = Number(bv);
    } else {
      av = String(av).toLowerCase();
      bv = String(bv).toLowerCase();
    }
    if (av < bv) return dir === "asc" ? -1 : 1;
    if (av > bv) return dir === "asc" ? 1 : -1;
    return 0;
  });
}

interface CopyButtonProps {
  text: string;
}

function CopyButton({ text }: CopyButtonProps) {
  const { t } = useTranslation();
  const [copied, setCopied] = useState(false);
  const handleCopy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    toast({ title: t("table.copied"), description: text });
  };
  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={handleCopy}
      title={t("table.copyShortUrl")}
      aria-label={t("table.copy")}
    >
      {copied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
    </Button>
  );
}

interface LinksTableProps {
  isLoading?: boolean;
  links?: ShortURL[];
}

export function LinksTable({ isLoading = false, links: linksProp }: LinksTableProps) {
  const { t } = useTranslation();
  const { links: storeLinks, deleteLink } = useLinksStore();
  const links = linksProp ?? storeLinks;
  const navigate = useNavigate();
  const [sortKey, setSortKey] = useState<SortKey>("created_at");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  };

  const handleDelete = async (link: ShortURL) => {
    if (!confirm(t("table.confirmDelete", { slug: link.slug }))) return;
    setDeletingId(link.id);
    try {
      await deleteLink(link.id);
      toast({
        title: t("table.linkDeleted"),
        description: t("table.linkDeletedDesc", { slug: link.slug }),
      });
    } catch {
      toast({
        title: t("table.error"),
        description: t("table.deleteError"),
        variant: "destructive",
      });
    } finally {
      setDeletingId(null);
    }
  };

  const SortHeader = ({ col, label }: { col: SortKey; label: string }) => (
    <Button
      variant="ghost"
      size="sm"
      className="-ml-3 h-8 data-[active=true]:text-foreground"
      data-active={sortKey === col}
      onClick={() => handleSort(col)}
    >
      {label}
      <ArrowUpDown className="ml-1 h-3.5 w-3.5 opacity-60" />
    </Button>
  );

  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-14 w-full" />
        ))}
      </div>
    );
  }

  if (links.length === 0) {
    return (
      <div className="text-center py-16 text-muted-foreground">
        <p className="text-lg font-medium">{t("table.noLinksTitle")}</p>
        <p className="text-sm mt-1">{t("table.noLinksDesc")}</p>
      </div>
    );
  }

  const sorted = sortLinks(links, sortKey, sortDir);

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>
              <SortHeader col="title" label={t("table.titleUrl")} />
            </TableHead>
            <TableHead>{t("table.shortUrl")}</TableHead>
            <TableHead>
              <SortHeader col="click_count" label={t("table.clicks")} />
            </TableHead>
            <TableHead>
              <SortHeader col="created_at" label={t("table.created")} />
            </TableHead>
            <TableHead>{t("table.status")}</TableHead>
            <TableHead className="text-right">{t("table.actions")}</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sorted.map((link) => (
            <TableRow key={link.id}>
              {/* Title + original URL */}
              <TableCell className="max-w-[220px]">
                <p className="font-medium truncate">{link.title || link.slug}</p>
                <p className="text-xs text-muted-foreground truncate" title={link.original_url}>
                  {truncateUrl(link.original_url, 40)}
                </p>
              </TableCell>

              {/* Short URL */}
              <TableCell className="font-mono text-sm">
                <a
                  href={link.short_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline"
                >
                  /{link.slug}
                </a>
              </TableCell>

              {/* Click count */}
              <TableCell className="tabular-nums">{formatNumber(link.click_count)}</TableCell>

              {/* Created date */}
              <TableCell className="text-muted-foreground text-sm whitespace-nowrap">
                {formatDate(link.created_at)}
              </TableCell>

              {/* Status badge */}
              <TableCell>
                {link.is_expired ? (
                  <Badge variant="destructive">{t("badge.expired")}</Badge>
                ) : link.is_active ? (
                  <Badge
                    variant="secondary"
                    className="bg-green-500/15 text-green-600 border-green-500/20"
                  >
                    {t("badge.active")}
                  </Badge>
                ) : (
                  <Badge variant="outline">{t("badge.inactive")}</Badge>
                )}
              </TableCell>

              {/* Actions */}
              <TableCell>
                <div className="flex items-center justify-end gap-0.5">
                  <CopyButton text={link.short_url} />

                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => navigate(`/links/${link.id}/analytics`)}
                    title={t("table.viewAnalytics")}
                    aria-label={t("table.analytics")}
                  >
                    <BarChart2 className="h-4 w-4" />
                  </Button>

                  <Button
                    variant="ghost"
                    size="icon"
                    asChild
                    title={t("table.openOriginal")}
                    aria-label={t("table.open")}
                  >
                    <a href={link.original_url} target="_blank" rel="noopener noreferrer">
                      <ExternalLink className="h-4 w-4" />
                    </a>
                  </Button>

                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleDelete(link)}
                    disabled={deletingId === link.id}
                    title={t("table.delete")}
                    aria-label={t("table.delete")}
                    className="text-destructive hover:text-destructive"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
