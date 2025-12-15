# services/api/app/tests/instrument_geometry/test_instrument_geometry_imports.py

def test_instrument_geometry_public_api_imports():
    """
    Confirms that the instrument_geometry package exposes the correct
    Wave-19 symbols, that legacy Wave-14 enums are NOT exported,
    and that basic functions load and work.
    """

    import app.instrument_geometry as ig

    # --- Wave-19 core types must exist ---
    assert hasattr(ig, "GuitarModelSpec")
    assert hasattr(ig, "ScaleSpec")
    assert hasattr(ig, "MultiScaleSpec")
    assert hasattr(ig, "NeckJointSpec")
    assert hasattr(ig, "BridgeSpec")
    assert hasattr(ig, "StringSpec")
    assert hasattr(ig, "StringSetSpec")
    assert hasattr(ig, "DXFMappingSpec")

    # --- Loader API must exist ---
    assert hasattr(ig, "load_model_spec")
    assert hasattr(ig, "list_available_model_ids")
    assert callable(ig.load_model_spec)
    assert callable(ig.list_available_model_ids)

    # --- Basic scale utilities must exist ---
    assert hasattr(ig, "compute_fret_positions_mm")
    assert hasattr(ig, "compute_fret_spacing_mm")
    assert hasattr(ig, "compute_compensated_scale_length_mm")

    # --- Legacy Wave-14 symbols must NOT exist ---
    assert not hasattr(ig, "InstrumentModelId")
    assert not hasattr(ig, "InstrumentModelStatus")
    assert not hasattr(ig, "InstrumentModelSpec")  # old version only

def test_load_benedetto_17_works():
    """
    Confirms that at least one known model loads end-to-end.
    """

    from app.instrument_geometry import load_model_spec, list_available_model_ids

    ids = list_available_model_ids()
    # Must contain our known model
    assert "benedetto_17" in ids

    spec = load_model_spec("benedetto_17")
    assert spec is not None

    # Spot-check: scale length > 600mm for this model
    assert spec.scale.scale_length_mm > 600
    # Spot-check: model defines string count
    assert len(spec.string_set.strings) >= 6
