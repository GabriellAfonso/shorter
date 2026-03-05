import { Link2 } from "lucide-react";
import { LoginForm } from "../components/LoginForm";

export function LoginPage() {
  return (
    <div className="flex min-h-[calc(100vh-3.5rem)] flex-col items-center justify-center gap-8 py-12">
      <div className="flex flex-col items-center gap-2 text-center">
        <div className="flex items-center gap-2">
          <Link2 className="h-8 w-8 text-primary" />
          <span className="text-3xl font-bold">Shorter</span>
        </div>
        <p className="text-muted-foreground">Shorten. Share. Track.</p>
      </div>
      <LoginForm />
    </div>
  );
}
