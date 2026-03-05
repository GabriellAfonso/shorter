/**
 * CreateLinkDialog — modal form for creating a new short URL.
 * Controlled externally via `open` / `onOpenChange` props.
 */
import { useState } from "react";
import { Plus } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/shared/components/ui/dialog";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import { Separator } from "@/shared/components/ui/separator";
import { toast } from "@/shared/hooks/useToast";
import { useLinksStore } from "../store/linksStore";

interface FormState {
  original_url: string;
  slug: string;
  title: string;
  expires_at: string;
}

const DEFAULT_FORM: FormState = {
  original_url: "",
  slug: "",
  title: "",
  expires_at: "",
};

interface CreateLinkDialogProps {
  /** When provided, the dialog is controlled externally. */
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  /** Render the default trigger button when no external control. */
  showTrigger?: boolean;
}

export function CreateLinkDialog({
  open,
  onOpenChange,
  showTrigger = true,
}: CreateLinkDialogProps) {
  const { createLink } = useLinksStore();
  const [form, setForm] = useState<FormState>(DEFAULT_FORM);
  const [isLoading, setIsLoading] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.original_url) return;

    setIsLoading(true);
    try {
      const link = await createLink({
        original_url: form.original_url,
        slug: form.slug || undefined,
        title: form.title || undefined,
        expires_at: form.expires_at || null,
      });

      toast({ title: "Link created!", description: `Short URL: ${link.short_url}` });
      setForm(DEFAULT_FORM);
      setShowAdvanced(false);
      onOpenChange?.(false);
    } catch (err: unknown) {
      const details = (
        err as { response?: { data?: { error?: { details?: Record<string, string[]> } } } }
      )?.response?.data?.error?.details;
      const msg = details
        ? Object.entries(details)
            .map(([field, errs]) => `${field}: ${errs.join(" ")}`)
            .join("; ")
        : "Failed to create link.";
      toast({ title: "Error", description: msg, variant: "destructive" });
    } finally {
      setIsLoading(false);
    }
  };

  const content = (
    <DialogContent className="sm:max-w-[520px]">
      <DialogHeader>
        <DialogTitle>Create Short URL</DialogTitle>
        <DialogDescription>Paste a long URL and get a short, shareable link.</DialogDescription>
      </DialogHeader>

      <form id="create-link-form" onSubmit={handleSubmit} className="space-y-4 py-2">
        {/* Required field */}
        <div className="space-y-2">
          <Label htmlFor="original_url">
            Destination URL <span className="text-destructive">*</span>
          </Label>
          <Input
            id="original_url"
            name="original_url"
            type="url"
            placeholder="https://your-long-url.com/path"
            value={form.original_url}
            onChange={handleChange}
            required
            autoFocus
          />
        </div>

        {/* Advanced toggle */}
        <button
          type="button"
          className="text-xs text-muted-foreground hover:text-foreground underline-offset-2 hover:underline"
          onClick={() => setShowAdvanced((v) => !v)}
        >
          {showAdvanced ? "Hide" : "Show"} advanced options
        </button>

        {showAdvanced && (
          <>
            <Separator />
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="slug">Custom slug</Label>
                <Input
                  id="slug"
                  name="slug"
                  placeholder="my-link"
                  value={form.slug}
                  onChange={handleChange}
                  pattern="[A-Za-z0-9_-]*"
                  title="Letters, numbers, hyphens and underscores only"
                />
                <p className="text-xs text-muted-foreground">Leave blank to auto-generate.</p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="title">Title</Label>
                <Input
                  id="title"
                  name="title"
                  placeholder="My awesome link"
                  value={form.title}
                  onChange={handleChange}
                />
              </div>

              <div className="space-y-2 sm:col-span-2">
                <Label htmlFor="expires_at">Expiry date &amp; time (optional)</Label>
                <Input
                  id="expires_at"
                  name="expires_at"
                  type="datetime-local"
                  value={form.expires_at}
                  onChange={handleChange}
                  min={new Date(Date.now() + 60_000).toISOString().slice(0, 16)}
                />
              </div>
            </div>
          </>
        )}
      </form>

      <DialogFooter>
        <Button
          type="button"
          variant="outline"
          onClick={() => onOpenChange?.(false)}
          disabled={isLoading}
        >
          Cancel
        </Button>
        <Button type="submit" form="create-link-form" disabled={isLoading}>
          <Plus className="mr-1 h-4 w-4" />
          {isLoading ? "Creating…" : "Create link"}
        </Button>
      </DialogFooter>
    </DialogContent>
  );

  if (showTrigger) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogTrigger asChild>
          <Button>
            <Plus className="mr-1 h-4 w-4" />
            New link
          </Button>
        </DialogTrigger>
        {content}
      </Dialog>
    );
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      {content}
    </Dialog>
  );
}
