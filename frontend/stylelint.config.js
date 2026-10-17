// Style rules: tokens.css and theme.css are the only places a raw colour, radius, shadow, z-index or
// duration may be written. Every other stylesheet asks for one through var().
const tokenProperties = [
  '/color$/',
  'fill',
  'stroke',
  '/radius$/',
  'box-shadow',
  'z-index',
  'transition-duration',
  'animation-duration',
]

// The functions that write a colour. var() stays allowed.
const colourFunctions = ['rgb', 'rgba', 'hsl', 'hsla', 'hwb', 'lab', 'lch', 'oklab', 'oklch', 'color', 'color-mix', 'light-dark']

export default {
  extends: ['stylelint-config-standard'],
  plugins: ['stylelint-declaration-strict-value'],
  rules: {
    'color-no-hex': true,
    'color-named': 'never',
    'function-disallowed-list': colourFunctions,
    'scale-unlimited/declaration-strict-value': [
      tokenProperties,
      {
        // false, so rgb() and oklch() can't slip through as "functions"
        ignoreFunctions: false,
        expandShorthand: true,
        ignoreValues: ['currentcolor', 'transparent', 'inherit', 'initial', 'unset', 'none', 'auto', '0'],
      },
    ],
  },
  overrides: [
    {
      files: ['src/styles/tokens.css', 'src/styles/theme.css'],
      rules: {
        'color-no-hex': null,
        'function-disallowed-list': null,
        'scale-unlimited/declaration-strict-value': null,
      },
    },
    // The starter page's styles predate these rules. The shell branch replaces them and removes this
    // exemption. Only the rules they fail today are off.
    {
      files: ['src/styles/global.css'],
      rules: { 'color-no-hex': null, 'scale-unlimited/declaration-strict-value': null },
    },
  ],
}
