from django.test import TestCase
from django.utils import timezone
from pantry.tests.factories import kitchen
from pantry.models import MealPlan,Recipe
from pantry.calendar import escape,folded
class CalendarTests(TestCase):
    def test_export_is_scoped_and_well_formed(self):
        user,home=kitchen();_,other=kitchen('other');self.client.force_login(user)
        for house,title in [(home,'Rice, beans'),(other,'Private meal')]:
            recipe=Recipe.objects.create(household=house,title=title,instructions='Cook')
            MealPlan.objects.create(household=house,recipe=recipe,date=timezone.localdate())
        r=self.client.get('/plan/calendar.ics')
        self.assertEqual(r.status_code,200);self.assertIn(b'Rice\\, beans',r.content);self.assertNotIn(b'Private meal',r.content)
        self.assertTrue(r.content.endswith(b'END:VCALENDAR\r\n'))
    def test_unicode_lines_are_folded_by_byte_count(self):
        self.assertTrue(all(len(line.encode())<=75 for line in folded('食材'*80).split('\r\n')))
    def test_escaped_text_cannot_inject_properties(self):
        value=escape('Rice\r\nATTENDEE:evil');self.assertNotIn('\r',value);self.assertNotIn('\n',value)
