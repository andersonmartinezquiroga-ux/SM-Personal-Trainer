-- Deployed to existing SJM Supabase project on 2026-10-18.
-- Bridge radar -> central work_queue -> browser_jobs, read-only only.
CREATE OR REPLACE FUNCTION sjm_ops.safe_job_queue_bridge_v1()
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
  c record;
  w record;
  j record;
  made integer := 0;
  joined integer := 0;
  finished integer := 0;
  blocked_count integer := 0;
  new_id bigint;
begin
  if not pg_catalog.pg_try_advisory_xact_lock(9026101821) then
    return pg_catalog.jsonb_build_object('status','already_running');
  end if;

  -- Radar -> central work_queue. The queue holds only inspection metadata.
  -- Exclude every case whose application was already sent / is under response.
  for c in
    select cases.case_key,cases.source_url
    from sjm_ops.cases cases
    join sjm_ops.public_job_site_allowlist a on a.url=cases.source_url and a.enabled=true
    where cases.project_key='commercial' and cases.lane='radar'
      and cases.status in ('identified','eligibility_review','draft')
      and not exists (
        select 1 from sjm_ops.work_queue existing
        where existing.source_key=cases.case_key
          and existing.dedupe_key like 'jobinspect:%'
          and (
            existing.state in ('queued','running')
            or existing.created_at > pg_catalog.now()-interval '23 hours'
          )
      )
  loop
    insert into sjm_ops.work_queue(
      dedupe_key, kind, state, source_key, source_digest, evidence_url,
      scheduled_at, is_test, max_attempts
    ) values (
      'jobinspect:'||pg_catalog.md5(c.case_key||':'||
           pg_catalog.to_char(pg_catalog.now() at time zone 'UTC','YYYYMMDD')),
      'research','queued',c.case_key,pg_catalog.md5(c.source_url),c.source_url,
      pg_catalog.now(),false,1
    ) on conflict(dedupe_key) do nothing returning id into new_id;
    if new_id is not null then made:=made+1; end if;
    new_id:=null;
  end loop;

  -- Central queue -> existing allowlisted browser_jobs; reconcile back.
  for w in
    select q.*
    from sjm_ops.work_queue q
    where q.kind='research'
      and q.dedupe_key like 'jobinspect:%'
      and q.is_test=false
      and q.state in ('queued','running','blocked')
    order by q.id
    limit 30
    for update of q skip locked
  loop
    if not exists (
      select 1 from sjm_ops.cases c2
      join sjm_ops.public_job_site_allowlist a2
        on a2.url=c2.source_url and a2.enabled=true
      where c2.case_key=w.source_key
        and c2.source_url=w.evidence_url
        and c2.status in ('identified','eligibility_review','draft')
    ) then
      update sjm_ops.work_queue
      set state='cancelled',updated_at=pg_catalog.now(),
          last_error='case_or_allowlist_no_longer_eligible_no_submission'
      where id=w.id;
      continue;
    end if;

    select b.id,b.state,b.last_error,b.completed_at,b.response_summary
    into j
    from sjm_ops.browser_jobs b
    where b.operation='inspect' and b.target_url=w.evidence_url
      and (b.state in ('queued','waiting') or
           b.completed_at > pg_catalog.now()-interval '23 hours')
    order by b.id desc
    limit 1;

    if j.id is null and w.state='queued' then
      insert into sjm_ops.browser_jobs(job_key,operation,target_url,state)
      values ('jobinspect-workqueue-'||w.id::text,'inspect',w.evidence_url,'queued')
      on conflict(job_key) do nothing;
      update sjm_ops.work_queue
      set state='running',claimed_at=coalesce(claimed_at,pg_catalog.now()),
          attempts=1,updated_at=pg_catalog.now()
      where id=w.id;
      joined:=joined+1;
    elsif j.state in ('queued','waiting') then
      update sjm_ops.work_queue
      set state='running',claimed_at=coalesce(claimed_at,pg_catalog.now()),
          attempts=1,updated_at=pg_catalog.now()
      where id=w.id and state <> 'running';
      joined:=joined+1;
    elsif j.state='done' and j.response_summary->>'submitted'='false' then
      update sjm_ops.work_queue
      set state='done',completed_at=pg_catalog.now(),attempts=1,
          last_error=null,updated_at=pg_catalog.now()
      where id=w.id and state <> 'done';
      finished:=finished+1;
    elsif j.state='failed' then
      update sjm_ops.work_queue
      set state='blocked',attempts=1,
          last_error=left('public_inspection_failed_no_application:'||
                         coalesce(j.last_error,'unknown'),250),
          updated_at=pg_catalog.now()
      where id=w.id and state <> 'blocked';
      blocked_count:=blocked_count+1;
    end if;
    j:=null;
  end loop;

  return pg_catalog.jsonb_build_object(
    'status','ok','radar_tasks_added',made,'browser_tasks_linked',joined,
    'read_only_inspections_completed',finished,
    'inspection_tasks_blocked',blocked_count,
    'employer_applications_submitted',0
  );
end;
$function$
;
revoke all on function sjm_ops.safe_job_queue_bridge_v1() from public,anon,authenticated;
grant execute on function sjm_ops.safe_job_queue_bridge_v1() to service_role;
select cron.schedule('sjm-job-queue-bridge-v1','*/5 * * * *',$cron$select sjm_ops.safe_job_queue_bridge_v1();$cron$);
