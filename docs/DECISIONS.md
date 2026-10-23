# Engineering decisions

| # | Decision | Why |
|---|---|---|
| 1 | Flask + stdlib `sqlite3` instead of FastAPI + SQLAlchemy (as first specified) | The build environment had no package registry access; using available libraries let every path be executed and tested end-to-end before delivery. Routers are thin and services framework-free, so porting to FastAPI is mechanical. |
| 2 | Plain SQL migrations, TEXT UUID keys, ISO-8601 UTC timestamps | Portable to PostgreSQL with no ORM dependency. |
| 3 | Rules as YAML data + small operator library | Policy changes are data changes with a version and checksum; operators are unit-tested. |
| 4 | Findings fingerprinted by rule, version and subject (not value) | Re-runs keep reviewer resolutions; fixed problems are cleared rather than duplicated. |
| 5 | Reviewer corrections stored beside originals | Nothing extracted is overwritten; the audit shows both. |
| 6 | In-process thread-pool job runner with a jobs table | Simple and reliable for one instance. For multiple instances swap `JobRunner` for Celery/RQ; run gunicorn with one worker until then. |
| 7 | Page images rendered server-side and cached | The viewer needs no PDF library in the browser, and bounding boxes are fractions of the page so overlays are resolution-independent. |
| 8 | Template summary always on; LLM optional | The demo and core workflow never depend on a network service. |
| 9 | Hash-based client routing, no router/query libraries | Fewer dependencies; works when served from any static host or from the API. |
