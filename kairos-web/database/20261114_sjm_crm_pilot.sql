-- SJM Empresa 360 IA · CRM piloto individual · 2026-11-14
-- Reproducción de la migración vigente sjm_empresa360_crm_owner_isolated_pilot_20261114.
-- No constituye un SaaS multiempresa; no almacenar PII o datos de clientes reales.
create table if not exists public.sjm_business_crm_opportunities_v1 (
 id uuid primary key default gen_random_uuid(),
 owner_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
 company_alias text not null check(char_length(btrim(company_alias)) between 1 and 90),
 opportunity text not null check(char_length(btrim(opportunity)) between 1 and 140),
 estimated_value numeric(14,2) not null default 0 check(estimated_value between 0 and 1000000000000),
 stage text not null default 'nuevo' check(stage in ('nuevo','contactado','propuesta','negociacion','ganado','perdido')),
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now(),
 unique(id,owner_id)
);
alter table public.sjm_business_crm_opportunities_v1 enable row level security;
drop policy if exists sjm_crm_opportunities_owner_read on public.sjm_business_crm_opportunities_v1;
create policy sjm_crm_opportunities_owner_read on public.sjm_business_crm_opportunities_v1
 for select to authenticated using(owner_id=auth.uid());
drop policy if exists sjm_crm_opportunities_owner_insert on public.sjm_business_crm_opportunities_v1;
create policy sjm_crm_opportunities_owner_insert on public.sjm_business_crm_opportunities_v1
 for insert to authenticated with check(owner_id=auth.uid() and stage='nuevo');
revoke all on public.sjm_business_crm_opportunities_v1 from public,anon,authenticated;
grant select,insert on public.sjm_business_crm_opportunities_v1 to authenticated;

create table if not exists public.sjm_business_crm_stage_events_v1 (
 id uuid primary key default gen_random_uuid(),
 owner_id uuid not null references auth.users(id) on delete cascade,
 opportunity_id uuid not null,
 from_stage text not null check(from_stage in ('nuevo','contactado','propuesta','negociacion','ganado','perdido')),
 to_stage text not null check(to_stage in ('nuevo','contactado','propuesta','negociacion','ganado','perdido')),
 note text not null default '' check(char_length(note)<=200),
 request_key uuid not null,
 created_at timestamptz not null default now(),
 foreign key(opportunity_id,owner_id) references public.sjm_business_crm_opportunities_v1(id,owner_id) on delete restrict,
 unique(owner_id,request_key)
);
create index if not exists sjm_business_crm_events_owner_date_idx
 on public.sjm_business_crm_stage_events_v1(owner_id,created_at desc);
alter table public.sjm_business_crm_stage_events_v1 enable row level security;
drop policy if exists sjm_crm_events_owner_read on public.sjm_business_crm_stage_events_v1;
create policy sjm_crm_events_owner_read on public.sjm_business_crm_stage_events_v1
 for select to authenticated using(owner_id=auth.uid());
revoke all on public.sjm_business_crm_stage_events_v1 from public,anon,authenticated;
grant select on public.sjm_business_crm_stage_events_v1 to authenticated;

create or replace function public.sjm_crm_advance_stage_v1(
 p_opportunity_id uuid,p_stage text,p_note text,p_request_key uuid
) returns jsonb language plpgsql security definer set search_path=''
as $function$
declare
 v_owner uuid := auth.uid();
 v_old text;
 v_event_id uuid;
 v_previous public.sjm_business_crm_stage_events_v1%rowtype;
begin
 if v_owner is null then raise exception 'Se requiere inicio de sesión' using errcode='28000'; end if;
 if p_opportunity_id is null or p_stage is null or p_stage not in
 ('nuevo','contactado','propuesta','negociacion','ganado','perdido')
 or p_request_key is null or char_length(coalesce(p_note,''))>200
 then raise exception 'Etapa o solicitud inválida' using errcode='22023'; end if;
 select stage into v_old from public.sjm_business_crm_opportunities_v1
 where id=p_opportunity_id and owner_id=v_owner for update;
 if not found then raise exception 'Oportunidad inexistente o no autorizada' using errcode='42501'; end if;
 select * into v_previous from public.sjm_business_crm_stage_events_v1
 where owner_id=v_owner and request_key=p_request_key;
 if found then
  if v_previous.opportunity_id is distinct from p_opportunity_id
   or v_previous.to_stage is distinct from p_stage
   or v_previous.note is distinct from coalesce(p_note,'')
  then raise exception 'La clave corresponde a un cambio diferente' using errcode='23505'; end if;
  return jsonb_build_object('ok',true,'duplicatePrevented',true,'eventId',v_previous.id,'stage',v_old);
 end if;
 if p_stage=v_old then raise exception 'La oportunidad ya se encuentra en esa etapa' using errcode='22023'; end if;
 update public.sjm_business_crm_opportunities_v1 set stage=p_stage,updated_at=now()
 where id=p_opportunity_id and owner_id=v_owner;
 insert into public.sjm_business_crm_stage_events_v1(owner_id,opportunity_id,from_stage,to_stage,note,request_key)
 values(v_owner,p_opportunity_id,v_old,p_stage,coalesce(p_note,''),p_request_key)
 returning id into v_event_id;
 return jsonb_build_object('ok',true,'duplicatePrevented',false,'eventId',v_event_id,'fromStage',v_old,'stage',p_stage);
end;
$function$;
revoke all on function public.sjm_crm_advance_stage_v1(uuid,text,text,uuid) from public,anon,authenticated;
grant execute on function public.sjm_crm_advance_stage_v1(uuid,text,text,uuid) to authenticated;
