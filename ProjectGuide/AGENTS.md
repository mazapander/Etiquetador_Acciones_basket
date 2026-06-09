# AGENTS.md

Este repo sigue el sistema de desarrollo definido en `docs/AI_DEV_OPERATING_SYSTEM.md` o en el documento base equivalente del workspace.

## Principios obligatorios

1. Pensar antes de codificar.
2. Simplicidad primero.
3. Cambios quirúrgicos.
4. Ejecución por criterios verificables.

## Reglas

- No tocar código no relacionado.
- No reformatear archivos enteros.
- No crear abstracciones innecesarias.
- Usar patrones existentes.
- Añadir tests cuando se toque lógica.
- Verificar antes de entregar.
- No introducir secretos.
- Si algo es ambiguo, explicitar supuestos antes de implementar.

## Antes de implementar

Devuelve:

```md
## Análisis previo

### Objetivo entendido

### Supuestos

### Riesgos

### Plan mínimo

### Criterios de aceptación
```

## Verificación final

```md
## Verificación realizada

- [ ] Tests backend
- [ ] Build frontend
- [ ] Migraciones
- [ ] Docker compose
- [ ] Prueba manual
- [ ] Revisión de secretos
- [ ] Riesgos pendientes
```

## Contexto IA

Usar contexto mínimo:

1. Issue + archivos concretos.
2. Árbol del repo + archivos relevantes.
3. Módulo completo.
4. Repo comprimido con Repomix.
5. Repo entero solo si es imprescindible.

Comandos útiles:

```bash
npx repomix@latest --compress
npx repomix@latest --token-count-tree 100
npx repomix@latest --include-diffs
npx repomix@latest --include "backend/app/**/*.py,frontend/src/**/*.tsx"
```
