# content/ — fuente de verdad del catalogo

Esta carpeta es la **fuente unica de verdad** del catalogo de la tienda.

La base de datos NO se administra a mano: se sincroniza desde aqui con
`python manage.py sync_content`.

## Estructura

```
content/
  categorias/
    <slug-categoria>/
      data.json
      portada.jpg          (opcional)
      <slug-subcategoria>/
        data.json
        portada.jpg        (opcional)
        productos/         (vacio por ahora; productos se cargan luego)
  servicios/
    <slug-servicio>/
      data.json
      portada.jpg          (opcional)
  home/
    <slug-bloque>/
      data.json
      portada.jpg          (opcional)
```

## data.json de una categoria

```json
{
  "name": "CCTV / Videovigilancia",
  "slug": "cctv-videovigilancia",
  "description": "Camaras, DVR, NVR y accesorios para videovigilancia.",
  "icon": "fa-video",
  "order": 1,
  "is_active": true
}
```

## data.json de una subcategoria

```json
{
  "name": "Camaras IP",
  "slug": "camaras-ip",
  "description": "Camaras IP profesionales para vigilancia remota.",
  "order": 1,
  "is_active": true
}
```

El `parent` se infiere de la estructura de carpetas: `cctv-videovigilancia/`
contiene `camaras-ip/`, asi que `camaras-ip` queda con
`parent = cctv-videovigilancia`.

## Comandos

- `python manage.py sync_content` — sincroniza carpetas con BD
- `python manage.py sync_content --dry-run` — muestra que haria sin escribir nada

## Reglas

1. **Carpeta nueva** -> registro creado en BD
2. **JSON modificado** -> registro actualizado
3. **Carpeta eliminada** -> registro marcado `is_active = false` (NO se borra)
4. **Slug debe ser unico globalmente** entre todas las categorias y subcategorias
5. Los productos NO se sincronizan todavia; eso queda para una siguiente fase
