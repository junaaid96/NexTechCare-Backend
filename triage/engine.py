"""AI Issue Triage: Groq LLM with a rule-based fallback.

Input: free-text problem description. Output: category, urgency, summary,
DIY steps and IDs of the best matching approved services.
"""
import json
import logging
import re
import urllib.request

from django.conf import settings

from services.models import Service, CATEGORY_CHOICES

log = logging.getLogger(__name__)
GROQ_URL = 'https://api.groq.com/openai/v1/chat/completions'
CATEGORY_KEYS = [k for k, _ in CATEGORY_CHOICES]

RULES = {
    'data_recovery': ['deleted', 'recover', 'lost file', 'corrupt', 'formatted', 'hard drive fail', 'ssd dead', 'raid', 'backup missing'],
    'cybersecurity': ['virus', 'malware', 'hacked', 'ransomware', 'phishing', 'password leak', 'suspicious', 'breach', 'antivirus', '2fa'],
    'networking': ['wifi', 'wi-fi', 'router', 'internet', 'network', 'slow connection', 'lan', 'vpn', 'dns', 'ethernet', 'no signal'],
    'hardware': ['screen', 'battery', 'keyboard', 'overheat', 'fan', 'not turning on', 'won\'t boot', 'broken', 'printer', 'ram', 'motherboard', 'charging', 'beep'],
    'cloud_backup': ['cloud', 'backup', 'google drive', 'onedrive', 'icloud', 'aws', 'sync', 'storage full'],
    'device_setup': ['new laptop', 'new phone', 'setup', 'set up', 'install windows', 'migrate', 'transfer data', 'configure'],
    'smart_home': ['smart home', 'alexa', 'google home', 'cctv', 'camera', 'smart tv', 'iot', 'smart bulb', 'doorbell'],
    'consultancy': ['advice', 'consult', 'plan', 'which laptop', 'architecture', 'it strategy', 'audit', 'quote', 'recommend'],
    'remote_support': ['remote', 'quick help', 'anydesk', 'teamviewer'],
    'software': ['error', 'crash', 'install', 'update', 'office', 'excel', 'app', 'software', 'bug', 'license', 'blue screen', 'bsod', 'slow'],
}
DIY = {
    'data_recovery': ['Stop using the affected drive immediately to avoid overwriting data.', 'Check Recycle Bin / Trash and any cloud version history.', 'Do not run disk repair tools on a failing drive.'],
    'cybersecurity': ['Disconnect the device from the internet.', 'Change important passwords from a different, clean device.', 'Enable two-factor authentication on email and banking.'],
    'networking': ['Restart the router and modem (unplug 30 seconds).', 'Test with a cable or another device to isolate the problem.', 'Forget and re-join the Wi-Fi network.'],
    'hardware': ['Check power cable, charger and outlet.', 'Hold the power button 30 seconds, then try again.', 'Note any beeps, lights or error messages for the engineer.'],
    'cloud_backup': ['Check your storage quota and sync status.', 'Sign out and back in to the sync client.', 'Make a local copy of critical files now.'],
    'device_setup': ['Back up the old device first.', 'Keep account passwords and license keys ready.', 'Update the new device to the latest OS.'],
    'smart_home': ['Power-cycle the device and hub.', 'Make sure the device is on the 2.4 GHz Wi-Fi band.', 'Update the companion app.'],
    'consultancy': ['List your goals, budget and timeline.', 'Inventory current devices and software.', 'Note any compliance or security requirements.'],
    'remote_support': ['Install a trusted remote tool only when the engineer asks.', 'Save your work and close sensitive apps.', 'Never share passwords in chat.'],
    'software': ['Restart the app and the computer.', 'Install pending updates.', 'Note the exact error message or take a screenshot.'],
}
URGENT = ['urgent', 'asap', 'immediately', 'emergency', 'hacked', 'ransomware', 'business down', 'deadline', 'server down', 'all data']


def _services_catalog(limit=40):
    return list(Service.objects.filter(admin_approved=True)
                .select_related('engineer__user')
                .values('id', 'name', 'category', 'description', 'price')[:limit])


def rule_based(text):
    t = text.lower()
    scores = {k: sum(1 for w in words if w in t) for k, words in RULES.items()}
    category = max(scores, key=scores.get) if any(scores.values()) else 'software'
    urgency = 'high' if any(w in t for w in URGENT) else ('normal' if len(t) > 40 else 'low')
    catalog = _services_catalog()
    tokens = set(re.findall(r'[a-z]{4,}', t))

    def rank(s):
        overlap = len(tokens & set(re.findall(r'[a-z]{4,}', (s['name'] + ' ' + s['description']).lower())))
        return (s['category'] == category) * 5 + overlap

    ranked = sorted(catalog, key=rank, reverse=True)
    ids = [s['id'] for s in ranked if rank(s) > 0][:3]
    label = dict(CATEGORY_CHOICES)[category]
    return {
        'category': category,
        'category_label': label,
        'urgency': urgency,
        'summary': f'Looks like a {label.lower()} issue. Try the quick checks below, or book a verified engineer.',
        'diy_steps': DIY[category],
        'recommended_service_ids': ids,
        'source': 'rules',
    }


def _call_groq(text, catalog):
    sys = (
        'You are NexTechCare triage, an IT support dispatcher. Classify the user problem and recommend services. '
        f'Allowed categories: {", ".join(CATEGORY_KEYS)}. Urgency: low|normal|high|critical. '
        'Reply ONLY with JSON: {"category": str, "urgency": str, "summary": str (max 2 sentences), '
        '"diy_steps": [3 short safe steps], "recommended_service_ids": [up to 3 ids from catalog]}. '
        'Never ask for passwords. If the request is not about technology support, use category "consultancy".'
    )
    cat = [{'id': s['id'], 'name': s['name'], 'category': s['category'], 'description': s['description'][:160]} for s in catalog]
    body = {
        'model': settings.GROQ_MODEL,
        'messages': [
            {'role': 'system', 'content': sys},
            {'role': 'user', 'content': f'Catalog: {json.dumps(cat)}\n\nProblem: {text[:2000]}'},
        ],
        'temperature': 0.2,
        'max_tokens': 700,
        'response_format': {'type': 'json_object'},
    }
    req = urllib.request.Request(GROQ_URL, data=json.dumps(body).encode(), method='POST', headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {settings.GROQ_API_KEY}',
        'User-Agent': 'nextechcare-triage/1.0',
    })
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read())
    content = data['choices'][0]['message']['content']
    m = re.search(r'\{.*\}', content, re.S)
    return json.loads(m.group(0) if m else content)


def triage(text):
    text = (text or '').strip()
    if not settings.GROQ_API_KEY:
        return rule_based(text)
    try:
        catalog = _services_catalog()
        out = _call_groq(text, catalog)
        valid_ids = {s['id'] for s in catalog}
        category = out.get('category') if out.get('category') in CATEGORY_KEYS else rule_based(text)['category']
        urgency = out.get('urgency') if out.get('urgency') in ['low', 'normal', 'high', 'critical'] else 'normal'
        ids = [i for i in out.get('recommended_service_ids', []) if isinstance(i, int) and i in valid_ids][:3]
        if not ids:
            ids = rule_based(text)['recommended_service_ids']
        steps = [str(s)[:200] for s in out.get('diy_steps', [])][:4] or DIY[category]
        return {
            'category': category,
            'category_label': dict(CATEGORY_CHOICES)[category],
            'urgency': urgency,
            'summary': str(out.get('summary', ''))[:400],
            'diy_steps': steps,
            'recommended_service_ids': ids,
            'source': 'ai',
        }
    except Exception as e:  # network, rate limit, bad JSON -> graceful fallback
        log.warning('Groq triage failed, using rules: %s', type(e).__name__)
        return rule_based(text)
