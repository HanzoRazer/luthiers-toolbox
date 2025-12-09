/**
 * Les Paul Neck Generator - Utility Functions
 * Generates parametric neck geometry for Les Paul style guitars (C-profile)
 */

// Unit conversion constants
const MM_PER_INCH = 25.4
const INCH_PER_MM = 0.03937007874015748

export interface NeckParameters {
  // Blank dimensions
  blank_length: number;
  blank_width: number;
  blank_thickness: number;
  
  // Scale and dimensions
  scale_length: number;
  nut_width: number;
  heel_width: number;
  neck_length: number;
  neck_angle: number;
  
  // Fretboard
  fretboard_radius: number;
  fretboard_offset: number;
  include_fretboard: boolean;
  
  // Profile (C-shape)
  thickness_1st_fret: number;
  thickness_12th_fret: number;
  radius_at_1st: number;
  radius_at_12th: number;
  
  // Headstock
  headstock_angle: number;
  headstock_length: number;
  headstock_thickness: number;
  tuner_layout: number;
  tuner_diameter: number;
  
  // Options
  alignment_pin_holes: boolean;
  
  // Units (optional, defaults to inches)
  units?: 'mm' | 'inch';
}

export interface ValidationWarning {
  field: string;
  message: string;
  severity: 'error' | 'warning';
}

export interface ValidationResult {
  valid: boolean;
  warnings: ValidationWarning[];
}

export interface NeckGeometry {
  profile: Point3D[];
  fretboard?: Point3D[];
  headstock: Point3D[];
  tuner_holes: Circle[];
  centerline: Point3D[];
}

interface Point3D {
  x: number;
  y: number;
  z: number;
}

interface Circle {
  center: Point3D;
  diameter: number;
}

/**
 * Generate Les Paul neck geometry from parameters
 */
export function generateLesPaulNeck(params: NeckParameters): NeckGeometry {
  const geometry: NeckGeometry = {
    profile: [],
    headstock: [],
    tuner_holes: [],
    centerline: []
  };

  // Generate centerline (spine of neck)
  geometry.centerline = generateCenterline(params);

  // Generate neck profile (C-shape cross-sections)
  geometry.profile = generateNeckProfile(params);

  // Generate headstock geometry
  geometry.headstock = generateHeadstock(params);

  // Generate tuner holes
  geometry.tuner_holes = generateTunerHoles(params);

  // Optionally generate fretboard
  if (params.include_fretboard) {
    geometry.fretboard = generateFretboard(params);
  }

  return geometry;
}

/**
 * Generate centerline from nut to heel
 */
function generateCenterline(params: NeckParameters): Point3D[] {
  const points: Point3D[] = [];
  const steps = 100;

  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    const distance = t * params.neck_length;
    
    // Simple linear centerline (can be enhanced with compound curves)
    points.push({
      x: distance,
      y: 0, // Center of neck
      z: 0  // Reference plane
    });
  }

  return points;
}

/**
 * Generate neck profile with C-shape cross-sections
 */
function generateNeckProfile(params: NeckParameters): Point3D[] {
  const points: Point3D[] = [];
  const lengthSteps = 20; // Number of cross-sections along length
  const widthSteps = 30;  // Points per cross-section

  for (let i = 0; i <= lengthSteps; i++) {
    const t = i / lengthSteps;
    const x = t * params.neck_length;
    
    // Interpolate width from nut to heel
    const width = params.nut_width + t * (params.heel_width - params.nut_width);
    
    // Interpolate thickness (at fret positions)
    const fret_t = t * 24; // Approximate fret number
    const thickness = interpolateThickness(fret_t, params);
    
    // Interpolate C-profile radius
    const radius = interpolateRadius(fret_t, params);
    
    // Generate C-shaped cross-section
    for (let j = 0; j <= widthSteps; j++) {
      const w_t = j / widthSteps;
      const y = (w_t - 0.5) * width;
      
      // C-profile: rounded back, flatter sides
      const z = calculateCProfileZ(w_t, thickness, radius);
      
      points.push({ x, y, z });
    }
  }

  return points;
}

/**
 * Calculate Z coordinate for C-profile cross-section
 */
function calculateCProfileZ(t: number, thickness: number, radius: number): number {
  // C-profile is rounded at center, flatter at edges
  // t ranges from 0 (left edge) to 1 (right edge), 0.5 is center
  
  const centerOffset = 0.5;
  const dist = Math.abs(t - centerOffset);
  
  // Parabolic curve for C-shape
  // More material at center, thinner at edges
  const curve = 1 - Math.pow(dist * 2, 1.5);
  
  return -thickness * curve; // Negative Z is back of neck
}

/**
 * Interpolate thickness between 1st and 12th fret
 */
function interpolateThickness(fret: number, params: NeckParameters): number {
  if (fret <= 1) return params.thickness_1st_fret;
  if (fret >= 12) return params.thickness_12th_fret;
  
  const t = (fret - 1) / 11; // Normalize between 1st and 12th
  return params.thickness_1st_fret + t * (params.thickness_12th_fret - params.thickness_1st_fret);
}

/**
 * Interpolate C-profile radius between 1st and 12th fret
 */
function interpolateRadius(fret: number, params: NeckParameters): number {
  if (fret <= 1) return params.radius_at_1st;
  if (fret >= 12) return params.radius_at_12th;
  
  const t = (fret - 1) / 11;
  return params.radius_at_1st + t * (params.radius_at_12th - params.radius_at_1st);
}

/**
 * Generate headstock geometry
 */
function generateHeadstock(params: NeckParameters): Point3D[] {
  const points: Point3D[] = [];
  const steps = 20;
  
  // Headstock starts at nut (x=0) and extends backward
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    const x = -t * params.headstock_length; // Negative X
    
    // Headstock width typically wider than nut
    const width = params.nut_width + t * 0.5; // Gradual taper
    
    // Headstock angle (tilt backward)
    const angle_rad = (params.headstock_angle * Math.PI) / 180;
    const z = -Math.tan(angle_rad) * (t * params.headstock_length);
    
    // Generate cross-section
    for (let j = 0; j <= 10; j++) {
      const w_t = j / 10;
      const y = (w_t - 0.5) * width;
      
      points.push({ x, y, z: z - params.headstock_thickness });
    }
  }
  
  return points;
}

/**
 * Generate tuner hole locations (3+3 configuration for Les Paul)
 */
function generateTunerHoles(params: NeckParameters): Circle[] {
  const holes: Circle[] = [];
  
  // 3+3 configuration: 3 on each side
  const spacing = params.tuner_layout;
  const x_positions = [
    -params.headstock_length * 0.33,
    -params.headstock_length * 0.55,
    -params.headstock_length * 0.77
  ];
  
  const y_offset = params.nut_width * 0.4;
  
  // Left side (bass strings)
  for (const x of x_positions) {
    holes.push({
      center: { x, y: -y_offset, z: 0 },
      diameter: params.tuner_diameter
    });
  }
  
  // Right side (treble strings)
  for (const x of x_positions) {
    holes.push({
      center: { x, y: y_offset, z: 0 },
      diameter: params.tuner_diameter
    });
  }
  
  return holes;
}

/**
 * Generate fretboard geometry
 */
function generateFretboard(params: NeckParameters): Point3D[] {
  const points: Point3D[] = [];
  const numFrets = 22; // Standard Les Paul
  
  // Fret positions using 12th root of 2 (equal temperament)
  const fretConstant = 17.817; // For inches
  
  for (let fret = 0; fret <= numFrets; fret++) {
    const distance = params.scale_length - (params.scale_length / Math.pow(2, fret / 12));
    
    // Fretboard width tapers from nut to heel
    const t = distance / params.neck_length;
    const width = params.nut_width + t * (params.heel_width - params.nut_width);
    
    // Generate fret slot (perpendicular line)
    for (let j = 0; j <= 10; j++) {
      const w_t = j / 10;
      const y = (w_t - 0.5) * width;
      
      // Fretboard has cylindrical radius
      const radius_in = params.fretboard_radius;
      const z = calculateFretboardZ(w_t, radius_in);
      
      points.push({
        x: distance,
        y,
        z: z + params.fretboard_offset
      });
    }
  }
  
  return points;
}

/**
 * Calculate Z for fretboard with cylindrical radius
 */
function calculateFretboardZ(t: number, radius: number): number {
  // t ranges from 0 to 1 across width
  // Cylindrical curve (simpler than compound radius)
  const centerOffset = 0.5;
  const dist = Math.abs(t - centerOffset);
  
  // Circular arc formula
  const chord = dist * 2; // Normalized
  const sagitta = radius - Math.sqrt(Math.pow(radius, 2) - Math.pow(chord * radius, 2));
  
  return sagitta;
}

/**
 * Unit Conversion Utilities
 */
export function mmToInch(mm: number): number {
  return mm * INCH_PER_MM;
}

export function inchToMm(inch: number): number {
  return inch * MM_PER_INCH;
}

/**
 * Convert all dimensional parameters between units
 * Angles (neck_angle, headstock_angle) are NOT converted
 */
export function convertParameters(
  params: Partial<NeckParameters>,
  fromUnits: 'mm' | 'inch',
  toUnits: 'mm' | 'inch'
): Partial<NeckParameters> {
  if (fromUnits === toUnits) {
    return { ...params, units: toUnits };
  }

  const convert = fromUnits === 'mm' ? mmToInch : inchToMm;
  
  // List of dimensional fields to convert (excludes angles and booleans)
  const dimensionalFields: (keyof NeckParameters)[] = [
    'blank_length',
    'blank_width',
    'blank_thickness',
    'scale_length',
    'nut_width',
    'heel_width',
    'neck_length',
    'fretboard_radius',
    'fretboard_offset',
    'thickness_1st_fret',
    'thickness_12th_fret',
    'radius_at_1st',
    'radius_at_12th',
    'headstock_length',
    'headstock_thickness',
    'tuner_layout',
    'tuner_diameter'
  ];

  const converted: any = { ...params, units: toUnits };
  
  dimensionalFields.forEach(field => {
    if (params[field] !== undefined) {
      converted[field] = convert(params[field] as number);
    }
  });

  return converted;
}

/**
 * Parameter Validation Rules (in inches)
 */
interface ValidationRule {
  min: number;
  max: number;
  unit: string;
  critical?: boolean; // If true, violation is an error, not just a warning
}

const VALIDATION_RULES: Record<string, ValidationRule> = {
  scale_length: { min: 20, max: 30, unit: 'inch', critical: true },
  nut_width: { min: 1.5, max: 2.5, unit: 'inch' },
  heel_width: { min: 2.0, max: 3.0, unit: 'inch' },
  blank_length: { min: 20, max: 40, unit: 'inch' },
  blank_width: { min: 2.5, max: 5.0, unit: 'inch' },
  blank_thickness: { min: 0.5, max: 2.0, unit: 'inch' },
  neck_length: { min: 10, max: 20, unit: 'inch' },
  neck_angle: { min: 0, max: 10, unit: 'degrees', critical: true },
  fretboard_radius: { min: 7, max: 20, unit: 'inch' },
  fretboard_offset: { min: 0, max: 0.5, unit: 'inch' },
  thickness_1st_fret: { min: 0.7, max: 1.2, unit: 'inch' },
  thickness_12th_fret: { min: 0.8, max: 1.5, unit: 'inch' },
  radius_at_1st: { min: 0.5, max: 2.0, unit: 'inch' },
  radius_at_12th: { min: 0.5, max: 2.0, unit: 'inch' },
  headstock_angle: { min: 0, max: 25, unit: 'degrees' },
  headstock_length: { min: 6, max: 12, unit: 'inch' },
  headstock_thickness: { min: 0.4, max: 1.0, unit: 'inch' },
  tuner_layout: { min: 2.5, max: 4.0, unit: 'inch' },
  tuner_diameter: { min: 0.25, max: 0.75, unit: 'inch' }
};

/**
 * Validate neck parameters and return warnings/errors
 */
export function validateParameters(params: Partial<NeckParameters>): ValidationResult {
  const warnings: ValidationWarning[] = [];
  let hasErrors = false;

  Object.keys(VALIDATION_RULES).forEach(field => {
    const value = params[field as keyof NeckParameters];
    if (value === undefined || typeof value !== 'number') return;

    const rule = VALIDATION_RULES[field];
    
    // Convert value to inches for validation if params are in mm
    let valueInInches = value;
    if (params.units === 'mm') {
      valueInInches = mmToInch(value);
    }

    if (valueInInches < rule.min || valueInInches > rule.max) {
      const severity = rule.critical ? 'error' : 'warning';
      if (rule.critical) hasErrors = true;

      warnings.push({
        field,
        message: `${field}: ${value.toFixed(3)} ${params.units || 'inch'} is outside valid range (${rule.min}-${rule.max} ${rule.unit})`,
        severity
      });
    }
  });

  // Logical validation: thickness should increase from 1st to 12th fret
  if (params.thickness_1st_fret !== undefined && params.thickness_12th_fret !== undefined) {
    if (params.thickness_12th_fret < params.thickness_1st_fret) {
      warnings.push({
        field: 'thickness_12th_fret',
        message: 'Neck thickness at 12th fret should be >= thickness at 1st fret for proper C-profile',
        severity: 'warning'
      });
    }
  }

  // Logical validation: heel width should be >= nut width
  if (params.nut_width !== undefined && params.heel_width !== undefined) {
    if (params.heel_width < params.nut_width) {
      warnings.push({
        field: 'heel_width',
        message: 'Heel width should be >= nut width for typical neck taper',
        severity: 'warning'
      });
    }
  }

  return {
    valid: !hasErrors,
    warnings
  };
}

/**
 * Export neck geometry as DXF (placeholder - needs ezdxf equivalent in TS)
 */
export function exportNeckAsDXF(geometry: NeckGeometry, filename: string): void {
  console.warn('DXF export not yet implemented in TypeScript. Use Python backend for export.');
  // TODO: Implement DXF export or call Python backend API
}

/**
 * Export neck geometry as JSON for backend processing
 */
export function exportNeckAsJSON(geometry: NeckGeometry): string {
  return JSON.stringify(geometry, null, 2);
}

/**
 * Get default Les Paul parameters
 */
export function getDefaultLesPaulParams(): NeckParameters {
  return {
    blank_length: 30,
    blank_width: 3.25,
    blank_thickness: 1.0,
    scale_length: 24.75,
    nut_width: 1.695,
    heel_width: 2.25,
    neck_length: 18,
    neck_angle: 3.5,
    fretboard_radius: 12,
    thickness_1st_fret: 0.8,
    thickness_12th_fret: 0.9,
    radius_at_1st: 1.25,
    radius_at_12th: 1.5,
    headstock_angle: 13,
    headstock_length: 6,
    headstock_thickness: 0.625,
    tuner_layout: 1.375,
    tuner_diameter: 0.375,
    fretboard_offset: 0.25,
    include_fretboard: true,
    alignment_pin_holes: false
  };
}
