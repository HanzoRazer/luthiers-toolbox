# Endpoint contracts

Both clusters call Axios `get`. Neither sets a request body, headers, `paramsSerializer`, or a retry. Query serialization is the Axios default applied to the `params` object. The characterization tests assert that object. They do not make live network requests.

Fixtures live in `packages/client/src/views/art/risk-dashboard/__tests__/riskDashboardFixtures.ts`. Both specs ran against them on 2026-11-10: 12 February 19 tests and 10 February 22 tests, all passing.

| Fixture | February 19 result | February 22 result |
|---|---|---|
| Successful bucket list | Three rows mapped. Score `4` with no label becomes High. String score `0.4` with an empty label becomes Low. Label `Kept` is preserved at score 9. Series `['1', null, 2]` becomes `[1, 0, 2]` with path `0.0,10.0 30.0,19.0 60.0,1.0`. A one-point series uses `0,10 60,10`. A non-array series becomes `[]`. | Same mapping and paths. |
| Empty bucket list | `data: []` and `data: null` both leave `bucketsRaw` empty. | Same. |
| One selected bucket | `GET /api/compare/risk_bucket_detail` with `lane`, `preset`, and `job_hint` when the filter is set. Entries replace the previous list. Loading is true until the promise settles. | Same. `job_hint` is read from the ref. |
| Missing selected bucket | 404 leaves the requested bucket selected, entries empty, loading false, error `Failed to load bucket entries.` | Same. |
| Bucket-details success | Entries equal the response array. | Same. |
| 404, 422, and network failure | Aggregate failure clears `bucketsRaw` and calls `console.error('Failed to load risk aggregates', err)`. Detail failure uses the static string above. Status and response body are not read. | Same for aggregate and detail. |
| CSV with commas, quotes, and newlines | Client CSV quotes `Rosette, "north"\nbench` as `"Rosette, ""north""\nbench"`. CRLF rows. Blob type `text/csv;charset=utf-8;`. Server CSV bytes are wrapped in a Blob and not parsed. | Same bytes and blob type. |
| JSON export | `JSON.stringify(data, null, 2)` for the report and the snapshot. Server bucket JSON uses `responseType: 'blob'` and is not re-stringified. | Same. |

## Operations

| Operation | Method and URL | Params | responseType | Empty input | Failure |
|---|---|---|---|---|---|
| Refresh | `GET /api/compare/risk_aggregate` | `since` and `until` only when non-empty | default | Allowed. Sends `{ params: {} }`. | `console.error`; `bucketsRaw = []` |
| Details | `GET /api/compare/risk_bucket_detail` | `lane`, `preset`, and `job_hint` only when the job filter is non-empty | default | A null bucket is not a detail call. An empty job filter omits `job_hint`. | Static detail error. Selection kept. |
| Bucket CSV | `GET /api/compare/risk_bucket_export` | `lane`, `preset`, `format=csv` | `blob` | Null bucket: no request | `console.error` only |
| Bucket JSON blob | `GET /api/compare/risk_bucket_export` | `lane`, `preset`, `format=json` | `blob` | Null bucket: no request | `console.error` only |
| Bucket report | `GET /api/compare/risk_bucket_report` | `lane`, `preset`, optional `job_hint` | `json` | Null bucket: no request. The entries array is not sent. | February 19: `console.error` only. February 22: `console.error` then `setError('Failed to download bucket JSON report.')` |
| Snapshot | `GET /api/compare/risk_snapshot` | `since` and `until` only when non-empty | `json` | Sends `{ params: {} }` | `console.error` only |

One explicit call issues one GET. Importing either module issues none.

## Sorting, filtering, and filenames

`allLanes` drops an empty lane and sorts. `allPresets` stores an empty preset as `(none)` and sorts. The filter predicate compares the raw preset, so the filter value `(none)` matches no empty preset. An empty filter string does not constrain that field.

Client CSV filename: `crosslab_risk_aggregate[_from-<since>][_to-<until>]_<stamp>.csv`.

Server blob filenames: `risk_bucket_<lane>_<preset>.csv` and `.json`. Lane and preset are not sanitized.

Report filename: `bucket_report_<lane>_<preset>[_hint-<job>][_from-<since>][_to-<until>]_<stamp>.json`.

Snapshot filename: `risk_snapshot[_from-<since>][_to-<until>]_<stamp>.json`.

`filenameTimestamp()` is `new Date().toISOString()` with `:` and `.` replaced by `-`. The tests freeze `2026-02-22T06:01:32.000Z`, which becomes `2026-02-22T06-01-32-000Z`.

## Where the contracts differ

The request builders agree when they are given the same strings. `RISK-L01` can change those strings after a query round-trip because February 22 writes untrimmed filter values. `RISK-L03` means a date edit on the February 22 dashboard does not issue the aggregate GET that the February 19 view issues. Those gaps are filter and watch behavior, recorded as `EARLIER_ONLY` in the matrix. They are not a second method, URL, or body for the same call.
