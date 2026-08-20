"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { motion } from "framer-motion";
import { BookOpen, LifeBuoy, Loader2, LogIn, ShieldCheck, Ticket } from "lucide-react";
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

const HIGHLIGHTS = [
  { icon: Ticket, text: "Suivi des tickets de bout en bout, du signalement à la résolution." },
  { icon: ShieldCheck, text: "Échéances SLA surveillées en continu, avant qu'elles ne soient dépassées." },
  { icon: BookOpen, text: "Une base de connaissances pour résoudre soi-même les problèmes courants." },
];

export default function LoginPage() {
  const { user, isLoading: isAuthLoading, login } = useAuth();
  const router = useRouter();
  const [serverError, setServerError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({ resolver: zodResolver(loginSchema) });

  useEffect(() => {
    if (!isAuthLoading && user) router.replace("/dashboard");
  }, [isAuthLoading, user, router]);

  const onSubmit = async (values: LoginFormValues) => {
    setServerError(null);
    setIsSubmitting(true);
    try {
      await login(values.email, values.password);
      router.replace("/dashboard");
    } catch (error) {
      setServerError(getErrorMessage(error));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      {/* Panneau de marque — masqué sur mobile, le formulaire reste identique à avant sur petit écran. */}
      <div className="relative hidden overflow-hidden bg-[hsl(var(--primary))] lg:flex lg:flex-col lg:justify-between lg:p-12">
        <div className="pointer-events-none absolute inset-0 login-ambient" aria-hidden />

        <div className="relative z-10 flex items-center gap-2.5 text-primary-foreground">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/15">
            <LifeBuoy className="h-5 w-5" />
          </span>
          <span className="text-sm font-semibold tracking-tight">IT Support</span>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
          className="relative z-10 max-w-md"
        >
          <h1 className="text-3xl font-semibold leading-tight tracking-tight text-primary-foreground">
            Le support informatique, sans friction.
          </h1>
          <ul className="mt-8 space-y-4">
            {HIGHLIGHTS.map(({ icon: Icon, text }) => (
              <li key={text} className="flex items-start gap-3 text-sm text-primary-foreground/85">
                <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-white/15">
                  <Icon className="h-3.5 w-3.5" />
                </span>
                {text}
              </li>
            ))}
          </ul>
        </motion.div>

        <p className="relative z-10 text-xs text-primary-foreground/60">Service informatique</p>
      </div>

      {/* Formulaire — logique et champs strictement identiques à avant. */}
      <div className="flex min-h-screen items-center justify-center bg-muted/40 px-4 py-12">
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
          className="w-full max-w-sm space-y-6"
        >
          <div className="flex flex-col items-center gap-2 text-center lg:hidden">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary text-primary-foreground">
              <LifeBuoy className="h-6 w-6" />
            </div>
            <h1 className="text-xl font-semibold">IT Support</h1>
            <p className="text-sm text-muted-foreground">Gestion des incidents et demandes informatiques</p>
          </div>

          <Card className="shadow-premium-md">
            <CardHeader>
              <CardTitle>Connexion</CardTitle>
              <CardDescription>Connectez-vous avec votre adresse e-mail professionnelle.</CardDescription>
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
                  <Input id="email" type="email" placeholder="prenom.nom@itsupport.example" autoComplete="username" {...register("email")} />
                  {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="password">Mot de passe</Label>
                  <Input id="password" type="password" placeholder="••••••••" autoComplete="current-password" {...register("password")} />
                  {errors.password && <p className="text-xs text-destructive">{errors.password.message}</p>}
                </div>
                <Button type="submit" className="w-full" disabled={isSubmitting}>
                  {isSubmitting ? <Loader2 className="animate-spin" /> : <LogIn />}
                  Se connecter
                </Button>
              </form>
            </CardContent>
          </Card>

          <p className="text-center text-sm text-muted-foreground">
            Pas encore de compte ?{" "}
            <Link href="/inscription" className="font-medium text-primary hover:underline">
              Créer un compte
            </Link>
          </p>
          <p className="text-center text-xs text-muted-foreground">
            Accès administrateur ?{" "}
            <Link href="/admin/login" className="font-medium text-primary hover:underline">
              Back-office
            </Link>
          </p>
        </motion.div>
      </div>
    </div>
  );
}
