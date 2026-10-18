"""SJM public application preflight classification.

Read-only form metadata -> authorization requirements. This module neither
handles applicant data nor creates a submission capability.
"""
import re
from urllib.parse import urlparse

ADAPTERS = {
    'freelancer.ypai.ai': 'ypai_colombia',
    'jobs.lever.co': 'lever',
    'jobs.ashbyhq.com': 'ashby',
    'community.transperfect.com': 'transperfect_listing',
    'www.workana.com': 'workana_listing',
    'myvirtualtrainer.co': 'partner_listing',
}
PHONE = re.compile(r'\b(phone|telephone|tel[eé]fono|celular|mobile|whatsapp)\b', re.I)
CV = re.compile(r'\b(cv|resume|r[eé]sum[eé]|curriculum|curr[ií]culo|hoja de vida)\b', re.I)
LEGAL = re.compile(r'\b(consent|consentimiento|privacy|privacidad|terms|t[eé]rminos|policy|pol[ií]tica|data protection|protecci[oó]n de datos|authorization|autorizaci[oó]n)\b', re.I)

def classify_application_form(url, fields, *, challenge=False, form_visible=False):
    """Summarize public labels/types only. Never infer approval or submit."""
    host = urlparse(url).hostname or ''
    adapter = ADAPTERS.get(host, 'unsupported')
    fields = fields if isinstance(fields, list) else []
    inspected = []
    for field in fields[:45]:
        if not isinstance(field, dict):
            continue
        name = str(field.get('name') or '')[:90]
        typ = str(field.get('type') or '').lower()[:32]
        label = str(field.get('label') or '')[:120]
        inspected.append((typ, name + ' ' + label, field.get('required') is True))
    required_phone = any(req and (typ == 'tel' or PHONE.search(name)) for typ, name, req in inspected)
    required_cv = any(req and (typ == 'file' or CV.search(name) or '_systemfield_resume' in name) for typ, name, req in inspected)
    file_upload = any(typ == 'file' for typ, _, _ in inspected)
    legal_consent = any((typ == 'checkbox' or req) and LEGAL.search(name) for typ, name, req in inspected)
    unknown_required_checkbox = any(typ == 'checkbox' and req for typ, _, req in inspected)
    legal_review = bool(legal_consent or unknown_required_checkbox)
    if challenge:
        state = 'requires_human_challenge'
    elif adapter == 'unsupported':
        state = 'unsupported_source'
    elif not form_visible or not inspected:
        state = 'needs_interactive_form_inspection'
    elif required_phone or required_cv or legal_review:
        state = 'needs_specific_authorization'
    else:
        state = 'needs_eligibility_and_terms_review'
    return {
        'adapter': adapter,
        'preflight_state': state,
        'visible_field_count': len(inspected),
        'required_phone': required_phone,
        'required_cv': required_cv,
        'file_upload_present': file_upload,
        'legal_consent_review_required': legal_review,
        'required_approval_scopes': [
            x for x, enabled in (
                ('phone', required_phone),
                ('cv', required_cv),
                ('terms_or_privacy', legal_review),
            ) if enabled
        ],
        'submitted': False,
        'automatic_submission_enabled': False,
    }
