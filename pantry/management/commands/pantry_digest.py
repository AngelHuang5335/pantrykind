from datetime import timedelta
from django.core.management.base import BaseCommand,CommandError
from django.utils import timezone
from pantry.models import Household
class Command(BaseCommand):
    help='Print date reminders for a household; suitable for your own scheduler or email wrapper.'
    def add_arguments(self,parser):parser.add_argument('household_id',type=int)
    def handle(self,*args,**options):
        try:home=Household.objects.get(pk=options['household_id'])
        except Household.DoesNotExist:raise CommandError('Household not found.')
        with timezone.override(home.timezone_name):
            today=timezone.localdate()
            items=home.items.filter(archived=False,quantity__gt=0,expiry_date__lte=today+timedelta(days=home.reminder_days)).order_by('expiry_date','name')
            self.stdout.write(f'PantryKind · {home.name} · {today}')
            for item in items:self.stdout.write(f'{item.expiry_date}: {item.name} ({item.quantity} {item.unit}) — {item.expiry_status}')
            if not items.exists():self.stdout.write('No upcoming label dates.')
