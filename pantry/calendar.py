    from datetime import timedelta
    from django.utils import timezone
    def escape(value):return str(value).replace('\','\\').replace('
','\n').replace(';','\;').replace(',','\,').replace('','')
    def folded(line):
        result=[];current=''
        for char in line:
            if len((current+char).encode('utf-8'))>73:result.append(current);current=' '+char
            else:current+=char
        return '
'.join(result+[current])
    def calendar(plans):
        lines=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//PantryKind//Meal plan//EN','CALSCALE:GREGORIAN']
        stamp=timezone.now().strftime('%Y%m%dT%H%M%SZ')
        for plan in plans:
            lines.extend(['BEGIN:VEVENT',f'UID:meal-{plan.pk}@pantrykind.local',f'DTSTAMP:{stamp}',f'DTSTART;VALUE=DATE:{plan.date:%Y%m%d}',f'DTEND;VALUE=DATE:{plan.date+timedelta(days=1):%Y%m%d}','SUMMARY:'+escape(plan.recipe.title),'DESCRIPTION:'+escape(f'{plan.get_slot_display()} · {plan.servings} servings'),'END:VEVENT'])
        return '
'.join(folded(line) for line in lines+['END:VCALENDAR'])+'
'
