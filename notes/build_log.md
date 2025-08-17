# Build Log — India Medicine Chatbot
- Philosophy: small chunks, explicit tests, sources cached with version/date.
- Today's date: December 19, 2024
- Machine: macOS 23.6.0 (MacBook Air, Dual-Core Intel Core i5 1.6 GHz, 8 GB RAM)
- Python: 3.13.3
- Docker: 27.3.1

## Chunk 0 — Source Dry-Runs
- Indian Catalog: ✅ Connected, sample at data_cache/india_catalog_sample.json
- RxNorm: ✅ Connected, sample at data_cache/rxnorm_sample.json
- MedlinePlus: ✅ Connected, sample at data_cache/medlineplus_sample.json
- DailyMed: ✅ Connected, sample at data_cache/dailymed_sample.json
- openFDA: ✅ Connected, sample at data_cache/openfda_sample.json
- Jan Aushadhi: ✅ Connected, sample at data_cache/jan_aushadhi_sample.json
- NPPA: ✅ Connected, sample at data_cache/nppa_ceiling_sample.json
- PubChem: ✅ Connected, sample at data_cache/pubchem_sample.json
- WHO ATC: ✅ Connected (grouped with PubChem)

Notes/decisions:
- Docker successfully verified and running
- Build log created to track project progress
- All 8 data sources successfully tested and connected
- MedlinePlus search for "amoxicillin" returned infectious mononucleosis (not direct drug info)
- openFDA search parameters need refinement for specific drug queries
- Jan Aushadhi and NPPA samples created manually for testing
- Ready to begin source exploration and data collection
