-- SJM Control 360 - deployed to Supabase on 2026-10-18
-- Safe recovery of temporary failures in READ-ONLY public job inspections.
-- Does NOT submit employer forms, transmit personal data or bypass challenges.
create or replace function sjm_ops.browser_safe_retry_v1()
returns jsonb
language plpgsql
security definer
set search_path = ''
as $fn$
declare
  j sjm_ops.browser_jobs%rowtype;
  inserted_count integer := 0;
  selected_id bigint;
begin
  if not pg_catalog.pg_try_advisory_xact_lock(9026101820) then
    return pg_catalog.jsonb_build_object('status','already_running','retries_enqueued',0);
  end if;

  for j in
    select b.*
    from sjm_ops.browser_jobs b
    join sjm_ops.public_job_site_allowlist a on a.url=b.target_url and a.enabled=true
    where b.operation='inspect'
      and b.state='failed'
      and b.completed_at is not null
      and b.completed_at > pg_catalog.now() - interval '24 hours'
      and b.completed_at <= pg_catalog.now() - interval '20 minutes'
      and (
        b.last_error = 'No HTTP response after 4 minutes'
        or b.last_error ~ '^HTTP:(429|502|503|504)(,|$)'
      )
      and not exists (
        select 1 from sjm_ops.browser_jobs newer
        where newer.target_url=b.target_url and newer.id>b.id
      )
      and not exists (
        select 1 from sjm_ops.cases c
        where c.source_url=b.target_url
          and c.status in ('application_sent','response','approved','rejected')
      )
      and (
        select count(*) from sjm_ops.browser_jobs recent
        where recent.target_url=b.target_url
          and recent.created_at > pg_catalog.now()-interval '24 hours'
      ) < 3
    order by b.completed_at, b.id
    limit 2
    for update of b skip locked
  loop
    insert into sjm_ops.browser_jobs(job_key,operation,target_url,state)
    values (
      'safe-retry:' || pg_catalog.md5(j.id::text || ':' || j.target_url),
      'inspect', j.target_url, 'queued'
    )
    on conflict (job_key) do nothing
    returning id into selected_id;

    if selected_id is not null then
      inserted_count := inserted_count + 1;
    end if;
    selected_id := null;
  end loop;

  return pg_catalog.jsonb_build_object(
    'status','ok',
    'retries_enqueued', inserted_count,
    'mode','allowlisted_read_only',
    'employer_submissions',0
  );
end;
$fn$;

revoke all on function sjm_ops.browser_safe_retry_v1() from public, anon, authenticated;
grant execute on function sjm_ops.browser_safe_retry_v1() to service_role;
select cron.schedule(
  'sjm-browser-safe-retry-v1',
  '*/20 * * * *',
  $cron$select sjm_ops.browser_safe_retry_v1();$cron$
);
