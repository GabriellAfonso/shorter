/**
 * /links — full table view of all user links with search, sort, and pagination.
 */
import { useEffect, useState } from "react";
import { Search, Plus } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useLinksStore } from "../store/linksStore";
import { LinksTable } from "../components/LinksTable";
import { CreateLinkDialog } from "../components/CreateLinkDialog";
import { Input } from "@/shared/components/ui/input";
import { Button } from "@/shared/components/ui/button";

export function LinksPage() {
  const { t } = useTranslation();
  const { links, pagination, isLoading, fetchLinks } = useLinksStore();
  const [search, setSearch] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);

  useEffect(() => {
    fetchLinks(1);
  }, [fetchLinks]);

  const filtered = search
    ? links.filter(
        (l) =>
          l.slug.toLowerCase().includes(search.toLowerCase()) ||
          l.title.toLowerCase().includes(search.toLowerCase()) ||
          l.original_url.toLowerCase().includes(search.toLowerCase())
      )
    : links;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{t("links.title")}</h1>
          <p className="text-muted-foreground mt-1">
            {pagination
              ? t("links.count_other", { count: pagination.count })
              : ""}
          </p>
        </div>

        <div className="flex gap-2">
          {/* Search filter (client-side, instant) */}
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground pointer-events-none" />
            <Input
              placeholder={t("links.searchPlaceholder")}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-8 w-48 sm:w-64"
              aria-label={t("links.searchPlaceholder")}
            />
          </div>

          <Button onClick={() => setDialogOpen(true)}>
            <Plus className="mr-1 h-4 w-4" />
            {t("links.newLink")}
          </Button>
          <CreateLinkDialog
            open={dialogOpen}
            onOpenChange={setDialogOpen}
            showTrigger={false}
          />
        </div>
      </div>

      {/* Table */}
      <LinksTable isLoading={isLoading} links={filtered} />

      {/* Pagination */}
      {pagination && pagination.total_pages > 1 && !search && (
        <div className="flex items-center justify-center gap-2 pt-2">
          <Button
            variant="outline"
            size="sm"
            disabled={!pagination.previous}
            onClick={() => fetchLinks(pagination.current_page - 1)}
          >
            {t("links.previous")}
          </Button>
          <span className="text-sm text-muted-foreground">
            {t("links.page", { current: pagination.current_page, total: pagination.total_pages })}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={!pagination.next}
            onClick={() => fetchLinks(pagination.current_page + 1)}
          >
            {t("links.next")}
          </Button>
        </div>
      )}
    </div>
  );
}
