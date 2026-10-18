-- Installed in existing Supabase project 2026-10-18.
-- Preserve only non-personal public application metadata; never store candidate values.
CREATE OR REPLACE FUNCTION sjm_ops.browser_collect_v1()
 RETURNS integer
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
  j sjm_ops.browser_jobs%rowtype;
  r record;
  details jsonb;
  count_completed integer:=0;
  pass boolean;
begin
  for j in select * from sjm_ops.browser_jobs where state='waiting' and request_id is not null
    order by id asc for update skip locked
  loop
    select status_code,content,timed_out,error_msg into r
      from net._http_response where id=j.request_id;
    if not found then
      if j.dispatched_at < now() - interval '4 minutes' then
        update sjm_ops.browser_jobs
          set state='failed',last_error='No HTTP response after 4 minutes',completed_at=now(),last_checked_at=now()
          where id=j.id;
        count_completed:=count_completed+1;
      end if;
      continue;
    end if;
    begin details:=r.content::jsonb;
    exception when others then details='{}'::jsonb;
    end;
    pass:=r.status_code=200 and
      case when j.operation='self_test'
        then (details #>> '{form,confirmation}')='RECIBIDO' and (details #>> '{form,submitted}')='true'
        else (details ->> 'submitted')='false'
           and coalesce(details ->> 'challenge_detected','false')='false'
           and lower(coalesce(details ->> 'title','')) not in ('just a moment...','just a moment','attention required!','verify you are human')
           and (
             coalesce((details ->> 'form_fields_total')::integer,0)>0
             or (
               (details ->> 'listing_visible')='true'
               and length(coalesce(details ->> 'title',''))>3
             )
           )
      end;
    update sjm_ops.browser_jobs
      set state=case when pass then 'done' else 'failed' end,
          completed_at=now(),last_checked_at=now(),
          response_summary=jsonb_build_object(
            'http_status',r.status_code,
            'passed',pass,
            'operation',j.operation,
            'title',case when j.operation='inspect' then left(details->>'title',180) else 'SJM Fictional Test' end,
            'fields',case when j.operation='inspect' then details->'form_fields_total' else null end,
            'submitted',case when j.operation='self_test' then details #> '{form,submitted}' else details->'submitted' end,
            'checked_at_utc',case when j.operation='inspect' then details->'checked_at_utc' else null end,
            'inspection_kind',case
                 when j.operation='self_test' then 'self_test'
                 when exists (select 1 from sjm_ops.public_job_site_allowlist a
                        where a.url=j.target_url and a.inspection_class='form')
                   and coalesce((details->>'form_fields_total')::integer,0)>0
                   then 'form'
                 else 'listing' end,
            'listing_visible',details->'listing_visible',
            'challenge_detected',case
              when lower(coalesce(details->>'title','')) in ('just a moment...','just a moment','attention required!','verify you are human')
                then 'true'::jsonb
              else coalesce(details->'challenge_detected','false'::jsonb)
              end,
            'application_form_visible',details->'application_form_visible',
            'required_phone',case when j.operation='inspect' then coalesce(details->'required_phone','false'::jsonb) else null end,
            'required_cv',case when j.operation='inspect' then coalesce(details->'required_cv','false'::jsonb) else null end,
            'required_fields',case when j.operation='inspect' then coalesce(details->'required_fields','[]'::jsonb) else '[]'::jsonb end,
            'login_link_visible',details->'login_link_visible',
            'apply_link_visible',details->'apply_link_visible',
            'final_url',left(details->>'final_url',500),
            'form_adapter',details #> '{adapter_summary,adapter}',
            'preflight_state',details #> '{adapter_summary,preflight_state}',
            'approval_scopes',coalesce(details #> '{adapter_summary,required_approval_scopes}','[]'::jsonb),
            'legal_consent_review_required',coalesce(details #> '{adapter_summary,legal_consent_review_required}','false'::jsonb),
            'automatic_submission_enabled','false'::jsonb
          ),
          last_error=case
            when pass then null
            when details->>'challenge_detected'='true'
              or lower(coalesce(details->>'title','')) in ('just a moment...','just a moment','attention required!','verify you are human')
              then 'human_challenge_detected_no_bypass'
            when r.status_code=200 and j.operation='inspect' then 'public_form_or_listing_not_verified'
            else left(concat('HTTP:',r.status_code,',',coalesce(r.error_msg,''),',timeout:',coalesce(r.timed_out::text,'')),320) end
      where id=j.id;
    count_completed:=count_completed+1;
  end loop;
  return count_completed;
end;
$function$
;
revoke all on function sjm_ops.browser_collect_v1() from public,anon,authenticated;
grant execute on function sjm_ops.browser_collect_v1() to service_role;
