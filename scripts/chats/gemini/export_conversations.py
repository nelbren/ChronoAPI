import os
import json
import re
import datetime
import platform
import argparse
import shutil


# Detect Operating System & Default Paths
def get_os_indicator():
    os_name = platform.system()
    if os_name == "Darwin":
        return "🍏 macOS"
    elif os_name == "Windows":
        return "💻 Windows"
    elif os_name == "Linux":
        return "🐧 Linux"
    else:
        return f"❓ {os_name}"


# Default paths resolved dynamically
DEFAULT_BRAIN_DIR = os.path.join(
    os.path.expanduser("~"), ".gemini", "antigravity", "brain"
)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_WORKSPACE_DIR = os.path.abspath(
    os.path.join(SCRIPT_DIR, "..", "..", "..")
)
DEFAULT_OUTPUT_DIR = os.path.join(
    DEFAULT_WORKSPACE_DIR, "docs", "chat_history"
)


def load_metadata(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error cargando metadatos desde {filepath}: {e}")
    return {}


def save_metadata(filepath, metadata):
    try:
        # Sort metadata by keys to keep it clean and Git-friendly
        sorted_meta = dict(sorted(metadata.items()))
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(sorted_meta, f, ensure_ascii=False, indent=4)
        print(f"Metadatos guardados con éxito en {filepath}")
    except Exception as e:
        print(f"Error guardando metadatos en {filepath}: {e}")


def clean_user_request(text):
    if not text:
        return ""
    # Extract text between <USER_REQUEST> tags if present
    req_match = re.search(
        r"<USER_REQUEST>(.*?)</USER_REQUEST>", text, re.DOTALL
    )
    if req_match:
        text = req_match.group(1)

    # Remove metadata block if present
    text = re.sub(
        r"<ADDITIONAL_METADATA>.*?</ADDITIONAL_METADATA>",
        "",
        text,
        flags=re.DOTALL,
    )

    return text.strip()


def format_timestamp_local(iso_str):
    if not iso_str:
        return "N/A"
    try:
        # Parse ISO string as UTC
        dt = datetime.datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        # America/Tegucigalpa is UTC-6
        tz_honduras = datetime.timezone(datetime.timedelta(hours=-6))
        dt_local = dt.astimezone(tz_honduras)
        suffix = " (America/Tegucigalpa)"
        return dt_local.strftime("%Y-%m-%d %H:%M:%S") + suffix
    except Exception:
        return iso_str


def get_now_local_str():
    tz_honduras = datetime.timezone(datetime.timedelta(hours=-6))
    now = datetime.datetime.now(tz_honduras)
    return now.strftime("%Y-%m-%d %H:%M:%S") + " (America/Tegucigalpa)"


def parse_transcript(logs_path):
    history = []
    if not os.path.exists(logs_path):
        return history

    with open(logs_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line)
                source = data.get("source")
                type_ = data.get("type")
                content = data.get("content", "")
                created_at = data.get("created_at")
                tool_calls = data.get("tool_calls", [])

                # Check for User requests
                if source == "USER_EXPLICIT" or type_ == "USER_INPUT":
                    cleaned = clean_user_request(content)
                    if cleaned:
                        history.append({
                            "role": "Usuario",
                            "timestamp": format_timestamp_local(created_at),
                            "raw_timestamp": created_at,
                            "content": cleaned
                        })
                # Check for Model responses
                elif (
                    source == "MODEL"
                    and type_ == "PLANNER_RESPONSE"
                    and content
                    and not tool_calls
                ):
                    history.append({
                        "role": "Asistente",
                        "timestamp": format_timestamp_local(created_at),
                        "raw_timestamp": created_at,
                        "content": content.strip()
                    })
            except Exception:
                # Silently skip lines with parsing issues
                continue

    return history


def normalize_markdown(text):
    # 1. Clean trailing whitespace from every line (fixes MD009)
    lines = [line.rstrip() for line in text.splitlines()]

    # 2. Collapse consecutive empty blockquote/normal lines (fixes MD012)
    collapsed = []
    for line in lines:
        # Extract blockquote prefix
        bq_match = re.match(r"^(\s*>\s*)(.*)$", line)
        if bq_match:
            prefix = bq_match.group(1)
            actual = bq_match.group(2)
        else:
            prefix = ""
            actual = line

        if not actual.strip():
            # Empty line or empty blockquote line
            if collapsed:
                prev_line = collapsed[-1]
                prev_bq = re.match(r"^(\s*>\s*)(.*)$", prev_line)
                prev_actual = prev_bq.group(2) if prev_bq else prev_line
                if not prev_actual.strip():
                    continue  # Collapse duplicates
            collapsed.append(prefix.rstrip() if prefix else "")
        else:
            collapsed.append(line)

    # 3. Handle headings, lists, and fences
    final_lines = []
    in_fence = False
    seen_headings = {}

    for idx, line in enumerate(collapsed):
        # Extract prefix and actual content
        bq_match = re.match(r"^(\s*>\s*)(.*)$", line)
        if bq_match:
            prefix = bq_match.group(1)
            actual = bq_match.group(2)
        else:
            prefix = ""
            actual = line

        is_fence_line = re.match(r"^\s*```", actual) is not None
        if is_fence_line:
            in_fence = not in_fence

        is_list_item = (
            not in_fence
            and re.match(r"^\s*([\*\-\+QC]|\d+\.)\s", actual) is not None
        )

        # Convert dash list items to asterisks (MD004)
        if not in_fence and re.match(r"^(\s*)-\s+", actual):
            actual = re.sub(r"^(\s*)-\s+", r"\1* ", actual)
            line = prefix + actual

        is_heading = (
            not in_fence
            and re.match(r"^(#{1,6})\s+(.*)$", actual) is not None
        )

        # Clean headings and enforce unique headings (MD024/MD026)
        if is_heading:
            pfx, heading_text = re.match(r"^(#{1,6})\s+(.*)$", actual).groups()
            heading_text = re.sub(r"([.:,;!?]+)$", "", heading_text).strip()

            heading_key = heading_text.lower().strip()
            if heading_key in seen_headings:
                seen_headings[heading_key] += 1
                heading_text = f"{heading_text} ({seen_headings[heading_key]})"
            else:
                seen_headings[heading_key] = 1
            actual = f"{pfx} {heading_text}"
            line = prefix + actual

        # Ensure blank line BEFORE heading (MD022),
        # fence start (MD031), or list start (MD032)
        if final_lines:
            prev_line = final_lines[-1]
            prev_bq = re.match(r"^(\s*>\s*)(.*)$", prev_line)
            prev_actual = prev_bq.group(2) if prev_bq else prev_line
            prev_is_list = (
                re.match(r"^\s*([\*\-\+QC]|\d+\.)\s", prev_actual) is not None
            )

            need_blank = False
            if is_heading and prev_actual.strip() != "":
                need_blank = True
            elif is_fence_line and in_fence and prev_actual.strip() != "":
                need_blank = True
            elif (
                is_list_item
                and not prev_is_list
                and prev_actual.strip() != ""
            ):
                need_blank = True

            if need_blank:
                final_lines.append(prefix.rstrip() if prefix else "")

        final_lines.append(line)

    # 4. Handle blank lines AFTER headings, fences, and lists
    post_lines = []
    in_fence = False
    for idx, line in enumerate(final_lines):
        bq_match = re.match(r"^(\s*>\s*)(.*)$", line)
        if bq_match:
            prefix = bq_match.group(1)
            actual = bq_match.group(2)
        else:
            prefix = ""
            actual = line

        is_fence_line = re.match(r"^\s*```", actual) is not None
        if is_fence_line:
            in_fence = not in_fence

        post_lines.append(line)

        if idx < len(final_lines) - 1:
            next_line = final_lines[idx + 1]
            next_bq = re.match(r"^(\s*>\s*)(.*)$", next_line)
            next_actual = next_bq.group(2) if next_bq else next_line

            is_heading = (
                not in_fence and re.match(r"^#{1,6}\s", actual) is not None
            )
            is_fence_end = is_fence_line and not in_fence
            is_list_item = (
                not in_fence
                and re.match(r"^\s*([\*\-\+QC]|\d+\.)\s", actual) is not None
            )
            next_is_list = (
                not in_fence
                and re.match(r"^\s*([\*\-\+QC]|\d+\.)\s", next_actual)
                is not None
            )

            if next_actual.strip() != "":
                need_blank = False
                if is_heading:
                    need_blank = True
                elif is_fence_end:
                    need_blank = True
                elif is_list_item and not next_is_list:
                    need_blank = True

                if need_blank:
                    post_lines.append(prefix.rstrip() if prefix else "")

    # MD047: Ensure single trailing newline
    while post_lines and not post_lines[-1].strip():
        post_lines.pop()
    post_lines.append("")

    return "\n".join(post_lines)


def export_chats(brain_dir, output_dir, force=False):
    if not os.path.exists(brain_dir):
        print(
            "El directorio de origen de Antigravity (brain) no existe: "
            f"{brain_dir}"
        )
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Creado directorio de salida: {output_dir}")

    # Load persistent conversation metadata from workspace
    metadata_path = os.path.join(output_dir, "metadata.json")
    convo_metadata = load_metadata(metadata_path)
    metadata_changed = False

    convo_folders = os.listdir(brain_dir)
    print(f"Buscando conversaciones en {brain_dir}...")
    print(f"Directorios encontrados: {len(convo_folders)}")

    exported_count = 0

    for cid in convo_folders:
        logs_path = os.path.join(
            brain_dir, cid, ".system_generated", "logs", "transcript.jsonl"
        )
        if not os.path.exists(logs_path):
            continue

        filename = f"chat_{cid}.md"
        filepath = os.path.join(output_dir, filename)

        # Check for incremental export based on modified times (mtime)
        if os.path.exists(filepath) and not force:
            transcript_mtime = os.path.getmtime(logs_path)
            export_mtime = os.path.getmtime(filepath)
            if export_mtime >= transcript_mtime:
                print(
                    f"La conversación {cid} no ha cambiado desde la última "
                    "exportación. Saltando..."
                )
                continue

        print(f"Procesando conversación {cid}...")
        history = parse_transcript(logs_path)

        if not history:
            print(f"No se encontró historial en {cid}, saltando...")
            continue

        # Get metadata from JSON, fallback to dynamic extraction if not found
        meta = convo_metadata.get(cid)
        if not meta:
            # Generate dynamic title and description from the history
            first_user_msg = ""
            for entry in history:
                if entry["role"] == "Usuario":
                    first_user_msg = entry["content"]
                    break

            if first_user_msg:
                # Split by lines and take first non-empty line for title
                lines = [
                    msg_line.strip()
                    for msg_line in first_user_msg.splitlines()
                    if msg_line.strip()
                ]
                first_line = lines[0] if lines else "Conversación"

                # Truncate title if too long
                if len(first_line) > 70:
                    title = first_line[:67] + "..."
                else:
                    title = first_line

                # Clean up title: capitalize first letter,
                # remove trailing punctuation
                title = title.strip()
                if title.endswith((".", ",")):
                    title = title[:-1]

                # Generate description: replace consecutive newlines
                # and spaces with single space
                desc_clean = re.sub(r"\s+", " ", first_user_msg).strip()
                if len(desc_clean) > 160:
                    description = desc_clean[:157] + "..."
                else:
                    description = desc_clean
            else:
                title = f"Conversación {cid[:8]}"
                description = "Conversación grabada del historial."

            # Save the dynamically generated metadata persistently
            convo_metadata[cid] = {
                "title": title,
                "description": description
            }
            metadata_changed = True
        else:
            title = meta["title"]
            description = meta["description"]

        start_time_formatted = (
            history[0]["timestamp"] if history[0]["timestamp"] else "N/A"
        )
        start_time_utc = (
            history[0]["raw_timestamp"] if history[0]["raw_timestamp"] else ""
        )

        # Build Markdown File Content
        content_lines = []
        content_lines.append(f"# 💬 {title}")
        content_lines.append("")
        content_lines.append(f"<!-- start_time_utc: {start_time_utc} -->")
        content_lines.append(f"> **ID de Conversación:** `{cid}`")
        content_lines.append(">")
        content_lines.append(f"> **Descripción:** {description}")
        content_lines.append(">")
        content_lines.append(f"> **Fecha de Inicio:** {start_time_formatted}")
        content_lines.append(">")
        content_lines.append("> **Herramienta IA:** 🤖 Antigravity (Gemini)")
        content_lines.append(">")
        content_lines.append(f"> **Sistema Operativo:** {get_os_indicator()}")
        content_lines.append(">")
        content_lines.append(f"> **Generado el:** {get_now_local_str()}")
        content_lines.append("")
        content_lines.append("---")
        content_lines.append("")

        # Scan for media files in the conversation directory
        media_files = []
        convo_dir = os.path.join(brain_dir, cid)
        if os.path.exists(convo_dir):
            for f in os.listdir(convo_dir):
                fpath = os.path.join(convo_dir, f)
                if os.path.isfile(fpath):
                    ext = os.path.splitext(f.lower())[1]
                    if ext in (".png", ".jpg", ".jpeg", ".gif", ".webp"):
                        media_ts = None
                        match = re.search(r"media__(\d+)", f)
                        if match:
                            try:
                                media_ts = float(match.group(1)) / 1000.0
                            except ValueError:
                                pass
                        if media_ts is None:
                            media_ts = os.path.getmtime(fpath)
                        media_files.append({
                            "filename": f,
                            "filepath": fpath,
                            "timestamp": media_ts,
                            "ext": ext
                        })

        # Merge history entries and media files chronologically
        items = []
        for entry in history:
            raw_ts = entry.get("raw_timestamp")
            ts = 0.0
            if raw_ts:
                try:
                    dt = datetime.datetime.fromisoformat(
                        raw_ts.replace("Z", "+00:00")
                    )
                    ts = dt.timestamp()
                except Exception:
                    pass
            items.append({
                "type": "message",
                "timestamp": ts,
                "data": entry
            })

        for media in media_files:
            items.append({
                "type": "media",
                "timestamp": media["timestamp"],
                "data": media
            })

        items.sort(key=lambda x: x["timestamp"])

        for item in items:
            if item["type"] == "message":
                entry = item["data"]
                role = entry["role"]
                timestamp = entry["timestamp"]
                content = entry["content"]

                # Level 2 Headings used for perfect heading increment (MD001)
                if role == "Usuario":
                    content_lines.append(f"## 👤 Usuario ({timestamp})")
                    content_lines.append("")
                    content_lines.append("```text")
                    content_lines.append(content)
                    content_lines.append("```")
                else:
                    content_lines.append(f"## 🤖 Antigravity AI ({timestamp})")
                    content_lines.append("")
                    content_lines.append(content)

                content_lines.append("")
                content_lines.append("---")
                content_lines.append("")
            elif item["type"] == "media":
                media = item["data"]
                orig_filename = media["filename"]
                media_filepath = media["filepath"]

                # Prevent collisions by prefixing if it doesn't start
                # with media__
                if orig_filename.startswith("media__"):
                    target_filename = orig_filename
                else:
                    target_filename = f"{cid[:8]}_{orig_filename}"

                images_dir = os.path.join(output_dir, "images")
                if not os.path.exists(images_dir):
                    os.makedirs(images_dir)
                    print(f"Creado directorio de imágenes: {images_dir}")

                dest_filepath = os.path.join(images_dir, target_filename)

                try:
                    shutil.copy2(media_filepath, dest_filepath)
                except Exception as e:
                    print(
                        f"Error al copiar la imagen {orig_filename} "
                        f"a {dest_filepath}: {e}"
                    )

                # Format local timestamp for media block
                tz_honduras = datetime.timezone(datetime.timedelta(hours=-6))
                media_dt = datetime.datetime.fromtimestamp(
                    media["timestamp"], tz=datetime.timezone.utc
                ).astimezone(tz_honduras)
                media_time_str = (
                    media_dt.strftime("%Y-%m-%d %H:%M:%S")
                    + " (America/Tegucigalpa)"
                )

                # Level 3 Heading to fit MD001 perfect heading increment
                content_lines.append(
                    f"### 🖼️ Imagen Adjunta ({media_time_str})"
                )
                content_lines.append("")
                content_lines.append(
                    f"![{target_filename}](images/{target_filename})"
                )
                content_lines.append("")
                content_lines.append("---")
                content_lines.append("")

        raw_markdown = "\n".join(content_lines)
        normalized_markdown = normalize_markdown(raw_markdown)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(normalized_markdown)

        print(f"Exportada con éxito a {filepath}")
        exported_count += 1

    # Save metadata back to JSON if new conversations were dynamically added
    if metadata_changed:
        save_metadata(metadata_path, convo_metadata)

    print(
            "Exportación de chats finalizada. Total exportados/actualizados: "
            f"{exported_count}"
        )


def generate_toc(output_dir):
    if not os.path.exists(output_dir):
        print(
            f"El directorio de salida {output_dir} no existe. "
            "No hay chats para generar TOC."
        )
        return

    print(
        "Generando Tabla de Contenidos (TOC) a partir de los "
        "archivos Markdown existentes..."
    )

    chat_files = [
        f for f in os.listdir(output_dir)
        if f.startswith("chat_") and f.endswith(".md")
    ]
    print(f"Archivos de chat encontrados en docs: {len(chat_files)}")

    exported_convos = []

    for filename in chat_files:
        filepath = os.path.join(output_dir, filename)

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract Title from `# 💬 Title`
            title_match = re.search(r"# 💬\s*(.*?)\n", content)
            title = title_match.group(1).strip() if title_match else filename

            # Extract ID from `ID de Conversación: `
            cid_match = re.search(
                r">\s*\*\*ID de Conversación:\*\*\s*`(.*?)`", content
            )
            cid = (
                cid_match.group(1).strip() if cid_match
                else filename.replace("chat_", "").replace(".md", "")
            )

            # Extract Description
            desc_match = re.search(
                r">\s*\*\*Descripción:\*\*\s*(.*?)\n", content
            )
            description = (
                desc_match.group(1).strip() if desc_match
                else "Conversación grabada del historial."
            )

            # Extract Start Time Formatted
            start_time_match = re.search(
                r">\s*\*\*Fecha de Inicio:\*\*\s*(.*?)\n", content
            )
            if start_time_match:
                start_time_formatted = start_time_match.group(1).strip()
            else:
                first_user_match = re.search(r"## 👤 Usuario \((.*)\)", content)
                start_time_formatted = (
                    first_user_match.group(1).strip() if first_user_match
                    else "N/A"
                )

            # Extract UTC Start Time for exact sorting
            utc_match = re.search(r"<!-- start_time_utc: (.*?) -->", content)
            start_time_utc = (
                utc_match.group(1).strip() if utc_match
                else start_time_formatted
            )

            # Extract OS
            os_match = re.search(
                r">\s*\*\*Sistema Operativo:\*\*\s*(.*?)\n", content
            )
            if os_match:
                os_indicator = os_match.group(1).strip()
            else:
                # Guess OS based on content paths for legacy files
                if (
                    "C:\\" in content or "c:\\" in content
                    or "C:/" in content or "c:/" in content
                ):
                    os_indicator = "💻 Windows"
                elif "/Users/" in content:
                    os_indicator = "🍏 macOS"
                else:
                    os_indicator = "❓ Desconocido"

            # Extract IA Tool
            ia_tool_match = re.search(
                r">\s*\*\*Herramienta IA:\*\*\s*(.*?)\n", content
            )
            if ia_tool_match:
                ia_tool = ia_tool_match.group(1).strip()
            else:
                ia_tool = "🤖 Antigravity (Gemini)"

            # Count messages (occurrences of standard headers)
            messages_count = len(
                re.findall(r"## 👤 Usuario|## 🤖 Antigravity AI", content)
            )

            exported_convos.append({
                "id": cid,
                "title": title,
                "description": description,
                "filename": filename,
                "messages_count": messages_count,
                "start_time": start_time_utc,
                "start_time_formatted": start_time_formatted,
                "ia_tool": ia_tool,
                "os": os_indicator
            })
        except Exception as e:
            print(f"Error al procesar {filename} para el TOC: {e}")

    # Sort conversations by start_time (ascending - oldest to newest)
    exported_convos.sort(key=lambda x: x["start_time"])

    # Write Index file
    index_path = os.path.join(output_dir, "index.md")

    index_lines = []
    index_lines.append("# 📚 Historial de Conversaciones y Pláticas")
    index_lines.append("")
    index_lines.append("## ⬆️🙃 BOF")
    index_lines.append("")
    index_lines.append("> [!NOTE]")
    index_lines.append("> **Tipo de Cuenta:** 🆓 **Gemini (Gratis)**")
    index_lines.append(">")
    index_lines.append(
        "> **Modelo Utilizado:** `Gemini 3.5 Flash (Medium)` "
        "(Pair Programming de Alto Rendimiento)"
    )
    index_lines.append("")
    index_lines.append(
        "Este directorio contiene el registro completo y documentado de tus "
        "interacciones y consultas con el asistente inteligente Antigravity "
        "en formato Markdown (`.md`)."
    )
    index_lines.append("")
    index_lines.append("## 🗂️ Lista de Conversaciones (Orden Cronológico)")
    index_lines.append("")
    index_lines.append(
        "| # | Título de la Conversación | Descripción | Fecha de Inicio | "
        "Mensajes | Herramienta IA | OS | Enlace al Archivo |"
    )
    index_lines.append(
        "| :-: | :--- | :--- | :--- | :---: | :---: | :---: | :--- |"
    )

    for idx, convo in enumerate(exported_convos, start=1):
        index_lines.append(
            f"| {idx} | **{convo['title']}** | {convo['description']} | "
            f"{convo['start_time_formatted']} | {convo['messages_count']} "
            f"| {convo['ia_tool']} | {convo['os']} | "
            f"[Ver Conversación](./{convo['filename']}) |"
        )

    index_lines.append("")
    index_lines.append("## ⬆⬇️🙂 EOF")
    index_lines.append("")
    index_lines.append("> [!NOTE]")
    index_lines.append("> **Tipo de Cuenta:** 💵 **Google AI Pro**")
    index_lines.append(">")
    index_lines.append(
        "> **Modelo Utilizado:** `Gemini 3.5 Flash (Medium)` "
        "(Pair Programming de Alto Rendimiento)"
    )
    index_lines.append("")
    index_lines.append("---")
    index_lines.append("")
    index_lines.append(
        f"_Historial actualizado automáticamente el: {get_now_local_str()}_"
    )
    index_lines.append("")
    index_lines.append(
        "_Puedes ejecutar el script "
        "`scripts/chats/gemini/export_conversations.py` en cualquier "
        "momento para actualizar estos documentos._"
    )

    raw_index = "\n".join(index_lines)
    normalized_index = normalize_markdown(raw_index)

    with open(index_path, "w", encoding="utf-8") as f:
        f.write(normalized_index)

    print(
        "¡Indice ordenado y normalizado para markdown linter generado con "
        f"éxito en {index_path}!"
    )

    # Actualizar dinámicamente mkdocs.yml con el menú ordenado
    # cronológicamente y enumerado
    try:
        workspace_dir = os.path.abspath(os.path.join(output_dir, "..", ".."))
        mkdocs_path = os.path.join(workspace_dir, "mkdocs.yml")
        if os.path.exists(mkdocs_path):
            with open(mkdocs_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Filtrar y remover el bloque 'nav:' existente
            new_lines = []
            skip_nav = False
            for line in lines:
                if line.strip().startswith("nav:"):
                    skip_nav = True
                    continue
                if skip_nav:
                    # Omitir cualquier línea tabulada, con espacios o guiones
                    if (
                        line.strip() == ""
                        or line.startswith(" ")
                        or line.startswith("\t")
                        or line.startswith("-")
                    ):
                        stripped = line.lstrip()
                        # Si encontramos una línea que no tenga espacios al
                        # inicio y no sea vacía, indica una nueva clave
                        # principal del YAML
                        if (
                            len(line) - len(stripped) == 0
                            and line.strip() != ""
                        ):
                            skip_nav = False
                        else:
                            continue
                new_lines.append(line)

            # Limpiar líneas vacías al final
            while new_lines and new_lines[-1].strip() == "":
                new_lines.pop()

            # Construir el bloque nav con la ordenación cronológica
            # y enumeración
            nav_block = [
                "",
                "nav:",
                "  - Centro de Control: index.md",
                "  - Guía del Proyecto (README): readme.md",
                "  - Guía de Reorganización: walkthrough.md",
                "  - Plan de Implementación: plan/implementation_plan.md",
                "  - Historial de Chats:",
                "      - Índice del Historial: chat_history/index.md"
            ]

            for i, convo in enumerate(exported_convos, start=1):
                # Escapar comillas dobles en títulos para evitar errores
                # de sintaxis YAML
                safe_title = convo['title'].replace('"', '\\"')
                nav_block.append(
                    f'      - "{i:02d}. {safe_title}": '
                    f'chat_history/{convo["filename"]}'
                )

            with open(mkdocs_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
                f.write("\n" + "\n".join(nav_block) + "\n")
            print(
                "¡Archivo mkdocs.yml actualizado con la navegación ordenada "
                "cronológicamente y enumerada con éxito!"
            )
    except Exception as e:
        print(
            "Error al actualizar mkdocs.yml con la navegación ordenada: "
            f"{e}"
        )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Multi-platform, incremental exporter of Antigravity AI "
            "conversations with decoupled TOC generation."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "--action", "-a",
        choices=["export", "toc", "all"],
        default="all",
        help=(
            "Action to perform: 'export' chats, generate 'toc' "
            "(index.md), or 'all' (both)."
        )
    )

    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help=(
            "Force re-exporting all chats even if they haven't changed "
            "since last export."
        )
    )

    parser.add_argument(
        "--brain-dir",
        default=DEFAULT_BRAIN_DIR,
        help="Path to the Antigravity brain/data directory."
    )

    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help="Path to the output chat history directory."
    )

    args = parser.parse_args()

    print(f"Sistemas Operativo Detectado: {get_os_indicator()}")
    print(f"Ruta de Origen (Brain): {args.brain_dir}")
    print(f"Ruta de Destino (Output): {args.output_dir}")
    print("-" * 50)

    if args.action in ("export", "all"):
        export_chats(args.brain_dir, args.output_dir, force=args.force)

    if args.action in ("toc", "all"):
        generate_toc(args.output_dir)

    # Sincronizar README.md principal con docs/readme.md
    try:
        workspace_dir = os.path.abspath(
            os.path.join(args.output_dir, "..", "..")
        )
        readme_src = os.path.join(workspace_dir, "README.md")
        readme_dst = os.path.join(workspace_dir, "docs", "readme.md")
        if os.path.exists(readme_src):
            shutil.copy2(readme_src, readme_dst)
            print(f"¡Sincronizado README.md con {readme_dst} con éxito!")
    except Exception as e:
        print(f"Error al sincronizar README.md: {e}")


if __name__ == "__main__":
    main()
