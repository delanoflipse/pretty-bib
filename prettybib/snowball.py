import argparse

import requests

from reference_generator.util import get_doi_from_title, get_entry_from_doi, load_library, write_entries_to_file
import json
      
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
  
  metadata_list = []
  doi_set = set()
  for entry in library.entries:
    print(f"Processing entry {entry.key} ({entry.entry_type})")
    if not "doi" in entry and not "DOI" in entry:
      continue
    
    doi = entry.get("doi") or entry.get("DOI")
    print(f"DOI: {doi.value}")
    
    request_url = f"https://api.crossref.org/works/{doi.value}"
    headers = {
      "Accept": "application/json; charset=utf-8"
    }
    response = requests.get(request_url, headers=headers)
    if response.status_code != 200:
      print(f"Failed to get entry from DOI: {doi.value}")
      continue
    
    data = response.json()
    
    print(f"Referenced by: {data['message']['is-referenced-by-count']}")
    print(f"Reference count: {len(data['message']['reference'])}")
    
    for reference in data["message"]["reference"]:
      doi = reference.get("DOI")
      if "DOI" not in reference:
        title = reference.get("article-title")
        if title is None:
          continue
        
        print(f"Looking up doi for: {title}")
        doi = get_doi_from_title(title)
        if doi is not None:
          print(f"Found doi: {doi}!")
        
        
      if doi is None:
        continue
        
      if doi in doi_set:
        continue
      doi_set.add(doi)
      metadata_list.append(reference)
    
  snowball_entries = []
  for doi in doi_set:
    entry = get_entry_from_doi(doi)
    snowball_entries.append(entry)
    
  
  output_filename = f"{filename}.json"
  with open(output_filename, 'w') as outfile:
    json.dump(metadata_list, outfile, indent=4)
  
  write_entries_to_file(snowball_entries, f"{filename}.snowball.bib")
  print(f"Snowballed {len(metadata_list)} entries")
