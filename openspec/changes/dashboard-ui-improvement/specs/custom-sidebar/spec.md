# Custom Sidebar Specification

## Purpose

Rediseño de la barra lateral del dashboard con componentes personalizados, diseño profesional y mejor jerarquía visual.

## ADDED Requirements

### Requirement: Custom Sidebar Container

La sidebar DEBE usar un contenedor custom en lugar de los componentes nativos de Streamlit.

#### Scenario: Custom container renders correctly

- GIVEN la aplicación iniciada
- WHEN la sidebar se renderiza
- THEN DEBE usar un layout basado en `st.container()` con CSS custom
- AND NO debe depender exclusivamente de `st.sidebar.*`

#### Scenario: Sections are collapsible

- GIVEN la sidebar con múltiples secciones
- WHEN el usuario hace click en el encabezado de una sección
- THEN DEBE colapsar/expandir el contenido de esa sección
- AND DEBE mantener el estado de colapso entre interacciones

### Requirement: Professional Visual Design

La sidebar DEBE tener un diseño profesional con jerarquía visual clara.

#### Scenario: Visual hierarchy is clear

- GIVEN la sidebar renderizada
- WHEN el usuario la observa
- THEN DEBE distinguir claramente entre títulos, métricas y acciones
- AND DEBE usar spacing consistente (16px entre secciones)
- AND DEBE usar tipografía con diferentes tamaños para niveles de jerarquía

#### Scenario: Custom color scheme applied

- GIVEN la configuración de tema en config.toml
- WHEN la sidebar se renderiza
- THEN DEBE usar una paleta de colores coherente con el tema oscuro
- AND DEBE usar acentos de steel blue para elementos interactivos
- AND DEBE usar colores diferenciados para estados (verde=éxito, rojo=error, amarillo=advertencia)

### Requirement: Card-Based Metrics Display

Las métricas DEBEN mostrarse en tarjetas visuales en lugar de simples métricas.

#### Scenario: Metrics displayed as cards

- GIVEN la sidebar mostrando documentos o latencia
- WHEN se renderiza cada grupo de métricas
- THEN DEBE mostrar cada métrica en una tarjeta visual
- AND DEBE incluir el valor principal y una etiqueta descriptiva
- AND DEBE usar bordes sutiles o sombra para delimitar las tarjetas

#### Scenario: System status indicator

- GIVEN el estado del sistema (conectado/desconectado)
- WHEN se renderiza en la sidebar
- THEN DEBE mostrar un indicador visual (dot/pill) con color según el estado
- AND DEBE incluir texto descriptivo junto al indicador

### Requirement: Sidebar Actions Section

La sidebar DEBE incluir una sección de acciones bien diseñada.

#### Scenario: Action buttons styled consistently

- GIVEN los botones de "Reiniciar Chat" y "Re-indexar Datos"
- WHEN se renderizan en la sidebar
- THEN DEBEN tener estilos consistentes con el resto de la UI
- AND DEBEN tener estados hover y active visibles
- AND DEBEN tener confirmación antes de ejecutar acciones destructivas

### Requirement: Responsive Sidebar Width

La sidebar DEBE adaptarse al ancho de pantalla disponible.

#### Scenario: Sidebar fits in narrow screens

- GIVEN la aplicación en una pantalla menor a 768px de ancho
- WHEN se renderiza la sidebar
- THEN DEBE reducir su contenido a lo esencial
- AND DEBE mantener la accesibilidad de las métricas principales