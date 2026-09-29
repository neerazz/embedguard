# Releasing EmbedGuard

Zenodo archives every release under the concept DOI [10.5281/zenodo.18364919](https://doi.org/10.5281/zenodo.18364919). Deposit each release **by hand** as a new version of the latest Zenodo record, not through Zenodo's GitHub integration.

The integration is switched off for this repository. Earlier versions were deposited by hand, so the integration has no record of them. It would treat the next GitHub release as the first one and start a new concept DOI, splitting the version history. The v1.3.0 webhook entry shows as "Failed" in the Zenodo account settings for this reason, and that entry can be ignored. The archived v1.3.0 is record [23032135](https://zenodo.org/records/23032135).

## Steps

1. **Pass the release gates.** In a fresh `git clone`, on Python 3.10 and 3.14, run:
   - `python -m pytest -q --no-cov`
   - `python -m ruff check .`
   - `./reproduce.sh`
   - `python -m build && python -m twine check dist/*`
2. **Regenerate the Tier-2b results** from a clean checkout of the code commit with `scripts/run_tier2b.sh`. Commit them. `tests/test_evidence_integrity.py` checks that the manuscript and docs tables match them.
3. **Bump the version** in `pyproject.toml`, `embedguard/__init__.py`, `CITATION.cff` and `CHANGELOG.md`.
4. **Tag and publish.** Create the tag with `git tag -a vX.Y.Z` and push it. Then publish the GitHub release.
5. **Build the archive files:**
   - `git archive --format=zip --prefix=embedguard-X.Y.Z/ -o embedguard-vX.Y.Z.zip vX.Y.Z`
   - the rendered `paper/manuscript.pdf`
6. **Deposit on Zenodo.** Open the latest record and choose **New version**. Then:
   - upload the two files;
   - set the version and resource type (Software);
   - link the tag as `isSupplementTo`;
   - publish.
7. **Verify the deposit:**
   - the new record appears under the concept DOI;
   - the downloaded zip's SHA-256 matches the local file;
   - the version DOI resolves at doi.org. DataCite registration can take up to two hours.
8. **Cite the new version DOI** in `README.md`, `CITATION.cff` and the manuscript's Data Availability section.
