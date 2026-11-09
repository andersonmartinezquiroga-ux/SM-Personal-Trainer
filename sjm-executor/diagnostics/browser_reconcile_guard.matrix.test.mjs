import assert from 'node:assert/strict';
import {reconcileBrowserJob,isExternalSubmissionProven} from './browser_reconcile_guard.mjs';
// Exhaustive matrix: a recovered job must never be replayed by this guard.
const states=['queued','running','done','failed','unknown',null];
const operations=['inspect','self_test','submit','payment','contract',null];
const errors=['','timeout','CAPTCHA required','2FA required','payment required','unauthorized domain'];
let cases=0;
for(const state of states) for(const operation of operations) for(const error_message of errors) {
  const job={id:'matrix-job',request_id:'matrix-request',state,operation,error_message,submitted:true};
  const decision=reconcileBrowserJob(job);
  assert.ok(['manual_review','never_retry'].includes(decision.action),JSON.stringify(job));
  assert.equal(isExternalSubmissionProven(job),false,JSON.stringify(job));
  if(operation==='self_test') assert.equal(decision.action,'never_retry');
  if(operation==='inspect' && state==='done' && !/captcha|2fa|payment|unauthorized/i.test(error_message))
    assert.equal(decision.action,'never_retry');
  cases++;
}
assert.equal(reconcileBrowserJob({id:'x',request_id:'r',operation:'inspect',state:'failed',error_message:'network timeout'}).action,'manual_review');
console.log(`${cases} fail-closed reconciliation combinations passed`);
