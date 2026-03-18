export const CALCULATOR_REGISTRY = {
  design: [
    'string-tension',
    'lutherie-geometry',
    'stiffness-index',
  ],
  cam: [
    'stiffness-index',
    'string-tension',
  ],
  'art-studio': [
    'stiffness-index',
  ],
  'smart-guitar': [
    'string-tension',
    'lutherie-geometry',
  ],
} as const

export type ModuleKey = keyof typeof CALCULATOR_REGISTRY
