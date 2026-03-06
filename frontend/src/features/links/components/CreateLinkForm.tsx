import { useState } from "react";
import { Plus, Link2 } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { toast } from "@/shared/hooks/useToast";
import { useLinksStore } from "../store/linksStore";

export function CreateLinkForm() {
  const { t } = useTranslation();
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
        title: t("createLink.linkCreated"),
        description: t("createLink.linkCreatedDesc", { url: link.short_url }),
      });
      setUrl("");
      setCustomSlug("");
      setTitle("");
    } catch (err: unknown) {
      const details = (err as { response?: { data?: { error?: { details?: Record<string, string[]> } } } })
        ?.response?.data?.error?.details;
      const msg = details
        ? Object.values(details).flat().join(" ")
        : t("createLink.createError");
      toast({ title: t("createLink.error"), description: msg, variant: "destructive" });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <Link2 className="h-5 w-5" />
          {t("createLink.shortenUrl")}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="flex gap-2">
            <Input
              type="url"
              placeholder={t("createLink.urlPlaceholder")}
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              required
              className="flex-1"
              aria-label={t("createLink.urlAriaLabel")}
            />
            <Button type="submit" disabled={isLoading}>
              <Plus className="mr-1 h-4 w-4" />
              {isLoading ? t("createLink.creating") : t("createLink.shorten")}
            </Button>
          </div>

          <button
            type="button"
            className="text-xs text-muted-foreground hover:text-foreground underline-offset-2 hover:underline"
            onClick={() => setShowAdvanced((v) => !v)}
          >
            {showAdvanced ? t("createLink.hideAdvanced") : t("createLink.showAdvanced")}
          </button>

          {showAdvanced && (
            <div className="grid gap-4 sm:grid-cols-2 pt-2 border-t">
              <div className="space-y-2">
                <Label htmlFor="customSlug">{t("createLink.customSlug")}</Label>
                <Input
                  id="customSlug"
                  placeholder="my-link"
                  value={customSlug}
                  onChange={(e) => setCustomSlug(e.target.value)}
                  pattern="[A-Za-z0-9_-]+"
                  title={t("createLink.slugPattern")}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="title">{t("createLink.title")}</Label>
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
