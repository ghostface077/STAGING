"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Plus, Search, Users, UserX } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { ConfirmDialog } from "@/components/common/confirm-dialog";
import { EmptyState } from "@/components/common/empty-state";
import { PageHeader } from "@/components/common/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Pagination } from "@/components/ui/pagination";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useToast } from "@/components/ui/use-toast";
import { useDepartments, useRoles } from "@/hooks/use-reference-data";
import { getErrorMessage, usersApi } from "@/lib/api";
import type { User } from "@/lib/types";

const PAGE_SIZE = 20;

const userSchema = z.object({
  first_name: z.string().min(1, "Le prénom est obligatoire."),
  last_name: z.string().min(1, "Le nom est obligatoire."),
  email: z.string().min(1, "L'adresse e-mail est obligatoire.").email("Adresse e-mail invalide."),
  password: z.string().min(8, "8 caractères minimum.").optional().or(z.literal("")),
  role_id: z.string().min(1, "Le rôle est obligatoire."),
  department_id: z.string().optional(),
});
type UserFormValues = z.infer<typeof userSchema>;

export default function AdminUsersPage() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const { data: roles } = useRoles();
  const { data: departments } = useDepartments();
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [editing, setEditing] = useState<User | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [userToDeactivate, setUserToDeactivate] = useState<User | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["users", { search, page }],
    queryFn: () =>
      usersApi.list({ search: search || undefined, page, page_size: PAGE_SIZE }).then((res) => res.data),
    placeholderData: (previous) => previous,
  });
  const users = data?.items;

  const { register, handleSubmit, watch, setValue, reset, formState: { errors } } = useForm<UserFormValues>({
    resolver: zodResolver(userSchema),
  });

  const openCreate = () => {
    setEditing(null);
    reset({ first_name: "", last_name: "", email: "", password: "", role_id: "", department_id: "" });
    setIsDialogOpen(true);
  };

  const openEdit = (user: User) => {
    setEditing(user);
    reset({
      first_name: user.first_name,
      last_name: user.last_name,
      email: user.email,
      password: "",
      role_id: String(user.role_id),
      department_id: user.department_id ? String(user.department_id) : "",
    });
    setIsDialogOpen(true);
  };

  const onSubmit = async (values: UserFormValues) => {
    setIsSubmitting(true);
    try {
      const payload = {
        first_name: values.first_name,
        last_name: values.last_name,
        email: values.email,
        role_id: Number(values.role_id),
        department_id: values.department_id ? Number(values.department_id) : null,
        ...(values.password ? { password: values.password } : {}),
      };
      if (editing) {
        await usersApi.update(editing.id, payload);
        toast({ title: "Utilisateur mis à jour." });
      } else {
        await usersApi.create({ ...payload, password: values.password || "ChangerMotDePasse123!" });
        toast({ title: "Utilisateur créé avec succès." });
      }
      queryClient.invalidateQueries({ queryKey: ["users"] });
      setIsDialogOpen(false);
    } catch (error) {
      toast({ title: "Erreur", description: getErrorMessage(error), variant: "destructive" });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeactivate = async () => {
    if (!userToDeactivate) return;
    await usersApi.remove(userToDeactivate.id);
    queryClient.invalidateQueries({ queryKey: ["users"] });
    toast({ title: "Utilisateur désactivé." });
  };

  return (
    <div>
      <PageHeader
        title="Utilisateurs"
        description="Gérez les comptes, rôles et services de tous les utilisateurs."
        actions={<Button onClick={openCreate}><Plus /> Nouvel utilisateur</Button>}
      />

      <div className="relative mb-4 max-w-md">
        <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={search}
          onChange={(event) => {
            setSearch(event.target.value);
            setPage(1);
          }}
          placeholder="Rechercher par nom ou e-mail…"
          className="pl-8"
        />
      </div>

      <Card>
        {isLoading ? (
          <div className="space-y-2 p-4">{Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}</div>
        ) : !users || users.length === 0 ? (
          <EmptyState icon={Users} title="Aucun utilisateur" />
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nom</TableHead>
                <TableHead>E-mail</TableHead>
                <TableHead>Rôle</TableHead>
                <TableHead>Service</TableHead>
                <TableHead>Statut</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {users.map((user) => (
                <TableRow key={user.id}>
                  <TableCell className="font-medium">{user.first_name} {user.last_name}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">{user.email}</TableCell>
                  <TableCell><Badge variant="secondary">{user.role?.name}</Badge></TableCell>
                  <TableCell className="text-sm">{user.department?.name ?? "—"}</TableCell>
                  <TableCell>
                    <Badge variant={user.is_active ? "success" : "outline"}>{user.is_active ? "Actif" : "Désactivé"}</Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <Button variant="ghost" size="sm" onClick={() => openEdit(user)}>Modifier</Button>
                    {user.is_active && (
                      <Button variant="ghost" size="sm" className="text-destructive" onClick={() => setUserToDeactivate(user)}>
                        <UserX className="h-3.5 w-3.5" />
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
        <Pagination page={page} pageCount={data?.pages ?? 1} onPageChange={setPage} totalItems={data?.total} pageSize={PAGE_SIZE} />
      </Card>

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>{editing ? "Modifier l'utilisateur" : "Nouvel utilisateur"}</DialogTitle></DialogHeader>
          <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label htmlFor="first_name">Prénom</Label>
                <Input id="first_name" {...register("first_name")} />
                {errors.first_name && <p className="text-xs text-destructive">{errors.first_name.message}</p>}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="last_name">Nom</Label>
                <Input id="last_name" {...register("last_name")} />
                {errors.last_name && <p className="text-xs text-destructive">{errors.last_name.message}</p>}
              </div>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="email">E-mail</Label>
              <Input id="email" type="email" {...register("email")} />
              {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="password">{editing ? "Nouveau mot de passe (optionnel)" : "Mot de passe"}</Label>
              <Input id="password" type="password" placeholder={editing ? "Laisser vide pour ne pas changer" : "Minimum 8 caractères"} {...register("password")} />
              {errors.password && <p className="text-xs text-destructive">{errors.password.message}</p>}
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label>Rôle</Label>
                <Select value={watch("role_id")} onValueChange={(value) => setValue("role_id", value)}>
                  <SelectTrigger><SelectValue placeholder="Sélectionner" /></SelectTrigger>
                  <SelectContent>
                    {roles?.map((role) => <SelectItem key={role.id} value={String(role.id)}>{role.name}</SelectItem>)}
                  </SelectContent>
                </Select>
                {errors.role_id && <p className="text-xs text-destructive">{errors.role_id.message}</p>}
              </div>
              <div className="space-y-1.5">
                <Label>Service</Label>
                <Select value={watch("department_id")} onValueChange={(value) => setValue("department_id", value)}>
                  <SelectTrigger><SelectValue placeholder="Sélectionner" /></SelectTrigger>
                  <SelectContent>
                    {departments?.map((department) => <SelectItem key={department.id} value={String(department.id)}>{department.name}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>Annuler</Button>
              <Button type="submit" disabled={isSubmitting}>{isSubmitting && <Loader2 className="animate-spin" />} Enregistrer</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={!!userToDeactivate}
        onOpenChange={(open) => !open && setUserToDeactivate(null)}
        title="Désactiver cet utilisateur ?"
        description="L'utilisateur ne pourra plus se connecter, mais son historique sera conservé."
        variant="destructive"
        confirmLabel="Désactiver"
        onConfirm={handleDeactivate}
      />
    </div>
  );
}
