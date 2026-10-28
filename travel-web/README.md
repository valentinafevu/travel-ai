# Interfaz de paquetes

Vue 3 + TypeScript + Vite. Consulta la API Django mediante `/api/`; requiere ejecutar
el backend de `../travel-app` en `127.0.0.1:8000`.

Desde la raíz del proyecto, activa micromamba y arranca la interfaz:

```bash
mm activate "$PWD/venv"
cd travel-web
npm install
npm run dev -- --host 127.0.0.1
```

`npm run build` comprueba tipos y genera `dist/`. Las instrucciones de carga del
catálogo, API y pruebas están en [el README principal](../README.md).
