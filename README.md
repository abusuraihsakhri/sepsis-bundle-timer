# Sepsis Bundle Timer

A de-identified, browser-based timestamp worksheet and Python timing utility for adult sepsis quality-improvement exercises. The browser app works without a server or Python runtime.

**Clinical limitation:** This is **not** a validated clinical decision-support device, formal SEP-1 compliance calculator, or medical record. Never delay assessment or treatment to use it. Do not enter patient names, MRNs, or other identifiers. Select the time zero and the applicable pathway using clinical judgment and local protocol.

## Browser application

The browser UI is in [web/index.html](web/index.html). GitHub Pages is configured through `.github/workflows/pages.yml` to publish the contents of `web/` after changes reach `master`. Open the deployed Pages environment when its deployment has succeeded; a public URL is not asserted until it is verified.

To use the app locally, open `web/index.html` in a modern browser or run:

```bash
python -m http.server 8000 --directory web
# Visit http://localhost:8000/
```

Set a recognition/suspicion timestamp and choose an adult assessment pathway. The worksheet displays elapsed time and a reference deadline; optionally record initial lactate, blood-culture collection and antibiotic administration timestamps. It indicates whether the recorded cultures preceded antibiotics, and exports a local CSV.

The pathway options reflect the **2026 Surviving Sepsis Campaign** adult guideline:
- **Shock or probable/definite sepsis:** administer antimicrobials immediately, ideally within **1 hour** of recognition.
- **Possible sepsis without shock:** rapidly investigate; if substantial infection concern persists, administer antimicrobials within **3 hours** of initial suspicion. This is conditional and must not delay indicated therapy.

Only the antibiotic reference time is calculated. Fluid resuscitation, vasopressors, lactate reassessment, antibiotic appropriateness, contraindications and formal quality-measure criteria are not assessed. These timestamps do **not** establish clinical eligibility or protocol compliance. Verify the workstation clock, local timezone and daylight-saving transitions before relying on any timestamp.

**References:** [SCCM Surviving Sepsis Campaign 2026 guidelines](https://sccm.org/clinical-resources/guidelines/guidelines/surviving-sepsis-campaign-international-guidelines-for-management-of-sepsis-and-septic-shock-2026).

## Python timing API and CLI

`bundle_timing.py` is standard-library-only. All Python timestamps **must include an explicit timezone offset**.

```bash
python -m bundle_timing --recognition 2026-10-13T10:00:00+00:00 --pathway urgent --antibiotic 2026-10-13T10:45:00+00:00
```

Or use `evaluate_timing(recognition, pathway, antibiotic=None, cultures=None, lactate=None, as_of=None)` directly. The existing `cli.py timing` command offers the same parameters when optional server dependencies are installed.

## Existing auxiliary tools

The repository retains the original `sepsis_timer.py` terminology lookup and batch CSV enrichment, `agents/` orchestration and mock responses, `enrichment.py` experimental thresholds, and FastAPI endpoints. These modules are **not validated clinical sepsis scoring or treatment engines**. In particular, the agent's generic numeric thresholds and mock replies must not be interpreted as clinical decisions.

```bash
python sepsis_timer.py single lactate
python sepsis_timer.py batch --input sample.csv --output output.csv
python cli.py audit --task-id TEST-001
python cli.py serve --host 127.0.0.1 --port 8000
```

## Development and tests

Requirements: Python 3.10+ for the legacy agent API; Node.js 18+ for browser test scripts (not required to use the web app).

```bash
python -m pip install -r requirements.txt pytest
python -m pytest -q
node --test web/timing.test.cjs
node --check web/app.js
docker build -t sepsis-bundle-timer .
```

`docker compose up --build` runs the FastAPI server on port 8000. The API is separate from the static browser application. A production server requires appropriate access controls, operational monitoring and a stable secret key (`AUDIT_SECRET_KEY`); the included server is not hardened for handling identifiable clinical data.

## Privacy and security

The **static browser app** does not make network requests or use browser storage. Data remains in browser memory and is discarded on reload; CSV export writes to the local device only at your request. Do not enter personal health information. The optional backend and legacy batch tools process input on the system running them and may hold data in memory; they have a limited regex-based identifier screen, **not** comprehensive HIPAA de-identification. The HMAC audit trail is in-memory unless persistence is implemented separately. Do not expose the API to untrusted networks.

Browser support: recent Chrome/Edge, Firefox, and Safari with JavaScript and `datetime-local` support. No Pyodide or server-side Python is used for the GitHub Pages app.

## License

[MIT](LICENSE).
