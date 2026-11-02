import csv,io
from django.http import HttpResponse
FIELDS=['name','quantity','unit','category','location','expiry_date','low_stock_at','notes']
def spreadsheet_safe(value):
    text='' if value is None else str(value)
    return "'"+text if text.lstrip().startswith(('=','+','-','@')) or text.startswith(('\t','\r','\n')) else text
def csv_response(filename,headers,rows):
    response=HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition']=f'attachment; filename="{filename}"'
    response.write('\ufeff')
    writer=csv.writer(response);writer.writerow(headers)
    for row in rows:writer.writerow([spreadsheet_safe(value) for value in row])
    return response
