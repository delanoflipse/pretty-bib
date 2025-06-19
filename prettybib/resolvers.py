
import time
from bibtexparser import parse_string
import requests

from prettybib.log import log_success
from prettybib.util import str_equal_ignore_case


def resolve(entry, resolvers) -> dict:
    """
    Resolve a DOI to a BibTeX entry using the available resolvers.
    """
    for resolver in resolvers:
        resolved_entry = resolver(entry)
        if resolved_entry is not None:
            log_success(f"Resolved using {resolver.__name__}")
            return resolved_entry
    return None


def resolve_from_doi(entry):
    if not "doi" in entry or not entry["doi"]:
        return None
    doi = entry["doi"]
    try:
        request_url = f"https://doi.org/{doi}"
        headers = {
            "Accept": "application/x-bibtex; charset=utf-8"
        }
        response = requests.get(request_url, headers=headers)
        temp_lib = parse_string(response.text)
        return temp_lib.entries[0]
    except Exception as e:
        print(f"Failed to get entry from DOI: {doi}")
        return None


def resolve_from_crossref(entry):
    if not "doi" in entry or not entry["doi"]:
        return None
    doi = entry["doi"]

    try:
        request_url = f"https://api.crossref.org/works/{doi}/transform/application/x-bibtex"
        response = requests.get(request_url)
        if response.status_code == 200:
            temp_lib = parse_string(response.text)
            return temp_lib.entries[0]
        else:
            print(
                f"Crossref returned status {response.status_code} for DOI: {doi}")
            return None
    except Exception as e:
        print(f"Failed to get entry from Crossref for DOI: {doi}")
        return None


def get_title(entry) -> str | None:
    if "shorttitle" in entry and entry["shorttitle"]:
        return entry["shorttitle"]
    if "title" in entry and entry["title"]:
        return entry["title"]
    return None


def get_with_backoff(url: str, headers: dict = None) -> requests.Response:
    resp = requests.get(url, headers=headers)
    if resp.status_code == 429:  # Too Many Requests
        # Default to 5 seconds if not specified
        retry_after = int(resp.headers.get("Retry-After", 5))
        print(f"Rate limit exceeded, retrying after {retry_after} seconds...")
        time.sleep(retry_after)
        return get_with_backoff(url)
    elif resp.status_code != 200:
        print(
            f"Failed to fetch data from {url}, status code: {resp.status_code}")
        raise Exception(
            f"Failed to fetch data from {url}, status code: {resp.status_code}")
    return resp


def resolve_from_dblp(entry):
    if not "doi" in entry or not entry["doi"]:
        return None
    doi = entry["doi"]
    # Lookup the publication URI from DBLP for a given DOI
    title: str = get_title(entry)
    if not title:
        return None
    title = title.replace("{", "").replace("}", "")
    # print(f"Resolving DBLP for title: {title}, doi: {doi}")
    uri_encoded_doi = requests.utils.quote(title)
    publication_uri = None
    try:
        dblp_api_url = f"https://dblp.org/search/publ/api?q={uri_encoded_doi}&format=json"
        # print(f"Requesting DBLP API URL: {dblp_api_url}")
        resp = get_with_backoff(dblp_api_url)
        data = resp.json()
        hits = data.get("result", {}).get("hits", {}).get("hit", [])
        for hit in hits:
            # Check if the DOI matches (can have multiple results)
            pub_doi = hit.get("info", {}).get("doi", None)
            if not str_equal_ignore_case(pub_doi, doi):
                return None

            publication_uri = hit.get("info", {}).get("url", None)
            if publication_uri is None:
                continue
            # print(f"Found publication URI: {publication_uri}")
            try:
                request_url = f"{publication_uri}.bib"
                headers = {
                    "Accept": "application/x-bibtex; charset=utf-8"
                }
                response = get_with_backoff(request_url, headers=headers)
                temp_lib = parse_string(response.text)
                found = temp_lib.entries[0]
                return found
            except Exception as e:
                # print(
                #     f"Failed to get entry from DBLP for DOI: {doi}, error: {e}")
                continue
    except Exception as e:
        # print(
        #     f"Failed to get entry from DBLP for DOI: {doi}, error: {e}")
        return None

    return None
