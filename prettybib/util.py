import bibtexparser.middlewares
import requests
import bibtexparser
from bibtexparser.model import Entry, Field


def get_entry_from_doi(doi):
    try:
        request_url = f"https://doi.org/{doi}"
        headers = {
            "Accept": "application/x-bibtex; charset=utf-8"
        }
        response = requests.get(request_url, headers=headers)
        temp_lib = bibtexparser.parse_string(response.text)
        return temp_lib.entries[0]
    except Exception as e:
        print(f"Failed to get entry from DOI: {doi}")
        return None


def read_file(filename):
    with open(filename, "r", encoding='utf8') as file:
        return file.read()


def print_library(library):
    for entry in library.entries:
        print(entry)


def load_library(filename):
    contents = read_file(filename)
    library = bibtexparser.parse_string(contents)

    if len(library.failed_blocks) > 0:
        print("Failed blocks:")
        for block in library.failed_blocks:
            print(block)
        exit()

    return library


def remove_fields_from_entry(entry, fields):
    for field in fields:
        if field in entry:
            entry.pop(field)


def write_entries_to_file(entries, filename):
    new_library = bibtexparser.Library(entries)

    # Write the modified library to a new file
    bibtex_format = bibtexparser.BibtexFormat()
    bibtex_format.indent = '  '
    bibtex_format.block_separator = '\n\n'
    bib_str = bibtexparser.write_string(
        new_library, bibtex_format=bibtex_format,
        # unparse_stack=[
        #     bibtexparser.middlewares.MonthIntMiddleware()],
        prepend_middleware=[
            bibtexparser.middlewares.MonthIntMiddleware()]
    )

    with open(filename, "w", encoding='utf8') as file:
        file.write(bib_str)
    print(f"Output file '{filename}' created successfully.")


def get_doi_from_title(title):
    request_url = f"https://api.crossref.org/works?query.title={title}"
    headers = {
        "Accept": "application/json; charset=utf-8"
    }
    response = requests.get(request_url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to get metadata from title: {title}")
        return None

    data = response.json()
    if 'message' in data and 'items' in data['message'] and len(data['message']['items']) > 0:
        found_title = data['message']['items'][0].get('title', [])[0]
        print(f"Found DOI, for title: {found_title}")
        return data['message']['items'][0].get('DOI', None)
    else:
        print(f"No DOI found for title: {title}")
        return None


def coalesce(*args):
    for arg in args:
        if arg is not None:
            return arg
    return None


def normalize_field(field: Field) -> Field:
    key = field.key.lower()
    value = field.value
    if isinstance(value, str):
        value = value.replace("’", "'")

    return Field(key, value)


def normalize_entry(entry: Entry) -> Entry:
    entry_type = entry.entry_type.lower()
    entry_key = entry.key

    fields: list[Field] = []

    for field in entry.fields:
        fields.append(normalize_field(field))

    return Entry(entry_type, entry_key, fields)


def merge_title(title: str, doi_title: str) -> str:
    title_has_braces = "{" in title and "}" in title
    doi_title_has_braces = "{" in doi_title and "}" in doi_title
    n1 = title.replace("{", "").replace("}", "")
    n2 = doi_title.replace("{", "").replace("}", "")

    if n1.lower() == n2.lower():
        # Return the one with braces (most correct)
        if title_has_braces:
            return title
        if doi_title_has_braces:
            return doi_title
        return doi_title

    return doi_title


def normalize_month(_month: str) -> str:
    month = _month.lower().strip()
    month_map = {
        "jan": "1", "january": "1",
        "feb": "2", "february": "2",
        "mar": "3", "march": "3",
        "apr": "4", "april": "4",
        "may": "5",
        "jun": "6", "june": "6",
        "jul": "7", "july": "7",
        "aug": "8", "august": "8",
        "sep": "9", "september": "9",
        "oct": "10", "october": "10",
        "nov": "11", "november": "11",
        "dec": "12", "december": "12"
    }
    print(f"{month} -> {month_map.get(month, month)}")
    return month_map.get(month, month)


def merge_fields(field: Field, doi_field: Field) -> Field:
    key = field.key
    value = doi_field.value

    if field.value == doi_field.value:
        return field

    # Special handling
    if key == "title" or key == "booktitle":
        value = merge_title(field.value, doi_field.value)
    elif key == "doi":
        value = doi_field.value
    # elif key == "month":
        # value = normalize_month(value)

    # print(f"Field '{field.key}' has conflicting values: '{
    #     field.value}' -> '{doi_field.value}', using '{value}'")
    return Field(key, value)


def merge_entries(entry: Entry, doi_entry: Entry) -> Entry:
    entry_type = coalesce(doi_entry.entry_type, entry.entry_type)
    if doi_entry.entry_type != entry.entry_type:
        print(f"!!! Entry type differ: '{
              entry.entry_type}' -> '{doi_entry.entry_type}', using '{entry_type}'")
    entry_key = entry.key

    fields: list[Field] = []

    existing_fields = [normalize_field(field) for field in entry.fields]
    doi_fields = [normalize_field(field) for field in doi_entry.fields]

    new_field_lookup = {field.key: field for field in doi_fields}
    existing_field_lookup = {field.key: field for field in existing_fields}

    new_field_set = set(new_field_lookup.keys())
    existing_field_set = set(existing_field_lookup.keys())

    for field in doi_fields:
        if field.key in existing_field_set:
            existing_field = existing_field_lookup[field.key]
            fields.append(merge_fields(existing_field, field))
        else:
            fields.append(field)

    for field in existing_fields:
        if field.key not in new_field_set:
            # if field.key not in ["doi"]:
            #     print(f"Field '{field.key}' not found in new entry, keeping existing value {
            #         field.value}")
            fields.append(field)

    created_entry = Entry(entry_type, entry_key, fields)
    return created_entry
