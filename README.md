# PNGTubeRemix Studio MCP

Fork + servidor **MCP** (39 herramientas) + **Agent Skill** (`pngtuber-remix-mcp`) para crear, riggear, animar, inspeccionar visualmente y exportar avatares `.pngRemix` completos con IA — **100% compatibles con el [PNGTuber-Remix](https://github.com/MudkipWorld/PNGTuber-Remix) oficial sin modificar**.

- **Fork del motor:** [sephirods/PNGTuber-Remix (`studio-mcp`)](https://github.com/sephirods/PNGTuber-Remix/tree/studio-mcp)
- **Releases compiladas:** [GitHub Releases](https://github.com/sephirods/pngtuber-remix-mcp/releases)

## Qué incluye

1. **`PNGTubeRemix-Studio-MCP`**: compilación de `PNGTuber-Remix` V1.4.7 con servidor WebSocket en `ws://localhost:9321` encendido automáticamente al iniciar y comandos para importar capas PNG, armar jerarquías, configurar parpadeo/micrófono/mouse-tracking/físicas/estados, simular entradas, capturar pantalla y guardar `.pngRemix` auto-contenidos.
2. **`server.py`**: servidor MCP en Python (`mcp>=2.0`, `websockets`) con 39 herramientas, incluyendo el constructor declarativo `build_rig_from_spec`.
3. **`skills/pngtuber-remix-mcp/`**: Skill lista para Antigravity / agentes con guía de flujo, referencia completa de las 39 herramientas, guía de propiedades y script validador `verify_pngremix.py`.

## Instalación rápida

1. Descarga desde [Releases](https://github.com/sephirods/pngtuber-remix-mcp/releases) el formato que prefieras:
   - **Instalable Windows:** `PNGTubeRemix-Studio-MCP-Windows-x86_64-Installer.exe` (asistente de instalación con accesos directos y desinstalador).
   - **Portable:** `PNGTubeRemix-Studio-MCP-Windows-x86_64-Portable.zip` o `PNGTubeRemix-Studio-MCP-Linux-x86_64-Portable.zip` (extraer y ejecutar).
2. Instala dependencias Python:
   ```bash
   pip install -r requirements.txt
   ```
3. Agrega el servidor a tu `mcp_config.json`:
   ```json
   {
     "mcpServers": {
       "pngtuber-remix": {
         "command": "python",
         "args": ["C:\\ruta\\a\\pngtuber-remix-mcp\\server.py"],
         "env": {
           "PNGTUBER_WS_URL": "ws://localhost:9321"
         }
       }
     }
   }
   ```
4. Para instalar la Skill en tu workspace o agente, copia `skills/pngtuber-remix-mcp/` dentro de `.agents/skills/pngtuber-remix-mcp/` (o `~/.gemini/config/skills/pngtuber-remix-mcp/`).

## Flujo de trabajo para clientes

1. Abre `PNGTube Remix.exe` de la carpeta `PNGTubeRemix-Studio-MCP/` (el WebSocket queda escuchando automáticamente en el puerto `9321`).
2. Pídele a tu agente que diseñe el personaje, lo importe y lo riggee en vivo en tu pantalla.
3. Revisa y pide ajustes en tiempo real (`replace_sprite_image`, `set_sprite_properties`).
4. Exporta un `.pngRemix` único con `save_model` y valídalo con:
   ```bash
   python skills/pngtuber-remix-mcp/scripts/verify_pngremix.py exports/Avatar.pngRemix
   ```
   El cliente abre ese archivo en el **PNGTuber-Remix oficial** sin instalar nada extra.

## Licencia

Ver [LICENSE](LICENSE) (el servidor MCP, la Skill y los ejemplos se distribuyen bajo licencia MIT; el fork del motor y los binarios compilados mantienen la licencia original de [MudkipWorld/PNGTuber-Remix](https://github.com/MudkipWorld/PNGTuber-Remix)).
