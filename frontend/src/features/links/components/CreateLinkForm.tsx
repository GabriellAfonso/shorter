import { useState } from "react";
import { Plus, Link2 } from "lucide-react";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { toast } from "@/shared/hooks/useToast";
import { useLinksStore } from "../store/linksStore";

export function CreateLinkForm() {
  const { createLink } = useLinksStore();
  const [url, setUrl] = useState("");
  const [customSlug, setCustomSlug] = useState("");
  const [title, setTitle] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) return;

    setIsLoading(true);
    try {
      const link = await createLink({
        original_url: url,
        slug: customSlug || undefined,
        title: title || undefined,
      });
      toast({
        title: "Link created!",
        description: `Your short URL: ${link.short_url}`,
      });
      setUrl("");
      setCustomSlug("");
      setTitle("");
    } catch (err: unknown) {
      const details = (err as { response?: { data?: { error?: { details?: Record<string, string[]> } } } })
        ?.response?.data?.error?.details;
      const msg = details
        ? Object.values(details).flat().join(" ")
        : "Failed to create link. Please try again.";
      toast({ title: "Error", description: msg, variant: "destructive" });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <Link2 className="h-5 w-5" />
          Shorten a URL
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="flex gap-2">
            <Input
              type="url"
              placeholder="https://your-long-url.com/path/to/page"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              required
              className="flex-1"
              aria-label="URL to shorten"
            />
            <Button type="submit" disabled={isLoading}>
              <Plus className="mr-1 h-4 w-4" />
              {isLoading ? "Creating…" : "Shorten"}
            </Button>
          </div>

          <button
            type="button"
            className="text-xs text-muted-foreground hover:text-foreground underline-offset-2 hover:underline"
            onClick={() => setShowAdvanced((v) => !v)}
          >
            {showAdvanced ? "Hide" : "Show"} advanced options
          </button>

          {showAdvanced && (
            <div className="grid gap-4 sm:grid-cols-2 pt-2 border-t">
              <div className="space-y-2">
                <Label htmlFor="customSlug">Custom slug (optional)</Label>
                <Input
                  id="customSlug"
                  placeholder="my-link"
                  value={customSlug}
                  onChange={(e) => setCustomSlug(e.target.value)}
                  pattern="[A-Za-z0-9_-]+"
                  title="Letters, numbers, hyphens and underscores only"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="title">Title (optional)</Label>
                <Input
                  id="title"
                  placeholder="My awesome link"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                />
              </div>
            </div>
          )}
        </form>
      </CardContent>
    </Card>
  );
}
