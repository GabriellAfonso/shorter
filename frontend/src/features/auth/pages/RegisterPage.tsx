import { Link2 } from "lucide-react";
import { useTranslation } from "react-i18next";
import { RegisterForm } from "../components/RegisterForm";

export function RegisterPage() {
  const { t } = useTranslation();
  return (
    <div className="flex min-h-[calc(100vh-3.5rem)] flex-col items-center justify-center gap-8 py-12">
      <div className="flex flex-col items-center gap-2 text-center">
        <div className="flex items-center gap-2">
          <Link2 className="h-8 w-8 text-primary" />
          <span className="text-3xl font-bold">Shorter</span>
        </div>
        <p className="text-muted-foreground">{t("auth.createFreeAccount")}</p>
      </div>
      <RegisterForm />
    </div>
  );
}
