-- Staged only: review and deploy with authorized 0.3.30 release.
CREATE OR REPLACE FUNCTION public.sjm_kairos_phone_receive_authorized_v1(p_device_id uuid, p_job_id uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'pg_catalog', 'pg_temp'
AS $function$
declare
 j record;
 now_at timestamptz;
 changed_count integer;
begin
 if p_device_id is null or p_job_id is null then
   return pg_catalog.jsonb_build_object('accepted',false,'reason','invalid_identifiers');
 end if;
 perform pg_catalog.pg_advisory_xact_lock(
   pg_catalog.hashtextextended('kairos-phone-class:'||p_device_id::text,0));
 select job.id,job.status,job.type,job.created_at,job.timeout_at,job.received_at,d.app_version
 into j
 from public.sjm_kairos_phone_jobs_v1 job
 join public.sjm_kairos_phone_devices_v1 d
   on d.device_id=job.device_id and d.owner_id=job.owner_id and d.enabled=true
 where job.id=p_job_id and job.device_id=p_device_id
 for update of job;
 if not found then return pg_catalog.jsonb_build_object('accepted',false,'reason','not_found'); end if;
 if j.type='local_test' and j.app_version not in ('0.3.11','0.3.12','0.3.13','0.3.14','0.3.15','0.3.16','0.3.17','0.3.18','0.3.19','0.3.20','0.3.21','0.3.22','0.3.23','0.3.24','0.3.25','0.3.26','0.3.27','0.3.28','0.3.29','0.3.30') then
   update public.sjm_kairos_phone_jobs_v1
   set status='failed',completed_at=pg_catalog.clock_timestamp(),
     result_message='LOCAL_TEST_APK_CHANGED_NOT_EXECUTED: requires approved KAIRÓS 0.3.11 through 0.3.29'
   where id=p_job_id and status='queued';
   return pg_catalog.jsonb_build_object('accepted',false,'reason','unsupported_apk');
 end if;
 if j.type='app_workflow' and j.app_version not in ('0.3.19','0.3.20','0.3.21','0.3.22','0.3.23','0.3.24','0.3.25','0.3.26','0.3.27','0.3.28','0.3.29','0.3.30') then
   update public.sjm_kairos_phone_jobs_v1
   set status='failed',completed_at=pg_catalog.clock_timestamp(),
       result_message='WORKFLOW_REQUIRES_V0319_TO_V0329: APK unsupported'
   where id=p_job_id and status='queued';
   return pg_catalog.jsonb_build_object('accepted',false,'reason','unsupported_workflow_apk');
 end if;
 if j.status<>'queued' or j.received_at is not null then
   return pg_catalog.jsonb_build_object('accepted',false,'reason','already_received_or_closed');
 end if;
 now_at:=pg_catalog.clock_timestamp();
 -- Always respect the recorded per-job deadline as well as the outer 10-minute limit.
 if (j.timeout_at is not null and j.timeout_at<=now_at)
     or j.created_at<=now_at-interval '10 minutes' then
   update public.sjm_kairos_phone_jobs_v1
   set status='failed',completed_at=pg_catalog.clock_timestamp(),
      result_message='COMMAND_EXPIRED_NOT_EXECUTED: venció el plazo de recepción autorizada'
   where id=p_job_id and status='queued';
   return pg_catalog.jsonb_build_object('accepted',false,'reason','expired');
 end if;
 if not exists(
   select 1 from public.sjm_kairos_phone_execution_gates_v1 g
   where g.device_id=p_device_id
     and ((j.type in ('open_app','open_url','speak','local_test','app_workflow') and not g.pause_open_app)
          or (j.type='notify' and not g.pause_notifications))
 ) then
   update public.sjm_kairos_phone_jobs_v1
   set status='failed',completed_at=pg_catalog.clock_timestamp(),
      result_message='CANCELLED_BY_OWNER_CLASS: no recibido por Android'
   where id=p_job_id and status='queued';
   return pg_catalog.jsonb_build_object('accepted',false,'reason','paused_by_owner');
 end if;
 -- Guard even the tiny race between expiration check and final status update.
 update public.sjm_kairos_phone_jobs_v1
 set status='received',received_at=pg_catalog.clock_timestamp()
 where id=p_job_id and device_id=p_device_id and status='queued'
   and (timeout_at is null or timeout_at>pg_catalog.clock_timestamp())
   and created_at>pg_catalog.clock_timestamp()-interval '10 minutes';
 get diagnostics changed_count = row_count;
 if changed_count<>1 then
   update public.sjm_kairos_phone_jobs_v1
   set status='failed',completed_at=pg_catalog.clock_timestamp(),
      result_message='COMMAND_EXPIRED_NOT_EXECUTED: venció antes de la autorización'
   where id=p_job_id and status='queued';
   return pg_catalog.jsonb_build_object('accepted',false,'reason','expired_at_update');
 end if;
 return pg_catalog.jsonb_build_object('accepted',true,'status','received');
end $function$

