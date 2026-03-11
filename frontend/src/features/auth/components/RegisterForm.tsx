import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Eye, EyeOff } from "lucide-react";
import { useAuthStore } from "../store/authStore";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/shared/components/ui/card";

type FieldErrors = Record<string, string[]>;

export function RegisterForm() {
  const { t } = useTranslation();
  const { register, isLoading } = useAuthStore();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    email: "",
    password: "",
    first_name: "",
    last_name: "",
  });
  const [showPassword, setShowPassword] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [generalError, setGeneralError] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFieldErrors({});
    setGeneralError(null);
    try {
      await register(form);
      navigate("/dashboard");
    } catch (err: unknown) {
      const details =
        (err as { response?: { data?: { error?: { details?: FieldErrors } } } })
          ?.response?.data?.error?.details;
      if (details) {
        setFieldErrors(details);
      } else {
        setGeneralError(t("auth.registrationFailedMsg"));
      }
    }
  };

  const fieldError = (field: string) => {
    const errs = fieldErrors[field];
    return errs?.length ? <p className="text-sm text-destructive">{errs[0]}</p> : null;
  };

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader className="space-y-1">
        <CardTitle className="text-2xl">{t("auth.createAccount")}</CardTitle>
        <CardDescription>{t("auth.startShortening")}</CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit}>
        <CardContent className="space-y-4">
          {generalError && <p className="text-sm text-destructive">{generalError}</p>}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              {fieldError("first_name")}
              <Label htmlFor="first_name">{t("auth.firstName")}</Label>
              <Input id="first_name" name="first_name" placeholder="Jane" onChange={handleChange} autoComplete="given-name" />
            </div>
            <div className="space-y-2">
              {fieldError("last_name")}
              <Label htmlFor="last_name">{t("auth.lastName")}</Label>
              <Input id="last_name" name="last_name" placeholder="Doe" onChange={handleChange} autoComplete="family-name" />
            </div>
          </div>
          <div className="space-y-2">
            {fieldError("email")}
            <Label htmlFor="email">{t("auth.email")}</Label>
            <Input
              id="email"
              name="email"
              type="email"
              placeholder="you@example.com"
              onChange={handleChange}
              required
              autoComplete="email"
            />
          </div>
          <div className="space-y-2">
            {fieldError("password")}
            <Label htmlFor="password">{t("auth.password")}</Label>
            <div className="relative">
              <Input
                id="password"
                name="password"
                type={showPassword ? "text" : "password"}
                placeholder={t("auth.passwordPlaceholder")}
                minLength={6}
                maxLength={128}
                onChange={handleChange}
                required
                autoComplete="new-password"
                className="pr-10"
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                className="absolute inset-y-0 right-0 flex items-center px-3 text-muted-foreground hover:text-foreground"
                tabIndex={-1}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>
        </CardContent>
        <CardFooter className="flex flex-col gap-4">
          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? t("auth.creatingAccount") : t("auth.createAccount")}
          </Button>
          <p className="text-sm text-muted-foreground text-center">
            {t("auth.alreadyHaveAccount")}{" "}
            <Link to="/login" className="text-primary underline underline-offset-4 hover:text-primary/80">
              {t("auth.signIn")}
            </Link>
          </p>
        </CardFooter>
      </form>
    </Card>
  );
}
