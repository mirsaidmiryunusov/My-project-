/**
 * Chakra UI Theme Configuration for Project GeminiVoiceConnect
 * 
 * This file defines the custom theme with colors, fonts, components,
 * and design tokens for the dashboard application.
 */

import { extendTheme, type ThemeConfig } from '@chakra-ui/react';

// Color palette
const colors = {
  brand: {
    50: '#E6F3FF',
    100: '#BAE0FF',
    200: '#8DCCFF',
    300: '#61B8FF',
    400: '#34A4FF',
    500: '#0890FF', // Primary brand color
    600: '#0673CC',
    700: '#055699',
    800: '#033966',
    900: '#021C33',
  },
  gray: {
    50: '#F7FAFC',
    100: '#EDF2F7',
    200: '#E2E8F0',
    300: '#CBD5E0',
    400: '#A0AEC0',
    500: '#718096',
    600: '#4A5568',
    700: '#2D3748',
    800: '#1A202C',
    900: '#171923',
  },
  success: {
    50: '#F0FFF4',
    100: '#C6F6D5',
    200: '#9AE6B4',
    300: '#68D391',
    400: '#48BB78',
    500: '#38A169',
    600: '#2F855A',
    700: '#276749',
    800: '#22543D',
    900: '#1C4532',
  },
  warning: {
    50: '#FFFBEB',
    100: '#FEF3C7',
    200: '#FDE68A',
    300: '#FCD34D',
    400: '#FBBF24',
    500: '#F59E0B',
    600: '#D97706',
    700: '#B45309',
    800: '#92400E',
    900: '#78350F',
  },
  error: {
    50: '#FEF2F2',
    100: '#FEE2E2',
    200: '#FECACA',
    300: '#FCA5A5',
    400: '#F87171',
    500: '#EF4444',
    600: '#DC2626',
    700: '#B91C1C',
    800: '#991B1B',
    900: '#7F1D1D',
  },
};

// Typography
const fonts = {
  heading: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif',
  body: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif',
  mono: '"Fira Code", "Monaco", "Cascadia Code", "Roboto Mono", Consolas, "Courier New", monospace',
};

const fontSizes = {
  xs: '0.75rem',
  sm: '0.875rem',
  md: '1rem',
  lg: '1.125rem',
  xl: '1.25rem',
  '2xl': '1.5rem',
  '3xl': '1.875rem',
  '4xl': '2.25rem',
  '5xl': '3rem',
  '6xl': '3.75rem',
  '7xl': '4.5rem',
  '8xl': '6rem',
  '9xl': '8rem',
};

// Component styles
const components = {
  Button: {
    baseStyle: {
      fontWeight: 'semibold',
      borderRadius: 'md',
      _focus: {
        boxShadow: 'outline',
      },
    },
    sizes: {
      sm: {
        fontSize: 'sm',
        px: 4,
        py: 2,
      },
      md: {
        fontSize: 'md',
        px: 6,
        py: 3,
      },
      lg: {
        fontSize: 'lg',
        px: 8,
        py: 4,
      },
    },
    variants: {
      solid: {
        bg: 'brand.500',
        color: 'white',
        _hover: {
          bg: 'brand.600',
          _disabled: {
            bg: 'brand.500',
          },
        },
        _active: {
          bg: 'brand.700',
        },
      },
      outline: {
        border: '2px solid',
        borderColor: 'brand.500',
        color: 'brand.500',
        _hover: {
          bg: 'brand.50',
          _disabled: {
            bg: 'transparent',
          },
        },
        _active: {
          bg: 'brand.100',
        },
      },
      ghost: {
        color: 'brand.500',
        _hover: {
          bg: 'brand.50',
          _disabled: {
            bg: 'transparent',
          },
        },
        _active: {
          bg: 'brand.100',
        },
      },
    },
    defaultProps: {
      variant: 'solid',
      size: 'md',
    },
  },
  Card: {
    baseStyle: {
      container: {
        borderRadius: 'lg',
        boxShadow: 'sm',
        border: '1px solid',
        borderColor: 'gray.200',
        _dark: {
          borderColor: 'gray.700',
          bg: 'gray.800',
        },
      },
      header: {
        px: 6,
        py: 4,
        borderBottom: '1px solid',
        borderColor: 'gray.200',
        _dark: {
          borderColor: 'gray.700',
        },
      },
      body: {
        px: 6,
        py: 4,
      },
      footer: {
        px: 6,
        py: 4,
        borderTop: '1px solid',
        borderColor: 'gray.200',
        _dark: {
          borderColor: 'gray.700',
        },
      },
    },
  },
  Input: {
    baseStyle: {
      field: {
        borderRadius: 'md',
        _focus: {
          borderColor: 'brand.500',
          boxShadow: '0 0 0 1px var(--chakra-colors-brand-500)',
        },
      },
    },
    variants: {
      outline: {
        field: {
          border: '2px solid',
          borderColor: 'gray.200',
          _hover: {
            borderColor: 'gray.300',
          },
          _focus: {
            borderColor: 'brand.500',
            boxShadow: '0 0 0 1px var(--chakra-colors-brand-500)',
          },
          _dark: {
            borderColor: 'gray.600',
            _hover: {
              borderColor: 'gray.500',
            },
          },
        },
      },
    },
    defaultProps: {
      variant: 'outline',
    },
  },
  Select: {
    baseStyle: {
      field: {
        borderRadius: 'md',
        _focus: {
          borderColor: 'brand.500',
          boxShadow: '0 0 0 1px var(--chakra-colors-brand-500)',
        },
      },
    },
  },
  Textarea: {
    baseStyle: {
      borderRadius: 'md',
      _focus: {
        borderColor: 'brand.500',
        boxShadow: '0 0 0 1px var(--chakra-colors-brand-500)',
      },
    },
  },
  Badge: {
    baseStyle: {
      borderRadius: 'full',
      fontWeight: 'semibold',
      fontSize: 'xs',
      px: 2,
      py: 1,
    },
    variants: {
      solid: {
        bg: 'brand.500',
        color: 'white',
      },
      outline: {
        border: '1px solid',
        borderColor: 'brand.500',
        color: 'brand.500',
      },
      subtle: {
        bg: 'brand.100',
        color: 'brand.800',
      },
    },
    defaultProps: {
      variant: 'subtle',
    },
  },
  Alert: {
    baseStyle: {
      container: {
        borderRadius: 'md',
        px: 4,
        py: 3,
      },
    },
    variants: {
      solid: {
        container: {
          bg: 'brand.500',
          color: 'white',
        },
      },
      'left-accent': {
        container: {
          borderLeft: '4px solid',
          borderLeftColor: 'brand.500',
          bg: 'brand.50',
          _dark: {
            bg: 'brand.900',
          },
        },
      },
      'top-accent': {
        container: {
          borderTop: '4px solid',
          borderTopColor: 'brand.500',
          bg: 'brand.50',
          _dark: {
            bg: 'brand.900',
          },
        },
      },
      subtle: {
        container: {
          bg: 'brand.50',
          _dark: {
            bg: 'brand.900',
          },
        },
      },
    },
    defaultProps: {
      variant: 'left-accent',
    },
  },
  Table: {
    baseStyle: {
      table: {
        borderCollapse: 'collapse',
      },
      th: {
        fontWeight: 'semibold',
        textTransform: 'uppercase',
        letterSpacing: 'wider',
        fontSize: 'xs',
        color: 'gray.600',
        _dark: {
          color: 'gray.400',
        },
      },
      td: {
        borderBottom: '1px solid',
        borderColor: 'gray.200',
        _dark: {
          borderColor: 'gray.700',
        },
      },
    },
    variants: {
      simple: {
        th: {
          borderBottom: '2px solid',
          borderColor: 'gray.200',
          _dark: {
            borderColor: 'gray.700',
          },
        },
      },
      striped: {
        tbody: {
          tr: {
            '&:nth-of-type(odd)': {
              bg: 'gray.50',
              _dark: {
                bg: 'gray.800',
              },
            },
          },
        },
      },
    },
    defaultProps: {
      variant: 'simple',
      size: 'md',
    },
  },
  Modal: {
    baseStyle: {
      dialog: {
        borderRadius: 'lg',
        boxShadow: 'xl',
      },
      header: {
        fontWeight: 'semibold',
        fontSize: 'lg',
      },
      closeButton: {
        borderRadius: 'md',
      },
    },
  },
  Drawer: {
    baseStyle: {
      dialog: {
        boxShadow: 'xl',
      },
      header: {
        fontWeight: 'semibold',
        fontSize: 'lg',
      },
      closeButton: {
        borderRadius: 'md',
      },
    },
  },
  Menu: {
    baseStyle: {
      list: {
        borderRadius: 'md',
        boxShadow: 'lg',
        border: '1px solid',
        borderColor: 'gray.200',
        _dark: {
          borderColor: 'gray.700',
          bg: 'gray.800',
        },
      },
      item: {
        _hover: {
          bg: 'brand.50',
          _dark: {
            bg: 'brand.900',
          },
        },
        _focus: {
          bg: 'brand.50',
          _dark: {
            bg: 'brand.900',
          },
        },
      },
    },
  },
  Tooltip: {
    baseStyle: {
      borderRadius: 'md',
      fontWeight: 'medium',
      fontSize: 'sm',
      px: 3,
      py: 2,
    },
  },
};

// Global styles
const styles = {
  global: {
    body: {
      bg: 'gray.50',
      color: 'gray.900',
      _dark: {
        bg: 'gray.900',
        color: 'gray.100',
      },
    },
    '*::placeholder': {
      color: 'gray.400',
    },
    '*, *::before, &::after': {
      borderColor: 'gray.200',
      _dark: {
        borderColor: 'gray.700',
      },
    },
  },
};

// Theme configuration
const config: ThemeConfig = {
  initialColorMode: 'light',
  useSystemColorMode: true,
};

// Breakpoints
const breakpoints = {
  sm: '30em',
  md: '48em',
  lg: '62em',
  xl: '80em',
  '2xl': '96em',
};

// Spacing
const space = {
  px: '1px',
  0.5: '0.125rem',
  1: '0.25rem',
  1.5: '0.375rem',
  2: '0.5rem',
  2.5: '0.625rem',
  3: '0.75rem',
  3.5: '0.875rem',
  4: '1rem',
  5: '1.25rem',
  6: '1.5rem',
  7: '1.75rem',
  8: '2rem',
  9: '2.25rem',
  10: '2.5rem',
  12: '3rem',
  14: '3.5rem',
  16: '4rem',
  20: '5rem',
  24: '6rem',
  28: '7rem',
  32: '8rem',
  36: '9rem',
  40: '10rem',
  44: '11rem',
  48: '12rem',
  52: '13rem',
  56: '14rem',
  60: '15rem',
  64: '16rem',
  72: '18rem',
  80: '20rem',
  96: '24rem',
};

// Shadows
const shadows = {
  xs: '0 0 0 1px rgba(0, 0, 0, 0.05)',
  sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  base: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
  xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
  '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
  outline: '0 0 0 3px rgba(66, 153, 225, 0.6)',
  inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
  none: 'none',
  'dark-lg': 'rgba(0, 0, 0, 0.1) 0px 0px 0px 1px, rgba(0, 0, 0, 0.2) 0px 5px 10px, rgba(0, 0, 0, 0.4) 0px 15px 40px',
};

// Create and export the theme
export const theme = extendTheme({
  config,
  colors,
  fonts,
  fontSizes,
  components,
  styles,
  breakpoints,
  space,
  shadows,
});

export default theme;