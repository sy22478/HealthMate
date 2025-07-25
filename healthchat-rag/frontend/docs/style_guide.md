# HealthChat RAG Dashboard - Style Guide

## Overview
This style guide defines the design system, visual standards, and component styling guidelines for the HealthChat RAG Dashboard. It ensures consistency across all components and provides a foundation for future development.

## Table of Contents
1. [Color Palette](#color-palette)
2. [Typography](#typography)
3. [Spacing and Layout](#spacing-and-layout)
4. [Component Styling](#component-styling)
5. [Icons and Visual Elements](#icons-and-visual-elements)
6. [Responsive Design](#responsive-design)
7. [Accessibility](#accessibility)
8. [Theme System](#theme-system)

---

## Color Palette

### Primary Colors
```css
/* Primary Blue */
--primary-color: #1f77b4;
--primary-light: #4a9bd4;
--primary-dark: #0d5a8a;

/* Secondary Orange */
--secondary-color: #ff7f0e;
--secondary-light: #ffa040;
--secondary-dark: #cc6600;
```

### Semantic Colors
```css
/* Success Green */
--success-color: #2ca02c;
--success-light: #4caf50;
--success-dark: #1b5e20;

/* Warning Red */
--warning-color: #d62728;
--warning-light: #f44336;
--warning-dark: #b71c1c;

/* Info Cyan */
--info-color: #17a2b8;
--info-light: #00bcd4;
--info-dark: #006064;

/* Neutral Grays */
--gray-100: #f8f9fa;
--gray-200: #e9ecef;
--gray-300: #dee2e6;
--gray-400: #ced4da;
--gray-500: #adb5bd;
--gray-600: #6c757d;
--gray-700: #495057;
--gray-800: #343a40;
--gray-900: #212529;
```

### Usage Guidelines
- **Primary Blue**: Main actions, navigation, primary buttons
- **Secondary Orange**: Secondary actions, highlights, CTAs
- **Success Green**: Positive feedback, completed actions
- **Warning Red**: Errors, warnings, destructive actions
- **Info Cyan**: Information, help text, tooltips
- **Neutral Grays**: Text, backgrounds, borders

---

## Typography

### Font Stack
```css
--font-family-primary: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
--font-family-mono: 'Fira Code', 'Consolas', 'Monaco', monospace;
```

### Font Sizes
```css
/* Heading Sizes */
--font-size-h1: 2.5rem;    /* 40px */
--font-size-h2: 2rem;      /* 32px */
--font-size-h3: 1.75rem;   /* 28px */
--font-size-h4: 1.5rem;    /* 24px */
--font-size-h5: 1.25rem;   /* 20px */
--font-size-h6: 1rem;      /* 16px */

/* Body Text */
--font-size-large: 1.125rem;   /* 18px */
--font-size-base: 1rem;        /* 16px */
--font-size-small: 0.875rem;   /* 14px */
--font-size-xs: 0.75rem;       /* 12px */
```

### Font Weights
```css
--font-weight-light: 300;
--font-weight-normal: 400;
--font-weight-medium: 500;
--font-weight-semibold: 600;
--font-weight-bold: 700;
```

### Line Heights
```css
--line-height-tight: 1.25;
--line-height-normal: 1.5;
--line-height-relaxed: 1.75;
```

### Usage Guidelines
- **H1**: Page titles, main headings
- **H2**: Section headings
- **H3**: Subsection headings
- **H4-H6**: Component headings, card titles
- **Body**: Regular text content
- **Small**: Captions, metadata, secondary text

---

## Spacing and Layout

### Spacing Scale
```css
--spacing-xs: 0.25rem;     /* 4px */
--spacing-sm: 0.5rem;      /* 8px */
--spacing-md: 1rem;        /* 16px */
--spacing-lg: 1.5rem;      /* 24px */
--spacing-xl: 2rem;        /* 32px */
--spacing-2xl: 3rem;       /* 48px */
--spacing-3xl: 4rem;       /* 64px */
```

### Layout Grid
```css
/* Container */
--container-max-width: 1200px;
--container-padding: 1rem;

/* Grid System */
--grid-columns: 12;
--grid-gap: 1rem;

/* Breakpoints */
--breakpoint-sm: 576px;
--breakpoint-md: 768px;
--breakpoint-lg: 992px;
--breakpoint-xl: 1200px;
```

### Usage Guidelines
- **Consistent Spacing**: Use the spacing scale for all margins and padding
- **Grid System**: Use 12-column grid for layout
- **Responsive**: Adapt spacing for different screen sizes
- **Visual Hierarchy**: Use spacing to create visual hierarchy

---

## Component Styling

### Buttons
```css
/* Primary Button */
.btn-primary {
    background-color: var(--primary-color);
    color: white;
    padding: 0.75rem 1.5rem;
    border-radius: 0.375rem;
    border: none;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.2s;
}

.btn-primary:hover {
    background-color: var(--primary-dark);
}

/* Secondary Button */
.btn-secondary {
    background-color: transparent;
    color: var(--primary-color);
    border: 1px solid var(--primary-color);
    padding: 0.75rem 1.5rem;
    border-radius: 0.375rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
}

.btn-secondary:hover {
    background-color: var(--primary-color);
    color: white;
}
```

### Cards
```css
.card {
    background-color: white;
    border-radius: 0.5rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    padding: 1.5rem;
    border: 1px solid var(--gray-200);
}

.card-header {
    border-bottom: 1px solid var(--gray-200);
    padding-bottom: 1rem;
    margin-bottom: 1rem;
}

.card-title {
    font-size: var(--font-size-h5);
    font-weight: var(--font-weight-semibold);
    color: var(--gray-900);
    margin: 0;
}
```

### Forms
```css
.form-group {
    margin-bottom: 1rem;
}

.form-label {
    display: block;
    font-weight: var(--font-weight-medium);
    color: var(--gray-700);
    margin-bottom: 0.5rem;
}

.form-input {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid var(--gray-300);
    border-radius: 0.375rem;
    font-size: var(--font-size-base);
    transition: border-color 0.2s;
}

.form-input:focus {
    outline: none;
    border-color: var(--primary-color);
    box-shadow: 0 0 0 3px rgba(31, 119, 180, 0.1);
}
```

### Tables
```css
.table {
    width: 100%;
    border-collapse: collapse;
    background-color: white;
    border-radius: 0.5rem;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.table th {
    background-color: var(--gray-100);
    padding: 1rem;
    text-align: left;
    font-weight: var(--font-weight-semibold);
    color: var(--gray-700);
    border-bottom: 1px solid var(--gray-200);
}

.table td {
    padding: 1rem;
    border-bottom: 1px solid var(--gray-200);
    color: var(--gray-800);
}

.table tr:hover {
    background-color: var(--gray-50);
}
```

---

## Icons and Visual Elements

### Icon System
```css
/* Icon Sizes */
--icon-size-xs: 0.75rem;   /* 12px */
--icon-size-sm: 1rem;      /* 16px */
--icon-size-md: 1.25rem;   /* 20px */
--icon-size-lg: 1.5rem;    /* 24px */
--icon-size-xl: 2rem;      /* 32px */
```

### Icon Guidelines
- **Consistent Style**: Use the same icon family throughout
- **Semantic Meaning**: Icons should have clear semantic meaning
- **Accessibility**: Provide alt text for icons
- **Sizing**: Use appropriate icon sizes for context

### Visual Elements
```css
/* Shadows */
--shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
--shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
--shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);

/* Border Radius */
--radius-sm: 0.25rem;      /* 4px */
--radius-md: 0.375rem;     /* 6px */
--radius-lg: 0.5rem;       /* 8px */
--radius-xl: 0.75rem;      /* 12px */
```

---

## Responsive Design

### Breakpoint System
```css
/* Mobile First Approach */
@media (min-width: 576px) {
    /* Small devices */
}

@media (min-width: 768px) {
    /* Medium devices */
}

@media (min-width: 992px) {
    /* Large devices */
}

@media (min-width: 1200px) {
    /* Extra large devices */
}
```

### Responsive Guidelines
- **Mobile First**: Design for mobile devices first
- **Progressive Enhancement**: Add features for larger screens
- **Touch Friendly**: Ensure touch targets are at least 44px
- **Readable Text**: Maintain readable font sizes on all devices

---

## Accessibility

### Color Contrast
```css
/* Minimum contrast ratios */
--contrast-ratio-normal: 4.5:1;
--contrast-ratio-large: 3:1;
```

### Focus States
```css
.focus-visible {
    outline: 2px solid var(--primary-color);
    outline-offset: 2px;
}
```

### Accessibility Guidelines
- **Color Contrast**: Maintain WCAG 2.1 AA compliance
- **Keyboard Navigation**: All interactive elements must be keyboard accessible
- **Screen Readers**: Provide proper ARIA labels and descriptions
- **Focus Management**: Ensure logical tab order and visible focus indicators

---

## Theme System

### Light Theme
```css
[data-theme="light"] {
    --bg-primary: #ffffff;
    --bg-secondary: var(--gray-100);
    --text-primary: var(--gray-900);
    --text-secondary: var(--gray-600);
    --border-color: var(--gray-200);
}
```

### Dark Theme
```css
[data-theme="dark"] {
    --bg-primary: var(--gray-900);
    --bg-secondary: var(--gray-800);
    --text-primary: var(--gray-100);
    --text-secondary: var(--gray-400);
    --border-color: var(--gray-700);
}
```

### Theme Switching
```javascript
// Theme switching functionality
function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}
```

---

## CSS Variables Usage

### Global Variables
```css
:root {
    /* Import all variables defined above */
    --primary-color: #1f77b4;
    --secondary-color: #ff7f0e;
    /* ... other variables */
}
```

### Component-Specific Variables
```css
.card {
    --card-padding: var(--spacing-lg);
    --card-border-radius: var(--radius-lg);
    --card-shadow: var(--shadow-md);
}
```

---

## Best Practices

### CSS Organization
1. **Reset/Normalize**: Start with CSS reset
2. **Variables**: Define CSS custom properties
3. **Base Styles**: Typography, colors, spacing
4. **Layout**: Grid system, containers
5. **Components**: Individual component styles
6. **Utilities**: Helper classes
7. **Themes**: Theme-specific overrides

### Performance
1. **Minimize CSS**: Remove unused styles
2. **Optimize Selectors**: Use efficient CSS selectors
3. **Reduce Repaints**: Use transform and opacity for animations
4. **Critical CSS**: Inline critical styles

### Maintenance
1. **Consistent Naming**: Use BEM or similar methodology
2. **Documentation**: Document complex CSS
3. **Version Control**: Track CSS changes
4. **Testing**: Test across browsers and devices

---

## Implementation Examples

### Streamlit Integration
```python
# Using CSS variables in Streamlit
st.markdown("""
<style>
.custom-button {
    background-color: var(--primary-color);
    color: white;
    padding: 0.75rem 1.5rem;
    border-radius: var(--radius-md);
    border: none;
    font-weight: var(--font-weight-medium);
    cursor: pointer;
}
</style>
""", unsafe_allow_html=True)
```

### Component Styling
```python
# Component with consistent styling
def styled_card(title, content):
    st.markdown(f"""
    <div class="card">
        <div class="card-header">
            <h3 class="card-title">{title}</h3>
        </div>
        <div class="card-content">
            {content}
        </div>
    </div>
    """, unsafe_allow_html=True)
```

---

## Version History

### v1.0.0 (Current)
- Initial style guide
- Color palette definition
- Typography system
- Component styling guidelines
- Responsive design principles
- Accessibility standards

### Future Enhancements
- Advanced theming system
- Animation guidelines
- Micro-interactions
- Advanced accessibility features
- Design token system 