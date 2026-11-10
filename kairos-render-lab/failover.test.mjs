import test from 'node:test';
import assert from 'node:assert/strict';
import {chooseProvider} from './failover.mjs';
const task={id:'case-1',kind:'inspect',status:'pending'};
const providers=[{id:'render',enabled:true,healthy:true,freeQuotaVerified:true,estimatedCostUsd:0,quotaRemaining:2,capabilities:['inspect']},{id:'github',enabled:true,healthy:true,freeQuotaVerified:true,estimatedCostUsd:0,quotaRemaining:5,capabilities:['inspect']}];
test('chooses eligible provider by remaining quota',()=>assert.equal(chooseProvider(task,providers).providerId,'github'));
test('falls back after failure',()=>assert.equal(chooseProvider({...task,lastFailedProvider:'github'},providers).providerId,'render'));
test('holds active lease and missing consent',()=>{assert.equal(chooseProvider({...task,leaseUntil:'2999-01-01T00:00:00Z'},providers).state,'hold');assert.equal(chooseProvider({...task,requiresConsent:true},providers).reason,'authorization_required')});
test('blocks duplicate-prone submission without key',()=>assert.equal(chooseProvider({...task,submission:true},providers).reason,'missing_idempotency_key'));
test('queues instead of charging',()=>assert.equal(chooseProvider(task,providers.map(p=>({...p,freeQuotaVerified:false}))).state,'queued'));

test('skips expired free provider and uses healthy backup',()=>{const now=Date.parse('2026-11-10T12:00:00Z');const list=[{...providers[0],id:'expired',quotaRemaining:99,expiresAt:'2026-11-10T11:00:00Z'}, {...providers[1],id:'backup'}];assert.equal(chooseProvider(task,list,now).providerId,'backup')});
test('skips provider during cooldown and queues when all unavailable',()=>{const now=Date.parse('2026-11-10T12:00:00Z');const list=providers.map(p=>({...p,cooldownUntil:'2026-11-10T13:00:00Z'}));assert.equal(chooseProvider(task,list,now).state,'queued')});
test('allows provider after cooldown',()=>{const now=Date.parse('2026-11-10T12:00:00Z');const list=[{...providers[0],cooldownUntil:'2026-11-10T11:00:00Z'}];assert.equal(chooseProvider(task,list,now).providerId,'render')});

test('fails closed on malformed active lease',()=>assert.equal(chooseProvider({...task,leaseUntil:'not-a-date'},providers).reason,'invalid_lease'));
test('rejects blank idempotency key',()=>assert.equal(chooseProvider({...task,submission:true,idempotencyKey:'   '},providers).reason,'missing_idempotency_key'));
test('ignores nonnumeric quota',()=>assert.equal(chooseProvider(task,[{...providers[0],quotaRemaining:'99'}]).state,'queued'));

test('does not dispatch running task',()=>assert.equal(chooseProvider({...task,status:'running'},providers).reason,'task_not_runnable'));
test('does not dispatch unknown state',()=>assert.equal(chooseProvider({...task,status:'unexpected'},providers).reason,'task_not_runnable'));
test('allows explicitly retryable task',()=>assert.equal(chooseProvider({...task,status:'retry_ready'},providers).state,'ready'));
