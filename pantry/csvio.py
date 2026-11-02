import csv, io
from django.http import HttpResponse

FIELDS = [
    "name",
    "quantity",
    "unit",
    "category",
    "location",
    "expiry_date",
    "low_stock_at",
    "notes",
]


def spreadsheet_safe(value):
    text = "" if value is None else str(value)
    return (
        "'" + text
        if text.lstrip().startswith(("=", "+", "-", "@")) or text.startswith(("\t", "\r", "\n"))
        else text
    )


def csv_response(filename, headers, rows):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow(headers)
    for row in rows:
        writer.writerow([spreadsheet_safe(value) for value in row])
    return response


from pantry.forms import ItemForm


def parse_inventory_csv(data):
    if len(data) > 1024 * 1024:
        raise ValueError("Please use a CSV file smaller than 1 MB.")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ValueError("Use a UTF-8 encoded CSV file.")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise ValueError("CSV headers must be present and unique.")
    if not {"name", "quantity", "unit"}.issubset(reader.fieldnames):
        raise ValueError("Required columns: name, quantity, unit.")
    if set(reader.fieldnames) - set(FIELDS):
        raise ValueError("Unknown columns. Download a pantry export to use as a template.")
    rows = []
    for number, row in enumerate(reader, start=2):
        if number > 501:
            raise ValueError("Import at most 500 food batches at a time.")
        if None in row:
            raise ValueError(f"Line {number}: too many columns.")
        clean = {field: (row.get(field) or "").strip() for field in FIELDS}
        for field in ["name", "notes"]:
            if clean[field].startswith("'") and clean[field][1:].lstrip().startswith(
                ("=", "+", "-", "@")
            ):
                clean[field] = clean[field][1:]
        clean["category"] = clean["category"] or "other"
        clean["location"] = clean["location"] or "pantry"
        clean["low_stock_at"] = clean["low_stock_at"] or "0"
        form = ItemForm(clean)
        if not form.is_valid():
            errors = "; ".join(
                f"{field}: {', '.join(messages)}" for field, messages in form.errors.items()
            )
            raise ValueError(f"Line {number}: {errors}")
        rows.append(clean)
    if not rows:
        raise ValueError("The file has no food batches.")
    return rows
