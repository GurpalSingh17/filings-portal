import sys
import requests
import xml.etree.ElementTree as ET
import pandas as pd

# —— CONFIG ——
DEFAULT_INPUT_CSV = "filtered_with_parsed.csv"
DEFAULT_OUTPUT_CSV = "example_of_final_output.csv"
HEADERS = {
    "User-Agent": "GitHub Actions Bot <actions@github.com>"
}
# ————————

def parse_primary_doc(xml_url: str) -> dict:
    """Fetches the XML and extracts the required fields."""
    resp = requests.get(xml_url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    root = ET.fromstring(resp.content)

    # PrimaryIssuer
    pi = root.find(".//primaryIssuer")
    cik     = pi.findtext("cik", "").strip() if pi is not None else ""
    name    = pi.findtext("entityName", "").strip() if pi is not None else ""
    etype   = pi.findtext("entityType", "").strip() if pi is not None else ""
    juri    = pi.findtext("jurisdictionOfInc", "").strip() if pi is not None else ""

    # Industry Group
    ig_elem = root.find(".//offeringData/industryGroup/industryGroupType")
    industry_group = (ig_elem.text or "").strip() if ig_elem is not None else ""

    # Related Persons
    related = []
    for rp in root.findall(".//relatedPersonsList/relatedPersonInfo"):
        fn  = rp.findtext("relatedPersonName/firstName", "").strip()
        ln  = rp.findtext("relatedPersonName/lastName", "").strip()
        full_name = (fn + " " + ln).strip()
        clar      = rp.findtext("relationshipClarification", "").strip()
        related.append(f"{full_name} ({clar})")
    related_persons = "; ".join(related)

    return {
        "CIK": cik,
        "CompanyName": name,
        "EntityType": etype,
        "IndustryGroup": industry_group,
        "JurisdictionOfIncorporation": juri,
        "RelatedPersons": related_persons,
        "InformationSource": xml_url
    }


def main():
    # allow passing input/output via args
    in_csv  = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_INPUT_CSV
    out_csv = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUTPUT_CSV

    df = pd.read_csv(in_csv, dtype=str)
    outputs = []

    for _, row in df.iterrows():
        xml_url = row.get("Source File", "")
        if not isinstance(xml_url, str) or not xml_url.lower().endswith(".xml"):
            continue

        try:
            record = parse_primary_doc(xml_url)
        except Exception as e:
            print(f"⚠️ Skipping {xml_url}: {e}")
            continue

        outputs.append(record)

    out_df = pd.DataFrame(outputs)
    out_df.to_csv(out_csv, index=False)
    print(f"✅ Wrote {len(out_df)} rows to {out_csv}")


if __name__ == "__main__":
    main()
