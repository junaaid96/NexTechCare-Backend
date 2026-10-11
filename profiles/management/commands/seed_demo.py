"""Create (or reset) the NexTechCare demo: demo users, services, bookings, reviews.

Safe to run any time: it only deletes and re-creates rows owned by `demo_*`
users, plus demo contact messages and activity entries.
"""
import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from activities.models import Activity
from bookings.models import Booking, BookingEvent
from contact.models import ContactText
from profiles.demo import DEMO_PREFIX
from profiles.models import AdminProfile, CustomerProfile, EngineerProfile, User
from reviews.models import Review
from services.models import Service

ENGINEERS = [
    ('demo_engineer', 'Rafi', 'Ahmed', 'Networking, Wi-Fi, CCTV, Ubiquiti', True),
    ('demo_eng_nadia', 'Nadia', 'Karim', 'Data recovery, RAID, forensics', True),
    ('demo_eng_tanvir', 'Tanvir', 'Hasan', 'Windows, macOS, Office 365, printers', False),
    ('demo_eng_sara', 'Sara', 'Islam', 'Cybersecurity, cloud backup, IT audits', True),
]
CUSTOMERS = [
    ('demo_customer', 'Mina', 'Rahman', 'Product designer'),
    ('demo_cust_arif', 'Arif', 'Chowdhury', 'Shop owner'),
    ('demo_cust_lisa', 'Lisa', 'Wong', 'Accountant'),
]
# (name, category, engineer idx, price, hours, sla, remote, description)
SERVICES = [
    ('Mesh Wi-Fi Dead-Zone Fix', 'networking', 0, 49, 2, 8, False, 'Signal survey, mesh setup and channel tuning so every room gets full-speed Wi-Fi.'),
    ('Office Network & VPN Setup', 'networking', 0, 180, 6, 48, True, 'Router, VLANs, firewall rules and secure remote VPN for small offices.'),
    ('Smart CCTV Installation', 'smart_home', 0, 140, 5, 72, False, 'Camera placement, NVR setup, motion alerts and phone viewing.'),
    ('Deleted File & SSD Recovery', 'data_recovery', 1, 120, 4, 48, True, 'Recover deleted or formatted files from SSD, HDD, SD cards and USB drives.'),
    ('RAID & NAS Rescue', 'data_recovery', 1, 350, 8, 72, False, 'Rebuild failed RAID arrays and recover NAS volumes safely, with a file report.'),
    ('Windows Speed-Up & Repair', 'software', 2, 35, 1, 24, True, 'Malware scan, startup cleanup, updates and driver fixes for a slow PC.'),
    ('New Laptop Setup & Data Transfer', 'device_setup', 2, 60, 2, 24, True, 'Unbox, update, migrate your data, install apps and set up backups.'),
    ('Printer & Scanner Repair', 'hardware', 2, 45, 2, 24, False, 'Fix paper jams, driver issues and network printing.'),
    ('15-Minute Remote Fix', 'remote_support', 2, 15, 1, 4, True, 'Quick secure screen-share session for small software problems.'),
    ('Malware & Ransomware Cleanup', 'cybersecurity', 3, 90, 3, 6, True, 'Contain, clean and harden your devices after an infection or a hack.'),
    ('Google Workspace Backup Plan', 'cloud_backup', 3, 150, 4, 48, True, 'Automated cloud backup with restore tests for your whole team.'),
    ('IT Audit for Startups', 'consultancy', 3, 250, 6, 96, True, 'Security, licensing and infrastructure review with a written action plan.'),
]
PENDING = [
    ('Home Office Ergonomic Tech Setup', 'device_setup', 2, 55, 2, 24, False, 'Monitor arms, docks, webcams and lighting, set up and cable-managed.'),
    ('Microsoft 365 Security Hardening', 'cybersecurity', 3, 120, 3, 24, True, 'MFA, conditional access, phishing protection and admin alerts.'),
]
ISSUES = {
    'networking': 'Wi-Fi drops every evening in the back rooms; video calls freeze.',
    'data_recovery': 'External drive stopped mounting; it holds 3 years of client photos.',
    'software': 'Laptop takes 5 minutes to boot and Outlook keeps crashing.',
    'device_setup': 'New MacBook arrived, need everything moved from the old Windows PC.',
    'hardware': 'Office printer prints blank pages after the last update.',
    'remote_support': 'Excel macros stopped working after the update.',
    'cybersecurity': 'Pop-up says files are encrypted; some documents will not open.',
    'cloud_backup': 'We have no backup for our shared drives and want one before audit season.',
    'smart_home': 'Want 4 cameras around the shop with phone alerts.',
    'consultancy': 'Planning IT for a 12-person startup office opening next month.',
}
COMMENTS = ['Fast, friendly and explained everything.', 'Fixed in one session. Great communication!',
            'Very professional, would book again.', 'Arrived on time and left everything tidy.',
            'Clear updates on the tracker the whole way.']


class Command(BaseCommand):
    help = 'Create or reset the demo accounts and data.'

    @transaction.atomic
    def handle(self, *args, **opts):
        rnd = random.Random(42)
        now = timezone.now()
        User.objects.filter(username__startswith=DEMO_PREFIX).delete()  # cascades to profiles/services/bookings/reviews
        ContactText.objects.filter(email__endswith='@demo.nextechcare.app').delete()
        Activity.objects.filter(name__icontains='(demo)').delete()

        def user(username, t, fn, ln):
            u = User(username=username, first_name=fn, last_name=ln, email=f'{username}@demo.nextechcare.app', user_type=t)
            u.set_unusable_password()  # demo accounts sign in only via /profiles/demo-login/
            u.save()
            return u

        AdminProfile.objects.create(user=user('demo_admin', 'A', 'Demo', 'Admin'), task='Platform operations')
        engs = [EngineerProfile.objects.create(user=user(u, 'E', fn, ln), skills=sk, verified=v,
                                               experience='8+ years supporting homes and small businesses.')
                for u, fn, ln, sk, v in ENGINEERS]
        custs = [CustomerProfile.objects.create(user=user(u, 'C', fn, ln), occupation=o) for u, fn, ln, o in CUSTOMERS]

        def svc(row, approved):
            n, c, e, p, h, sla, remote, desc = row
            return Service.objects.create(name=n, category=c, engineer=engs[e], price=p, duration=h, sla_hours=sla,
                                          is_remote=remote, description=desc, admin_approved=approved)

        services = [svc(r, True) for r in SERVICES]
        for r in PENDING:
            svc(r, False)

        def event(b, st, actor, note, at):
            ev = BookingEvent.objects.create(booking=b, status=st, actor=actor, note=note)
            BookingEvent.objects.filter(pk=ev.pk).update(created_at=at)

        # History: resolved / cancelled bookings over the last 3 weeks
        for i in range(30):
            s = rnd.choice(services)
            c = rnd.choice(custs)
            created = now - timedelta(days=rnd.randint(1, 20), hours=rnd.randint(0, 20))
            status = rnd.choice(['resolved'] * 6 + ['cancelled'])
            b = Booking.objects.create(service=s, customer=c, status=status, priority=rnd.choice(['normal', 'normal', 'high', 'low']),
                                       issue=ISSUES[s.category])
            Booking.objects.filter(pk=b.pk).update(created_at=created, sla_due_at=created + timedelta(hours=s.sla_hours))
            event(b, 'requested', c.user, 'Booking requested', created)
            upd = {}
            if status == 'resolved':
                acc = created + timedelta(hours=rnd.uniform(0.2, 3))
                start = acc + timedelta(hours=rnd.uniform(0.5, 2))
                res = start + timedelta(hours=rnd.uniform(0.5, s.sla_hours * (1.1 if rnd.random() < 0.12 else 0.7)))
                upd = dict(accepted_at=acc, started_at=start, resolved_at=res)
                event(b, 'accepted', s.engineer.user, 'Accepted. I will be in touch shortly.', acc)
                event(b, 'in_progress', s.engineer.user, 'Work started.', start)
                event(b, 'resolved', s.engineer.user, 'Fixed and tested with the customer.', res)
                s.customer.add(c)
                if not Review.objects.filter(customer=c, service=s).exists() and rnd.random() < 0.8:
                    r = Review.objects.create(customer=c, service=s, rating=rnd.choice([8, 9, 10, 10, 10]), comment=rnd.choice(COMMENTS))
                    Review.objects.filter(pk=r.pk).update(created_at=res + timedelta(hours=2))
            else:
                event(b, 'cancelled', c.user, 'Fixed it myself, thanks!', created + timedelta(hours=1))
            Booking.objects.filter(pk=b.pk).update(**upd)

        # Live bookings for the demo customer / engineer, one in each tracker state
        mina, rafi = custs[0], engs[0]

        def live(service, cust, status, hours_ago, prio, issue, triage, notes):
            created = now - timedelta(hours=hours_ago)
            b = Booking.objects.create(service=service, customer=cust, status=status, priority=prio, issue=issue, triage_summary=triage)
            upd = dict(created_at=created, sla_due_at=created + timedelta(hours=service.sla_hours))
            event(b, 'requested', cust.user, 'Booking requested', created)
            t = created
            for st, note in notes:
                t = t + timedelta(minutes=25)
                upd[{'accepted': 'accepted_at', 'in_progress': 'started_at', 'resolved': 'resolved_at'}[st]] = t
                event(b, st, service.engineer.user, note, t)
            Booking.objects.filter(pk=b.pk).update(**upd)
            service.customer.add(cust)

        live(services[0], mina, 'in_progress', 3, 'high',
             'Wi-Fi dies in the bedroom and home office; router is downstairs. Two laptops and a TV affected.',
             'Likely a coverage problem from a single router; a mesh system or extra access point should fix it.',
             [('accepted', 'Accepted. I will bring a 3-node mesh kit.'), ('in_progress', 'On site, running a signal survey now.')])
        live(services[2], mina, 'accepted', 1, 'normal', 'Want 4 cameras around the shop with phone alerts.', '',
             [('accepted', 'Booked for tomorrow 10:00. Please keep the NVR spot near a power outlet.')])
        live(services[1], custs[1], 'requested', 0.5, 'high', 'Staff cannot connect to the office VPN from home since Monday.',
             'VPN authentication or certificate problem; check client config and firewall rules.', [])
        live(services[0], custs[2], 'requested', 7, 'critical', 'Whole office Wi-Fi is down, card machine offline.', '', [])
        live(services[9], mina, 'resolved', 30, 'critical', 'Pop-up says files are encrypted.', 'Possible ransomware: isolate the device first.',
             [('accepted', 'On it now.'), ('in_progress', 'Device isolated, scanning.'), ('resolved', 'Cleaned, files restored from backup, MFA enabled.')])

        ContactText.objects.create(name='Hasan Ali', email='hasan@demo.nextechcare.app', subject='Monthly support for 20 PCs',
                                   message='Hi, we would like a monthly support plan for our office. Can you share pricing?')
        ContactText.objects.create(name='Priya Sen', email='priya@demo.nextechcare.app', subject='Engineer verification',
                                   message='How long does engineer verification usually take?')
        for txt in ['Rafi Ahmed accepted a booking (demo)', 'Sara Islam submitted "Microsoft 365 Security Hardening" for approval (demo)',
                    'Mina Rahman reviewed Malware & Ransomware Cleanup (demo)', 'Demo data was reset (demo)']:
            Activity.objects.create(name=txt)
        self.stdout.write(self.style.SUCCESS(f'Demo ready: {Booking.objects.filter(customer__user__username__startswith=DEMO_PREFIX).count()} bookings'))
