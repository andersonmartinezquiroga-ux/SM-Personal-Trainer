-- COMTROL 360 · Respaldo voluntario de conversaciones, usuario único
-- Migración ya aplicada en el proyecto Supabase SJM el 15-nov-2026.
create table if not exists public.sjm_comtrol_chat_backups_v1 (
 owner_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
 chat_key text not null check(char_length(chat_key) between 8 and 96 and chat_key ~ '^[a-zA-Z0-9_-]+$'),
 title text not null check(char_length(btrim(title)) between 1 and 90),
 messages jsonb not null check(
 jsonb_typeof(messages)='array'
 and jsonb_array_length(messages) between 1 and 60
 and octet_length(messages::text)<=100000),
 updated_at timestamptz not null default now(),
 primary key(owner_id,chat_key)
);
create index if not exists sjm_comtrol_chat_backups_owner_updated_idx
 on public.sjm_comtrol_chat_backups_v1(owner_id,updated_at desc);
alter table public.sjm_comtrol_chat_backups_v1 enable row level security;
drop policy if exists sjm_chat_backups_owner_read on public.sjm_comtrol_chat_backups_v1;
create policy sjm_chat_backups_owner_read on public.sjm_comtrol_chat_backups_v1
 for select to authenticated using(owner_id=auth.uid());
drop policy if exists sjm_chat_backups_owner_create on public.sjm_comtrol_chat_backups_v1;
create policy sjm_chat_backups_owner_create on public.sjm_comtrol_chat_backups_v1
 for insert to authenticated with check(owner_id=auth.uid());
drop policy if exists sjm_chat_backups_owner_update on public.sjm_comtrol_chat_backups_v1;
create policy sjm_chat_backups_owner_update on public.sjm_comtrol_chat_backups_v1
 for update to authenticated using(owner_id=auth.uid()) with check(owner_id=auth.uid());
revoke all on public.sjm_comtrol_chat_backups_v1 from public,anon,authenticated;
grant select,insert,update on public.sjm_comtrol_chat_backups_v1 to authenticated;

-- Derecho de eliminación solo para el propietario, bajo RLS
-- Migración complementaria comtrol_owner_explicit_delete_private_chat_backups_20261115.
drop policy if exists sjm_chat_backups_owner_delete on public.sjm_comtrol_chat_backups_v1;
create policy sjm_chat_backups_owner_delete on public.sjm_comtrol_chat_backups_v1
 for delete to authenticated using(owner_id=auth.uid());
grant delete on public.sjm_comtrol_chat_backups_v1 to authenticated;
