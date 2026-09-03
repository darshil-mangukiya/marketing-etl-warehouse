# Canonical Analysis Input

These versioned CSV files are the public, reproducible input contract for the six modeled stakeholder analyses. They are a generated/synthetic snapshot of the governed mart and deterministic scenario outputs used to produce the published analysis pack.

The snapshot includes only the tables and columns consumed by `../build_analysis_pack.py`. It contains no customer data, credentials, private filesystem paths, or live platform extracts. The builder loads these files into an in-memory DuckDB database, so clean-clone output does not depend on an ignored local warehouse or a shell environment override.

To refresh the snapshot intentionally, regenerate the governed marts, export the required columns in deterministic order, rebuild the analysis pack, and review all changed evidence together. Do not replace these files with an arbitrary local warehouse extract.
