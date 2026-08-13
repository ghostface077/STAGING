"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2, LogIn, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { getErrorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

const loginSchema = z.object({
  email: z.string().min(1, "L'adresse e-mail est obligatoire.").email("Adresse e-mail invalide."),
  password: z.string().min(1, "Le mot de passe est obligatoire."),
});
type LoginFormValues = z.infer<typeof loginSchema>;

export default function AdminLoginPage() {
  const { user, isLoading: isAuthLoading, login } = useAuth();
  const router = useRouter();
  const [serverError, setServerError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { register, handleSubmit, formState: { errors } } = useForm<LoginFormValues>({ resolver: zodResolver(loginSchema) });

  useEffect(() => {
    if (!isAuthLoading && user?.role?.name === "Administrateur") router.replace("/admin/dashboard");
  }, [isAuthLoading, user, router]);

  const onSubmit = async (values: LoginFormValues) => {
    setServerError(null);
    setIsSubmitting(true);
    try {
      const loggedInUser = await login(values.email, values.password);
      if (loggedInUser.role?.name !== "Administrateur") {
        setServerError("Accès réservé aux administrateurs. Utilisez la connexion standard.");
        return;
      }
      router.replace("/admin/dashboard");
    } catch (error) {
      setServerError(getErrorMessage(error));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="flex flex-col items-center gap-2 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary text-primary-foreground">
            <ShieldCheck className="h-6 w-6" />
          </div>
          <h1 className="text-xl font-semibold text-white">Back-office administrateur</h1>
          <p className="text-sm text-slate-400">Accès réservé aux administrateurs de la plateforme.</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Connexion administrateur</CardTitle>
            <CardDescription>Saisissez vos identifiants administrateur.</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-4" onSubmit={handleSubmit(onSubmit)} noValidate>
              {serverError && (
                <Alert variant="destructive">
                  <AlertDescription>{serverError}</AlertDescription>
                </Alert>
              )}
              <div className="space-y-1.5">
                <Label htmlFor="email">Adresse e-mail</Label>
                <Input id="email" type="email" autoComplete="username" {...register("email")} />
                {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="password">Mot de passe</Label>
                <Input id="password" type="password" autoComplete="current-password" {...register("password")} />
                {errors.password && <p className="text-xs text-destructive">{errors.password.message}</p>}
              </div>
              <Button type="submit" className="w-full" disabled={isSubmitting}>
                {isSubmitting ? <Loader2 className="animate-spin" /> : <LogIn />}
                Se connecter
              </Button>
            </form>
          </CardContent>
        </Card>

        <p className="text-center text-xs text-slate-400">
          <Link href="/login" className="hover:text-white hover:underline">Retour à la connexion standard</Link>
        </p>
      </div>
    </div>
  );
}
