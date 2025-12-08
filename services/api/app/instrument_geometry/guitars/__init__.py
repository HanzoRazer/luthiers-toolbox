"""
Guitar Model Stubs Subpackage

Contains per-model geometry specifications for 19 supported instruments.

Each module provides:
- get_spec() -> InstrumentSpec: Default specification for that model
- get_body_outline() -> List[Tuple[float, float]]: Body outline points (if available)
- MODEL_INFO: Dict with metadata (scale length, frets, strings, etc.)

Models by Category:
- Electric: strat, tele, les_paul, prs, sg, es_335, flying_v, explorer, firebird, moderne
- Acoustic: dreadnought, om_000, j_45, jumbo_j200, gibson_l_00, classical
- Bass: jazz_bass
- Other: archtop, ukulele
"""

from ..models import InstrumentModelId

# Model imports - each provides get_spec() and MODEL_INFO
from .strat import get_spec as get_strat_spec, MODEL_INFO as STRAT_INFO
from .tele import get_spec as get_tele_spec, MODEL_INFO as TELE_INFO
from .les_paul import get_spec as get_les_paul_spec, MODEL_INFO as LES_PAUL_INFO
from .dreadnought import get_spec as get_dreadnought_spec, MODEL_INFO as DREADNOUGHT_INFO
from .om_000 import get_spec as get_om_000_spec, MODEL_INFO as OM_000_INFO
from .j_45 import get_spec as get_j_45_spec, MODEL_INFO as J_45_INFO
from .jazz_bass import get_spec as get_jazz_bass_spec, MODEL_INFO as JAZZ_BASS_INFO
from .classical import get_spec as get_classical_spec, MODEL_INFO as CLASSICAL_INFO
from .archtop import get_spec as get_archtop_spec, MODEL_INFO as ARCHTOP_INFO
from .prs import get_spec as get_prs_spec, MODEL_INFO as PRS_INFO
from .sg import get_spec as get_sg_spec, MODEL_INFO as SG_INFO
from .jumbo_j200 import get_spec as get_jumbo_j200_spec, MODEL_INFO as JUMBO_J200_INFO
from .ukulele import get_spec as get_ukulele_spec, MODEL_INFO as UKULELE_INFO
from .gibson_l_00 import get_spec as get_gibson_l_00_spec, MODEL_INFO as GIBSON_L_00_INFO
from .flying_v import get_spec as get_flying_v_spec, MODEL_INFO as FLYING_V_INFO
from .es_335 import get_spec as get_es_335_spec, MODEL_INFO as ES_335_INFO
from .explorer import get_spec as get_explorer_spec, MODEL_INFO as EXPLORER_INFO
from .firebird import get_spec as get_firebird_spec, MODEL_INFO as FIREBIRD_INFO
from .moderne import get_spec as get_moderne_spec, MODEL_INFO as MODERNE_INFO

# Registry of all model specs by ID
MODEL_SPECS = {
    InstrumentModelId.STRAT: get_strat_spec,
    InstrumentModelId.TELE: get_tele_spec,
    InstrumentModelId.LES_PAUL: get_les_paul_spec,
    InstrumentModelId.DREADNOUGHT: get_dreadnought_spec,
    InstrumentModelId.OM_000: get_om_000_spec,
    InstrumentModelId.J_45: get_j_45_spec,
    InstrumentModelId.JAZZ_BASS: get_jazz_bass_spec,
    InstrumentModelId.CLASSICAL: get_classical_spec,
    InstrumentModelId.ARCHTOP: get_archtop_spec,
    InstrumentModelId.PRS: get_prs_spec,
    InstrumentModelId.SG: get_sg_spec,
    InstrumentModelId.JUMBO_J200: get_jumbo_j200_spec,
    InstrumentModelId.UKULELE: get_ukulele_spec,
    InstrumentModelId.GIBSON_L_00: get_gibson_l_00_spec,
    InstrumentModelId.FLYING_V: get_flying_v_spec,
    InstrumentModelId.ES_335: get_es_335_spec,
    InstrumentModelId.EXPLORER: get_explorer_spec,
    InstrumentModelId.FIREBIRD: get_firebird_spec,
    InstrumentModelId.MODERNE: get_moderne_spec,
}

# Registry of all model info dicts by ID
MODEL_INFOS = {
    InstrumentModelId.STRAT: STRAT_INFO,
    InstrumentModelId.TELE: TELE_INFO,
    InstrumentModelId.LES_PAUL: LES_PAUL_INFO,
    InstrumentModelId.DREADNOUGHT: DREADNOUGHT_INFO,
    InstrumentModelId.OM_000: OM_000_INFO,
    InstrumentModelId.J_45: J_45_INFO,
    InstrumentModelId.JAZZ_BASS: JAZZ_BASS_INFO,
    InstrumentModelId.CLASSICAL: CLASSICAL_INFO,
    InstrumentModelId.ARCHTOP: ARCHTOP_INFO,
    InstrumentModelId.PRS: PRS_INFO,
    InstrumentModelId.SG: SG_INFO,
    InstrumentModelId.JUMBO_J200: JUMBO_J200_INFO,
    InstrumentModelId.UKULELE: UKULELE_INFO,
    InstrumentModelId.GIBSON_L_00: GIBSON_L_00_INFO,
    InstrumentModelId.FLYING_V: FLYING_V_INFO,
    InstrumentModelId.ES_335: ES_335_INFO,
    InstrumentModelId.EXPLORER: EXPLORER_INFO,
    InstrumentModelId.FIREBIRD: FIREBIRD_INFO,
    InstrumentModelId.MODERNE: MODERNE_INFO,
}


def get_spec_by_model_id(model_id: InstrumentModelId):
    """
    Get the InstrumentSpec for a given model ID.
    
    Args:
        model_id: InstrumentModelId enum value
        
    Returns:
        InstrumentSpec for the model
        
    Raises:
        KeyError: If model_id not found in registry
    """
    return MODEL_SPECS[model_id]()


def get_info_by_model_id(model_id: InstrumentModelId):
    """
    Get the MODEL_INFO dict for a given model ID.
    
    Args:
        model_id: InstrumentModelId enum value
        
    Returns:
        Dict with model metadata
        
    Raises:
        KeyError: If model_id not found in registry
    """
    return MODEL_INFOS[model_id]


__all__ = [
    "MODEL_SPECS",
    "MODEL_INFOS",
    "get_spec_by_model_id",
    "get_info_by_model_id",
    # Individual spec getters
    "get_strat_spec",
    "get_tele_spec",
    "get_les_paul_spec",
    "get_dreadnought_spec",
    "get_om_000_spec",
    "get_j_45_spec",
    "get_jazz_bass_spec",
    "get_classical_spec",
    "get_archtop_spec",
    "get_prs_spec",
    "get_sg_spec",
    "get_jumbo_j200_spec",
    "get_ukulele_spec",
    "get_gibson_l_00_spec",
    "get_flying_v_spec",
    "get_es_335_spec",
    "get_explorer_spec",
    "get_firebird_spec",
    "get_moderne_spec",
]
