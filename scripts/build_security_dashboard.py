#!/usr/bin/env python3
"""Aggregate CycloneDX SBOMs and Snyk / GitLab Container Scanning JSON reports
into a merged CycloneDX BOM and a self-contained HTML security dashboard.
"""

from __future__ import annotations

import datetime
import html
import json
import uuid
from pathlib import Path

SBOM_SOURCES = {
    "frontend-sbom.cdx.json": "Frontend App",
    "sbom-backend-cdx.json": "Backend App",
    "sbom-container-backend.cdx.json": "Backend Container",
    "sbom-container-frontend.cdx.json": "Frontend Container",
}

SNYK_SOURCES = {
    "snyk-frontend.json": "Snyk (Frontend)",
    "snyk-backend.json": "Snyk (Backend)",
}

CS_SOURCES = {
    "cs-backend.json": "Container Scan (Backend)",
    "cs-frontend.json": "Container Scan (Frontend)",
}

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "unknown": 4}


def extract_licenses(component: dict) -> str:
    licenses = []
    for item in component.get("licenses", []):
        if isinstance(item, dict):
            lic = item.get("license", {})
            name = lic.get("id") or lic.get("name") or item.get("expression")
            if name:
                licenses.append(name)
    return ", ".join(dict.fromkeys(licenses)) or "Unknown"


def load_sboms() -> tuple[list[dict], dict]:
    merged: dict[str, dict] = {}
    raw_components: list[dict] = []

    for filename, source_label in SBOM_SOURCES.items():
        path = Path(filename)
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue

        for comp in data.get("components", []):
            name = comp.get("name", "unknown")
            version = comp.get("version", "")
            purl = comp.get("purl") or f"{name}@{version}"
            comp_type = comp.get("type", "library")
            lic = extract_licenses(comp)

            if purl not in merged:
                merged[purl] = {
                    "name": name,
                    "version": version,
                    "type": comp_type,
                    "purl": purl,
                    "license": lic,
                    "sources": [source_label],
                }
                raw_components.append(comp)
            else:
                if source_label not in merged[purl]["sources"]:
                    merged[purl]["sources"].append(source_label)
                if merged[purl]["license"] == "Unknown" and lic != "Unknown":
                    merged[purl]["license"] = lic

    bom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": f"urn:uuid:{uuid.uuid4()}",
        "version": 1,
        "metadata": {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "tools": [{"name": "CounterApp Security Aggregator", "version": "1.0.0"}],
        },
        "components": raw_components,
    }
    return sorted(merged.values(), key=lambda c: (c["name"].lower(), c["version"])), bom


def load_vulnerabilities() -> list[dict]:
    vulns: list[dict] = []

    # 1. Snyk JSON reports (dict or list of project results)
    for filename, source_label in SNYK_SOURCES.items():
        path = Path(filename)
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue

        entries = data if isinstance(data, list) else [data]
        for entry in entries:
            for v in entry.get("vulnerabilities", []):
                sev = str(v.get("severity", "unknown")).lower()
                vulns.append(
                    {
                        "id": v.get("id", "N/A"),
                        "title": v.get("title", "Untitled"),
                        "severity": sev,
                        "package": f"{v.get('packageName', '')}@{v.get('version', '')}".strip("@"),
                        "fixed_in": ", ".join(v.get("fixedIn", [])) or "No fix",
                        "source": source_label,
                        "url": v.get("url", ""),
                    }
                )

    # 2. GitLab Container Scanning reports
    for filename, source_label in CS_SOURCES.items():
        path = Path(filename)
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue

        for v in data.get("vulnerabilities", []):
            sev = str(v.get("severity", "unknown")).lower()
            loc = v.get("location", {})
            dep = loc.get("dependency", {})
            pkg_name = dep.get("package", {}).get("name", "")
            pkg_ver = dep.get("version", "")
            cve = next(
                (i.get("value") for i in v.get("identifiers", []) if i.get("type") == "cve"),
                v.get("id", "N/A"),
            )
            links = v.get("links", [])
            url = links[0].get("url", "") if links else ""
            vulns.append(
                {
                    "id": cve,
                    "title": v.get("message") or v.get("description", "Container Vulnerability")[:120],
                    "severity": sev,
                    "package": f"{pkg_name}@{pkg_ver}".strip("@"),
                    "fixed_in": v.get("solution", "See advisory"),
                    "source": source_label,
                    "url": url,
                }
            )

    vulns.sort(key=lambda x: (SEVERITY_ORDER.get(x["severity"], 99), x["id"]))
    return vulns


def render_html(components: list[dict], vulns: list[dict]) -> str:
    sev_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for v in vulns:
        if v["severity"] in sev_counts:
            sev_counts[v["severity"]] += 1

    vuln_rows = "\n".join(
        f"""<tr data-sev="{html.escape(v['severity'])}">
          <td><span class="badge sev-{html.escape(v['severity'])}">{html.escape(v['severity'].upper())}</span></td>
          <td>{f'<a href="{html.escape(v["url"])}" target="_blank" rel="noopener">{html.escape(v["id"])}</a>' if v["url"] else html.escape(v["id"])}</td>
          <td>{html.escape(v['title'])}</td>
          <td><code>{html.escape(v['package'])}</code></td>
          <td>{html.escape(v['fixed_in'])}</td>
          <td>{html.escape(v['source'])}</td>
        </tr>"""
        for v in vulns
    ) or '<tr><td colspan="6" class="empty">No vulnerabilities reported.</td></tr>'

    comp_rows = "\n".join(
        f"""<tr>
          <td><strong>{html.escape(c['name'])}</strong></td>
          <td><code>{html.escape(c['version'])}</code></td>
          <td>{html.escape(c['type'])}</td>
          <td>{html.escape(c['license'])}</td>
          <td>{html.escape(', '.join(c['sources']))}</td>
        </tr>"""
        for c in components
    ) or '<tr><td colspan="5" class="empty">No SBOM components found.</td></tr>'

    generated_at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>CounterApp Security & SBOM Dashboard</title>
<style>
  body {{ font-family: system-ui, -apple-system, sans-serif; margin: 2rem; background: #f8fafc; color: #0f172a; }}
  h1 {{ margin-bottom: 0.25rem; }}
  .meta {{ color: #64748b; margin-bottom: 1.5rem; font-size: 0.9rem; }}
  .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
  .card {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1rem; }}
  .card .num {{ font-size: 1.75rem; font-weight: 700; }}
  .card .lbl {{ color: #64748b; font-size: 0.85rem; }}
  .controls {{ display: flex; gap: 1rem; margin-bottom: 1rem; }}
  input {{ padding: 0.5rem 0.75rem; border: 1px solid #cbd5e1; border-radius: 6px; width: 320px; }}
  table {{ width: 100%; border-collapse: collapse; background: #fff; border: 1px solid #e2e8f0; margin-bottom: 2.5rem; }}
  th, td {{ text-align: left; padding: 0.65rem 0.85rem; border-bottom: 1px solid #e2e8f0; font-size: 0.9rem; }}
  th {{ background: #f1f5f9; font-weight: 600; }}
  .badge {{ padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 700; color: #fff; }}
  .sev-critical {{ background: #991b1b; }}
  .sev-high {{ background: #dc2626; }}
  .sev-medium {{ background: #d97706; }}
  .sev-low {{ background: #2563eb; }}
  .sev-unknown {{ background: #64748b; }}
  .empty {{ text-align: center; color: #64748b; padding: 1.5rem; }}
</style>
</head>
<body>
  <h1>CounterApp Security & SBOM Dashboard</h1>
  <div class="meta">Generated {generated_at}</div>

  <div class="cards">
    <div class="card"><div class="num">{len(components)}</div><div class="lbl">Total Components</div></div>
    <div class="card"><div class="num" style="color:#991b1b">{sev_counts['critical']}</div><div class="lbl">Critical Vulns</div></div>
    <div class="card"><div class="num" style="color:#dc2626">{sev_counts['high']}</div><div class="lbl">High Vulns</div></div>
    <div class="card"><div class="num" style="color:#d97706">{sev_counts['medium']}</div><div class="lbl">Medium Vulns</div></div>
    <div class="card"><div class="num" style="color:#2563eb">{sev_counts['low']}</div><div class="lbl">Low Vulns</div></div>
  </div>

  <h2>Vulnerabilities ({len(vulns)})</h2>
  <div class="controls">
    <input type="text" placeholder="Filter vulnerabilities..." oninput="filterTable('vuln-table', this.value)">
  </div>
  <table id="vuln-table">
    <thead><tr><th>Severity</th><th>ID</th><th>Title</th><th>Package</th><th>Fix</th><th>Source</th></tr></thead>
    <tbody>{vuln_rows}</tbody>
  </table>

  <h2>Software Bill of Materials ({len(components)})</h2>
  <div class="controls">
    <input type="text" placeholder="Filter packages, licenses, or sources..." oninput="filterTable('sbom-table', this.value)">
  </div>
  <table id="sbom-table">
    <thead><tr><th>Package</th><th>Version</th><th>Type</th><th>License</th><th>Found In</th></tr></thead>
    <tbody>{comp_rows}</tbody>
  </table>

<script>
function filterTable(tableId, query) {{
  const q = query.toLowerCase();
  for (const row of document.querySelectorAll('#' + tableId + ' tbody tr')) {{
    row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
  }}
}}
</script>
</body>
</html>
"""


def main() -> None:
    components, merged_bom = load_sboms()
    vulns = load_vulnerabilities()

    Path("merged-sbom.cdx.json").write_text(json.dumps(merged_bom, indent=2), encoding="utf-8")
    Path("security-dashboard.html").write_text(render_html(components, vulns), encoding="utf-8")
    print(f"Dashboard generated: {len(components)} components, {len(vulns)} vulnerabilities.")


if __name__ == "__main__":
    main()