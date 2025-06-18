import argparse

from prettybib.util import get_entry_from_doi, load_library, merge_entries, normalize_entry, remove_fields_from_entry, write_entries_to_file

if __name__ == "__main__":
    # Create an argument parser
    parser = argparse.ArgumentParser()

    # Add an argument for the filename
    parser.add_argument("filename", help="Path to the input file")

    # Parse the arguments
    args = parser.parse_args()

    # Access the filename from the parsed arguments
    filename = args.filename
    library = load_library(filename)

    new_library_entries = []
    for entry in library.entries:
        print(f"Processing entry {entry.key} ({entry.entry_type})")

        if "doi" in entry:
            doi = entry["doi"]
            new_entry = get_entry_from_doi(doi)
            if new_entry is not None:
                merged_entry = merge_entries(entry, new_entry)
                new_library_entries.append(merged_entry)
            else:
                new_library_entries.append(normalize_entry(entry))
        else:
            print("No DOI found, using existing entry")
            new_library_entries.append(normalize_entry(entry))

    disallowed_fields = ["file", "note", "annotation",
                         "abstract", "keywords", "language", "editor", "copyright"]
    per_type_disallowed_fields = {
        "article": ["url", "urldate"],
        "inproceedings": ["url", "urldate"],
    }

    for entry in new_library_entries:
        keys_to_delete = disallowed_fields
        if entry.entry_type in per_type_disallowed_fields:
            keys_to_delete += per_type_disallowed_fields[entry.entry_type]

        remove_fields_from_entry(entry, keys_to_delete)

    output_filename = f"{filename}.out"
    write_entries_to_file(new_library_entries, output_filename)
