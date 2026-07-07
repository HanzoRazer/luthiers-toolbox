"""WP-001 — registry_router symbol disambiguation: route-mount regression.

Ground-zero witness for the WP-001 alias-only change. The CAM guitar registry router
and the instruments guitar registry router were both imported as the symbol
`registry_router`, creating cross-package import/consumer ambiguity. They were aliased
to domain-specific names (`cam_registry_router`, `instrument_registry_router`).

This is a naming-clarity change only: symbols were disambiguated; **no route was moved,
renamed, or removed**. These tests prove both routers still mount their distinctive
endpoints, and guard against the ambiguous shared symbol returning.
"""


def _paths(router):
    return {getattr(r, "path", None) for r in router.routes}


def test_instruments_guitar_registry_router_still_mounts():
    """Instruments guitar registry endpoints are unchanged after the alias rename."""
    from app.routers.instruments.guitar import router as guitar_router
    paths = _paths(guitar_router)
    # Distinctive endpoints owned by the instruments registry router:
    assert "/smart/bundle" in paths
    assert "/" in paths
    assert "/{model_id}/spec" in paths


def test_cam_guitar_registry_router_still_mounts():
    """CAM guitar registry endpoints are unchanged after the alias rename."""
    from app.routers.cam.guitar import router as cam_guitar_router
    paths = _paths(cam_guitar_router)
    # Distinctive endpoints owned by the CAM registry router:
    assert "/{model_id}/health" in paths
    assert "/{model_id}/capabilities" in paths


def test_no_router_is_bound_to_the_ambiguous_symbol():
    """Regression guard: neither package binds an APIRouter under the generic
    `registry_router` name.

    Note: `instruments/guitar/registry_router.py` is a *submodule*, so the attribute
    `registry_router` may legitimately exist as that module. What WP-001 removes is the
    ambiguity of a *router object* bound as `registry_router` in both packages. So the
    guard checks types: the domain-specific aliases are APIRouters, and the generic name
    is not bound to a router in either package.
    """
    from fastapi import APIRouter
    import app.routers.cam.guitar as cam_guitar_pkg
    import app.routers.instruments.guitar as instr_guitar_pkg

    # Domain-specific router aliases exist and are routers.
    assert isinstance(cam_guitar_pkg.cam_registry_router, APIRouter)
    assert isinstance(instr_guitar_pkg.instrument_registry_router, APIRouter)

    # The generic `registry_router` name is NOT an APIRouter in either package
    # (in instruments it is the submodule; in cam it is absent).
    assert not isinstance(getattr(cam_guitar_pkg, "registry_router", None), APIRouter)
    assert not isinstance(getattr(instr_guitar_pkg, "registry_router", None), APIRouter)
