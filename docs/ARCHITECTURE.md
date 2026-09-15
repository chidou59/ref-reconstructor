# Architecture

## Overview

`ref-reconstructor` is a Streamlit application that finds references in uploaded Word documents, reconstructs citation metadata, and writes a revised document.

## Processing flow

```text
Uploaded DOCX
  -> security and file validation
  -> DocParser
  -> citation mapping
  -> metadata Orchestrator
  -> provider adapters / optional Qwen assistance
  -> formatter
  -> DocRenderer
  -> downloadable DOCX and audit summary
```

## Packages

- `main_web.py`: Streamlit entry point and page configuration.
- `web_app/`: page sections, presentation, and end-to-end application logic.
- `core/doc_parser.py`: Word document parsing.
- `core/citation_mapper.py`: connects in-text references to bibliography entries.
- `core/doc_renderer.py`: generates the revised document.
- `core/security.py`: validates upload names, types, paths, and size constraints.
- `engines/orchestrator.py`: metadata lookup and fallback policy.
- `engines/api_providers/`: Crossref, OpenAlex, Semantic Scholar, and Qwen adapters.
- `engines/formatter.py`: citation normalization and GB/T 7714-2015 rendering.

## Privacy boundary

Uploaded documents, generated documents, audit logs, and credentials are runtime data. They must not be committed. Deployments should use the host's secret manager for optional API keys.
