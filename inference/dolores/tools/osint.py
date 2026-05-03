# Standard library imports.
from json import dumps, loads
from os import environ
from requests import get

# Third party imports.
from langchain.tools import tool


@tool
def search_nvd(keyword: str, results_per_page: int = 10) -> dict:
    """Search the National Vulnerability Database (NVD) for Common Vulnerabilities and Exposures (CVEs) by keyword.

    Args:
        keyword: The keyword to search for in the NVD CVE database.
        results_per_page: Number of results to return (default 10, max 2000).
    """
    api_key = environ["NVD_API_KEY"]
    response = get(
        "https://services.nvd.nist.gov/rest/json/cves/2.0",
        headers={"apiKey": api_key},
        params={"keywordSearch": keyword, "resultsPerPage": results_per_page},
    )
    response.raise_for_status()
    return response.json()


@tool
def convert_cve_to_stix(cve_json: str) -> str:
    """Converts a CVE JSON object from the NVD API to a STIX 2.1 Vulnerability object.

    Args:
        cve_json: A JSON string representing a single CVE item from the NVD API response
    """
    cve = loads(cve_json)
    cve_item = cve["vulnerabilities"][0]["cve"] if "vulnerabilities" in cve else cve

    cve_id = cve_item["id"]
    description = next(
        (d["value"] for d in cve_item.get("descriptions", []) if d["lang"] == "en"),
        "No description available",
    )
    published = cve_item.get("published", "")
    modified = cve_item.get("lastModified", "")

    cvss_score = None
    cvss_vector = None
    metrics = cve_item.get("metrics", {})
    for version_key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        if version_key in metrics:
            cvss_data = metrics[version_key][0]["cvssData"]
            cvss_score = cvss_data.get("baseScore")
            cvss_vector = cvss_data.get("vectorString")
            break

    stix_object = {
        "type": "vulnerability",
        "spec_version": "2.1",
        "id": f"vulnerability--{cve_id.lower().replace('cve-', '', 1).replace('-', '-', 1)}",
        "created": published,
        "modified": modified,
        "name": cve_id,
        "description": description,
        "external_references": [
            {
                "source_name": "cve",
                "external_id": cve_id,
                "url": f"https://nvd.nist.gov/vuln/detail/{cve_id}",
            }
        ],
    }

    if cvss_score is not None:
        stix_object["x_cvss"] = {
            "score": cvss_score,
            "vector": cvss_vector,
        }

    return dumps(stix_object)
