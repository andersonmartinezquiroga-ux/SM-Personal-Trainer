-- SJM Empresa 360 IA · Inventario piloto v1 · 2026-11-14
-- CANONICAL reproducible schema. Production already received the equivalent
-- migrations sjm_empresa360_inventory_pilot_owner_isolated_20261114
-- and sjm_empresa360_inventory_idempotent_owner_rpc_v2.
-- Applies exclusively to a single authenticated owner, NOT multi-company isolation.
create table if not exists public.sjm_business_inventory_items_v1 (
 id uuid primary key default gen_random_uuid(),
 owner_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
 sku text not null check(char_length(btrim(sku)) between 1 and 64),
 name text not null check(char_length(btrim(name)) between 1 and 140),
 unit text not null default 'unidad' check(char_length(btrim(unit)) between 1 and 24),
 reorder_point numeric(14,3) not null default 0 check(reorder_point between 0 and 1000000000),
 active boolean not null default true,
 created_at timestamptz not null default now(),
 unique(owner_id,sku),
 unique(id,owner_id)
);
alter table public.sjm_business_inventory_items_v1 enable row level security;
drop policy if exists sjm_inventory_items_owner_read on public.sjm_business_inventory_items_v1;
create policy sjm_inventory_items_owner_read on public.sjm_business_inventory_items_v1 for select to authenticated using(owner_id=auth.uid());
drop policy if exists sjm_inventory_items_owner_create on public.sjm_business_inventory_items_v1;
create policy sjm_inventory_items_owner_create on public.sjm_business_inventory_items_v1 for insert to authenticated with check(owner_id=auth.uid());
drop policy if exists sjm_inventory_items_owner_modify on public.sjm_business_inventory_items_v1;
create policy sjm_inventory_items_owner_modify on public.sjm_business_inventory_items_v1 for update to authenticated using(owner_id=auth.uid()) with check(owner_id=auth.uid());
revoke all on public.sjm_business_inventory_items_v1 from public,anon,authenticated;
grant select,insert,update on public.sjm_business_inventory_items_v1 to authenticated;

create table if not exists public.sjm_business_inventory_movements_v1 (
 id uuid primary key default gen_random_uuid(),
 owner_id uuid not null references auth.users(id) on delete cascade,
 item_id uuid not null,
 movement_type text not null check(movement_type in ('entrada','salida')),
 quantity numeric(14,3) not null check(quantity>0 and quantity<=1000000000),
 note text not null default '' check(char_length(note)<=240),
 request_key uuid not null,
 created_at timestamptz not null default now(),
 foreign key(item_id,owner_id) references public.sjm_business_inventory_items_v1(id,owner_id) on delete restrict,
 unique(owner_id,request_key)
);
create index if not exists sjm_inventory_moves_owner_item_date_idx on public.sjm_business_inventory_movements_v1(owner_id,item_id,created_at desc);
alter table public.sjm_business_inventory_movements_v1 enable row level security;
drop policy if exists sjm_inventory_moves_owner_read on public.sjm_business_inventory_movements_v1;
create policy sjm_inventory_moves_owner_read on public.sjm_business_inventory_movements_v1 for select to authenticated using(owner_id=auth.uid());
revoke all on public.sjm_business_inventory_movements_v1 from public,anon,authenticated;
grant select on public.sjm_business_inventory_movements_v1 to authenticated;

create or replace function public.sjm_inventory_register_movement_v1(
 p_item_id uuid,p_type text,p_quantity numeric,p_note text,p_request_key uuid
) returns jsonb language plpgsql security definer set search_path=''
as $function$
declare
 v_owner uuid := auth.uid();
 v_stock numeric(14,3);
 v_id uuid;
 v_previous public.sjm_business_inventory_movements_v1%rowtype;
begin
 if v_owner is null then raise exception 'Se requiere inicio de sesión' using errcode='28000'; end if;
 if p_item_id is null or p_type is null or p_type not in('entrada','salida')
 or p_quantity is null or p_quantity<=0 or p_quantity>1000000000
 or p_quantity<>round(p_quantity,3) or p_request_key is null
 or char_length(coalesce(p_note,''))>240 then
  raise exception 'Movimiento inválido' using errcode='22023';
 end if;
 perform 1 from public.sjm_business_inventory_items_v1
  where id=p_item_id and owner_id=v_owner and active=true for update;
 if not found then raise exception 'Producto no disponible o no autorizado' using errcode='42501'; end if;
 select * into v_previous from public.sjm_business_inventory_movements_v1
  where owner_id=v_owner and request_key=p_request_key;
 if found then
  if v_previous.item_id is distinct from p_item_id
   or v_previous.movement_type is distinct from p_type
   or v_previous.quantity is distinct from p_quantity
   or v_previous.note is distinct from coalesce(p_note,'') then
   raise exception 'Clave de solicitud ya utilizada para otro movimiento' using errcode='23505';
  end if;
  select coalesce(sum(case when movement_type='entrada' then quantity else -quantity end),0)
   into v_stock from public.sjm_business_inventory_movements_v1
   where owner_id=v_owner and item_id=p_item_id;
  return jsonb_build_object('ok',true,'duplicatePrevented',true,'movementId',v_previous.id,'stock',v_stock);
 end if;
 select coalesce(sum(case when movement_type='entrada' then quantity else -quantity end),0)
 into v_stock from public.sjm_business_inventory_movements_v1
 where owner_id=v_owner and item_id=p_item_id;
 if p_type='salida' and v_stock<p_quantity then
  raise exception 'Existencias insuficientes. Disponible: %',v_stock using errcode='P0001';
 end if;
 insert into public.sjm_business_inventory_movements_v1(owner_id,item_id,movement_type,quantity,note,request_key)
 values(v_owner,p_item_id,p_type,p_quantity,coalesce(p_note,''),p_request_key)
 returning id into v_id;
 if p_type='entrada' then v_stock:=v_stock+p_quantity; else v_stock:=v_stock-p_quantity; end if;
 return jsonb_build_object('ok',true,'duplicatePrevented',false,'movementId',v_id,'stock',v_stock);
end;
$function$;
revoke all on function public.sjm_inventory_register_movement_v1(uuid,text,numeric,text,uuid) from public,anon,authenticated;
grant execute on function public.sjm_inventory_register_movement_v1(uuid,text,numeric,text,uuid) to authenticated;
