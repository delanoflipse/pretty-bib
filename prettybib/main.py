import argparse

from prettybib.log import log_info, log_warn
from prettybib.resolvers import resolve, resolve_from_crossref, resolve_from_dblp, resolve_from_doi
from prettybib.util import load_library, merge_entries, normalize_entry, read_file, remove_fields_from_entry, write_entries_to_file

# --- HARDCODED CONFIGURATION ---
# ! Change as needed !

# Resolvers take a BibTeX entry and return a resolved BibTeX entry or None if not resolved
# The are called in order, so change it to your liking
doi_resolvers = [
    resolve_from_dblp,
    resolve_from_doi,
    resolve_from_crossref,
]

# Keys that should be ignored
disallowed_fields = [
    "file",
    "note",
    "annotation",
    "abstract",
    "keywords",
    "language",
    "editor",
    "copyright",
    "biburl",
    "bibsource",
    "timestamp",
    "eprinttype",
    "eprint"
]

# Keys that are disallowed per entry type
per_type_disallowed_fields = {
    "article": [
        "url",
        "urldate",
        "isbn",
        "url"
    ],
    "inproceedings": [
        "url",
        "urldate",
        "isbn",
        "url",
        "address"
    ],
}

# --- Start of the main script ---


def run_script():
    # Create an argument parser
    parser = argparse.ArgumentParser()
    # Add an argument for the filename (required positional argument)
    parser.add_argument(
        "filename", help="Path to the input file")

    # Parse the arguments
    args = parser.parse_args()

    # Access the filename from the parsed arguments
    filename = args.filename
    file_contents = read_file(filename)

    # Load the library from the file contents
    library = load_library(file_contents)

    # For each entry, either resolve it or keep the original entry
    entries = []
    for entry in library.entries:
        log_info(f"Processing entry {entry.key} ({entry.entry_type})")
        resolved_entry = resolve(entry, doi_resolvers)
        if resolved_entry is None:
            log_warn(f"Failed to resolve {entry.key}, keeping original entry")
            entries.append(entry)
            continue

        # We need to merge the fields.
        # We assume the resolved entry has more complete information
        merged_entry = merge_entries(entry, resolved_entry)
        entries.append(merged_entry)

    # Normalize entries
    entries = [normalize_entry(entry) for entry in entries]

    # Remove disallowed fields
    for entry in entries:
        # determine which fields to delete
        keys_to_delete = disallowed_fields

        if entry.entry_type in per_type_disallowed_fields:
            keys_to_delete += per_type_disallowed_fields[entry.entry_type]

        if "issn" in entry and "doi" in entry:
            keys_to_delete.append("issn")

        remove_fields_from_entry(entry, keys_to_delete)

    # Write the entries to a file
    if filename.endswith(".bib"):
        output_filename = filename[:-4] + ".out.bib"
    else:
        output_filename = f"{filename}.out"

    write_entries_to_file(entries, output_filename)


if __name__ == "__main__":
    run_script()
