import argparse
from typing import Callable

from prettybib.log import log_info, log_success, log_warn
from prettybib.resolvers import resolve_from_crossref, resolve_from_dblp, resolve_from_doi
from prettybib.util import load_library, merge_entries, normalize_entry, read_file, remove_fields_from_entry, write_entries_to_file

doi_resolvers = [
    resolve_from_dblp,
    resolve_from_doi,
    resolve_from_crossref,
]


def resolve(entry) -> dict:
    """
    Resolve a DOI to a BibTeX entry using the available resolvers.
    """
    for resolver in doi_resolvers:
        resolved_entry = resolver(entry)
        if resolved_entry is not None:
            log_success(f"Resolved using {resolver.__name__}")
            return resolved_entry
    return None


if __name__ == "__main__":
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
    library = load_library(file_contents)

    entries = []
    for entry in library.entries:
        log_info(f"Processing entry {entry.key} ({entry.entry_type})")
        resolved_entry = resolve(entry)
        if resolved_entry is None:
            log_warn(f"Failed to resolve {entry.key}, keeping original entry")
            print("")
            entries.append(entry)
            continue

        merged_entry = merge_entries(entry, resolved_entry)
        entries.append(merged_entry)
        print("")

    # Normalize entries
    entries = [normalize_entry(entry) for entry in entries]

    disallowed_fields = ["file", "note", "annotation",
                         "abstract", "keywords", "language", "editor", "copyright", "biburl", "bibsource", "timestamp", "eprinttype", "eprint"]
    per_type_disallowed_fields = {
        "article": ["url", "urldate", "isbn", "url"],
        "inproceedings": ["url", "urldate", "isbn", "url", "address"],
    }

    for entry in entries:
        keys_to_delete = disallowed_fields
        if entry.entry_type in per_type_disallowed_fields:
            keys_to_delete += per_type_disallowed_fields[entry.entry_type]
        if "issn" in entry and "doi" in entry:
            keys_to_delete.append("issn")
        remove_fields_from_entry(entry, keys_to_delete)

    if filename.endswith(".bib"):
        output_filename = filename[:-4] + ".out.bib"
    else:
        output_filename = f"{filename}.out"
    write_entries_to_file(entries, output_filename)
