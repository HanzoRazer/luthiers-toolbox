/**
 * CurveLab constants.
 */
import type { FixOptionDef } from './curveLabTypes'

export const FIX_OPTIONS: FixOptionDef[] = [
  {
    id: 'convert_to_r12',
    label: 'Convert to R12',
    helper: 'Ensures exports target AC1009 for maximum CAM compatibility'
  },
  {
    id: 'set_units_mm',
    label: 'Set units to millimeters',
    helper: 'Writes $INSUNITS=mm when file omits unit metadata'
  },
  {
    id: 'close_open_polylines',
    label: 'Close open polylines',
    helper: 'Closes paths with <0.1 mm gap so pocketing works'
  },
  {
    id: 'merge_duplicate_layers',
    label: 'Merge duplicate layers',
    helper: 'Consolidates inconsistently cased layer names'
  },
  {
    id: 'explode_splines',
    label: 'Explode splines',
    helper: 'Converts splines to polylines (experimental)'
  }
]
