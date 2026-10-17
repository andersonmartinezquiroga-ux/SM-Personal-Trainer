#!/usr/bin/env python3
"""SJM Radar independent: public official pages only. Does not apply to jobs or grants."""
import argparse
import datetime as dt
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

SOURCES=[
 {"id":"transperfect-audio-qa-co","project":"income","kind":"job","name":"Audio QA Reviewer Spanish Colombia","url":"https://community.transperfect.com/jobs/720525-audio-quality-assurance-reviewer-spanish-colombia","eligibility_note":"Good English required; candidate skill and eligibility not verified"},
 {"id":"transperfect-voice-director-co","project":"income","kind":"job","name":"Voice Director Spanish Colombia","url":"https://community.transperfect.com/jobs/720577-voice-director-spanish-colombia","eligibility_note":"Relevant voice direction/linguistics/speech tech experience and good English required"},
 {"id":"welodata-community","project":"income","kind":"job","name":"Welo Data — AI work community","url":"https://welodata.ai/join-the-community/","eligibility_note":"Account, assessments and individual offers require separate review"},
 {"id":"techstars-anywhere","project":"human","kind":"accelerator","name":"Techstars Anywhere","url":"https://www.techstars.com/accelerators/anywhere","eligibility_note":"Already applied via SJM; do not duplicate. Equity requires founder's approval"},
 {"id":"awesome-foundation","project":"human","kind":"grant","name":"Awesome Foundation — chapters","url":"https://www.awesomefoundation.org/en","eligibility_note":"Chapter fit and any prior submissions require checking before application"},
]

class VisibleHTML(HTMLParser):
 def __init__(self):
  super().__init__();self.parts=[];self.hidden=0;self.in_title=False;self.title=[]
 def handle_starttag(self,tag,attrs):
  if tag in ('script','style','noscript','svg'):self.hidden+=1
  if tag=='title':self.in_title=True
 def handle_endtag(self,tag):
  if tag in ('script','style','noscript','svg') and self.hidden:self.hidden-=1
  if tag=='title':self.in_title=False
 def handle_data(self,data):
  if self.in_title:self.title.append(data)
  elif not self.hidden:self.parts.append(data)

def classify(text):
 t=re.sub(r'\s+',' ',text).lower()
 if re.search(r'(applications? (are )?closed|this (job|position) (is|has been) (closed|filled)|no longer accepting applications)',t):return 'possibly_closed'
 if re.search(r'(apply now|apply today|application[s]? open|postularme|submit (an? )?application|join the community)',t):return 'application_route_visible'
 return 'no_open_signal_verified'

def examine(s):
 d={'id':s['id'],'project':s['project'],'kind':s['kind'],'name':s['name'],'official_url':s['url'],'eligibility_note':s['eligibility_note'],'checked_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'formal_submission_confirmed':False,'human_eligibility_verified':False,'availability_signal':'not_checked','error':None}
 try:
  req=Request(s['url'],headers={'User-Agent':'SJM-Radar/1.0 (public-read-only)','Accept':'text/html'})
  with urlopen(req,timeout=14) as res:
   dest=res.geturl()
   if urlparse(dest).scheme!='https':raise ValueError('insecure redirect')
   raw=res.read(220000);d['http_status']=getattr(res,'status',200);d['resolved_url']=dest
  p=VisibleHTML();p.feed(raw.decode('utf-8',errors='replace'))
  content=html.unescape(' '.join(p.parts))
  d['page_title']=' '.join(p.title).strip()[:160]
  d['source_sha256']=hashlib.sha256(raw).hexdigest()
  d['availability_signal']=classify(content)
  d['evidence_excerpt']=re.sub(r'\s+',' ',content).strip()[:280]
 except (HTTPError,URLError,TimeoutError,ValueError,OSError) as e:
  d['error']=type(e).__name__+': '+str(e)[:180];d['availability_signal']='unreachable'
 return d

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',default='radar_results.json');ap.add_argument('--self-test',action='store_true');args=ap.parse_args()
 if args.self_test:
  assert classify('Apply now!')=='application_route_visible'
  assert classify('Applications are closed')=='possibly_closed'
  assert classify('Nothing about jobs')=='no_open_signal_verified'
  assert len(SOURCES)==len({s['id'] for s in SOURCES})
  assert all(urlparse(s['url']).scheme=='https' for s in SOURCES)
  print('Radar SJM self-test PASS: 5 checks');return
 outcomes=[examine(s) for s in SOURCES]
 data={'schema_version':1,'generated_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'disclaimer':'Read-only official page checks. NO applications sent. Check requirements, terms, language, identity and prior submissions separately.','checked':len(outcomes),'reachable':sum(x['error'] is None for x in outcomes),'route_visible':sum(x['availability_signal']=='application_route_visible' for x in outcomes),'formal_submissions_created':0,'sources':outcomes}
 dest=Path(args.output);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 print(json.dumps({'checked':data['checked'],'reachable':data['reachable'],'visible_routes':data['route_visible'],'sent':0,'output':str(dest)},ensure_ascii=False))

if __name__=='__main__':main()
