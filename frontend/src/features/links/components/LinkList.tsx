import { useEffect } from "react";
import { Loader2 } from "lucide-react";
import { useLinksStore } from "../store/linksStore";
import { LinkCard } from "./LinkCard";
import { Button } from "@/shared/components/ui/button";

export function LinkList() {
  const { links, pagination, isLoading, fetchLinks } = useLinksStore();

  useEffect(() => {
    fetchLinks();
  }, [fetchLinks]);

  if (isLoading && links.length === 0) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!isLoading && links.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <p className="text-lg font-medium">No links yet</p>
        <p className="text-sm mt-1">Create your first short URL above.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {links.map((link) => (
        <LinkCard key={link.id} link={link} />
      ))}

      {/* Pagination */}
      {pagination && pagination.total_pages > 1 && (
        <div className="flex items-center justify-center gap-2 pt-4">
          <Button
            variant="outline"
            size="sm"
            disabled={!pagination.previous}
            onClick={() => fetchLinks(pagination.current_page - 1)}
          >
            Previous
          </Button>
          <span className="text-sm text-muted-foreground">
            Page {pagination.current_page} of {pagination.total_pages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={!pagination.next}
            onClick={() => fetchLinks(pagination.current_page + 1)}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
}
