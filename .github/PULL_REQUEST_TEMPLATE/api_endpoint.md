# API Endpoint PR Checklist

## Endpoint Details

- **Path:** `/api/...`
- **Method:** `GET` / `POST` / `PUT` / `DELETE`
- **Router file:** `services/api/app/.../`

---

## Lane Compliance

> See [API Lane Consolidation Plan](../../docs/ARCH/API_Lane_Consolidation_Plan.md)

### Required

- [ ] Endpoint is under a **canonical lane**:
  - [ ] `/api/art/*` for Art Studio
  - [ ] `/api/rmos/*` for RMOS

### If using legacy lane (requires justification)

- [ ] I am adding to `/api/art-studio/*` because: _____________
- [ ] I am adding to `/rosette/*` because: _____________
- [ ] I have applied for `legacy-exception` label

**Note:** New endpoints on legacy lanes will be rejected without justification.

---

## Implementation Checklist

- [ ] Endpoint follows existing patterns in the router file
- [ ] Request/response schemas defined in appropriate `schemas*.py`
- [ ] Auth requirements documented (if applicable)
- [ ] Error responses follow API conventions (4xx/5xx with detail)

---

## Testing

- [ ] Unit test added for happy path
- [ ] Unit test added for error cases (400, 401, 403, 404)
- [ ] Tested manually via curl/Postman

---

## Documentation

- [ ] Added to `docs/ENDPOINT_TRUTH_MAP.md` if new endpoint family
- [ ] OpenAPI/Swagger docs updated (if using FastAPI auto-docs)

---

## Deprecation (if modifying legacy endpoint)

- [ ] Added `Deprecation: true` header
- [ ] Added `Sunset: YYYY-MM-DD` header
- [ ] Added `Link: <successor>; rel="successor-version"` header
- [ ] Added server log warning for deprecated endpoint hit
