"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { KeyRound, Loader2, Save } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { PageHeader } from "@/components/common/page-header";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/components/ui/use-toast";
import { getErrorMessage, usersApi } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { getInitials } from "@/lib/utils";

const passwordSchema = z
  .object({
    current_password: z.string().min(1, "Le mot de passe actuel est obligatoire."),
    new_password: z.string().min(8, "Le nouveau mot de passe doit contenir au moins 8 caractères."),
    confirm_password: z.string().min(1, "Merci de confirmer le nouveau mot de passe."),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: "Les mots de passe ne correspondent pas.",
    path: ["confirm_password"],
  });
type PasswordFormValues = z.infer<typeof passwordSchema>;

export default function ProfilePage() {
  const { user, refreshUser } = useAuth();
  const { toast } = useToast();
  const [firstName, setFirstName] = useState(user?.first_name ?? "");
  const [lastName, setLastName] = useState(user?.last_name ?? "");
  const [phone, setPhone] = useState(user?.phone ?? "");
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [profileError, setProfileError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<PasswordFormValues>({ resolver: zodResolver(passwordSchema) });
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [isSavingPassword, setIsSavingPassword] = useState(false);

  if (!user) return null;

  const handleSaveProfile = async (event: React.FormEvent) => {
    event.preventDefault();
    setProfileError(null);
    setIsSavingProfile(true);
    try {
      await usersApi.updateMyProfile({ first_name: firstName, last_name: lastName, phone });
      await refreshUser();
      toast({ title: "Profil mis à jour avec succès." });
    } catch (error) {
      setProfileError(getErrorMessage(error));
    } finally {
      setIsSavingProfile(false);
    }
  };

  const onChangePassword = async (values: PasswordFormValues) => {
    setPasswordError(null);
    setIsSavingPassword(true);
    try {
      await usersApi.changeMyPassword({ current_password: values.current_password, new_password: values.new_password });
      toast({ title: "Mot de passe modifié avec succès." });
      reset();
    } catch (error) {
      setPasswordError(getErrorMessage(error));
    } finally {
      setIsSavingPassword(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <PageHeader title="Mon profil" description="Gérez vos informations personnelles et votre mot de passe." />

      <Card>
        <CardHeader className="flex flex-row items-center gap-4">
          <Avatar className="h-14 w-14">
            <AvatarFallback className="text-lg">{getInitials(user.first_name, user.last_name)}</AvatarFallback>
          </Avatar>
          <div>
            <CardTitle>{user.first_name} {user.last_name}</CardTitle>
            <p className="text-sm text-muted-foreground">{user.role?.name} {user.department ? `· ${user.department.name}` : ""}</p>
          </div>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={handleSaveProfile}>
            {profileError && <Alert variant="destructive"><AlertDescription>{profileError}</AlertDescription></Alert>}
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label htmlFor="first_name">Prénom</Label>
                <Input id="first_name" value={firstName} onChange={(event) => setFirstName(event.target.value)} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="last_name">Nom</Label>
                <Input id="last_name" value={lastName} onChange={(event) => setLastName(event.target.value)} />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="email">Adresse e-mail</Label>
              <Input id="email" value={user.email} disabled />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="phone">Téléphone</Label>
              <Input id="phone" value={phone ?? ""} onChange={(event) => setPhone(event.target.value)} />
            </div>
            <Button type="submit" disabled={isSavingProfile}>
              {isSavingProfile ? <Loader2 className="animate-spin" /> : <Save />}
              Enregistrer
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Changer mon mot de passe</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={handleSubmit(onChangePassword)} noValidate>
            {passwordError && <Alert variant="destructive"><AlertDescription>{passwordError}</AlertDescription></Alert>}
            <div className="space-y-1.5">
              <Label htmlFor="current_password">Mot de passe actuel</Label>
              <Input id="current_password" type="password" {...register("current_password")} />
              {errors.current_password && <p className="text-xs text-destructive">{errors.current_password.message}</p>}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="new_password">Nouveau mot de passe</Label>
              <Input id="new_password" type="password" {...register("new_password")} />
              {errors.new_password && <p className="text-xs text-destructive">{errors.new_password.message}</p>}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="confirm_password">Confirmer le nouveau mot de passe</Label>
              <Input id="confirm_password" type="password" {...register("confirm_password")} />
              {errors.confirm_password && <p className="text-xs text-destructive">{errors.confirm_password.message}</p>}
            </div>
            <Button type="submit" disabled={isSavingPassword}>
              {isSavingPassword ? <Loader2 className="animate-spin" /> : <KeyRound />}
              Modifier le mot de passe
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
