import os
import json
import re
import datetime

# Directory Paths
brain_dir = r"C:\Users\nelbren\.gemini\antigravity\brain"
workspace_dir = r"c:\Testing_Antigravity_v2.0.1_Gemini_3.5_Flash_(High)\ChronoAPI"
output_dir = os.path.join(workspace_dir, "docs", "chat_history")

# Hardcoded metadata for known conversations, fallback to parsing if unknown
CONVO_METADATA = {
    "54914d18-540f-4ec4-9f2e-948bcb752485": {
        "title": "Confirmación de Ruta de Proyecto",
        "description": "Confirmar la ruta de inicio actual del proyecto ChronoAPI y verificar la estructura del entorno virtual y archivos."
    },
    "5d102ccd-506f-4d7d-91e4-407b702c9c34": {
        "title": "Creación de Endpoints FastAPI (Date & Time)",
        "description": "Creación de una API REST con FastAPI con tres endpoints (/date, /time, /timestamp), diseño premium del frontend y enlaces a Swagger UI y ReDoc."
    },
    "666388ec-2b15-4bc8-aa6e-984b2c199347": {
        "title": "Documentación de Chats en Markdown",
        "description": "Consulta sobre cómo exportar e instrumentar el guardado automático de todas las pláticas de la sesión en formato Markdown (.md)."
    }
}


def clean_user_request(text):
    if not text:
        return ""
    # Extract text between <USER_REQUEST> tags if present
    req_match = re.search(r"<USER_REQUEST>(.*?)</USER_REQUEST>", text, re.DOTALL)
    if req_match:
        text = req_match.group(1)

    # Remove metadata block if present
    text = re.sub(r"<ADDITIONAL_METADATA>.*?</ADDITIONAL_METADATA>", "", text, flags=re.DOTALL)

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
        return dt_local.strftime("%Y-%m-%d %H:%M:%S") + " (America/Tegucigalpa)"
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
                elif source == "MODEL" and type_ == "PLANNER_RESPONSE" and content and not tool_calls:
                    history.append({
                        "role": "Asistente",
                        "timestamp": format_timestamp_local(created_at),
                        "raw_timestamp": created_at,
                        "content": content.strip()
                    })
            except Exception as e:
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

        is_list_item = not in_fence and re.match(r"^\s*([\*\-\+QC]|\d+\.)\s", actual) is not None

        # Convert dash list items to asterisks (MD004)
        if not in_fence and re.match(r"^(\s*)-\s+", actual):
            actual = re.sub(r"^(\s*)-\s+", r"\1* ", actual)
            line = prefix + actual

        is_heading = not in_fence and re.match(r"^(#{1,6})\s+(.*)$", actual) is not None

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

        # Ensure blank line BEFORE heading (MD022), fence start (MD031), or list start (MD032)
        if final_lines:
            prev_line = final_lines[-1]
            prev_bq = re.match(r"^(\s*>\s*)(.*)$", prev_line)
            prev_actual = prev_bq.group(2) if prev_bq else prev_line
            prev_is_list = re.match(r"^\s*([\*\-\+QC]|\d+\.)\s", prev_actual) is not None

            need_blank = False
            if is_heading and prev_actual.strip() != "":
                need_blank = True
            elif is_fence_line and in_fence and prev_actual.strip() != "":
                need_blank = True
            elif is_list_item and not prev_is_list and prev_actual.strip() != "":
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

            is_heading = not in_fence and re.match(r"^#{1,6}\s", actual) is not None
            is_fence_end = is_fence_line and not in_fence
            is_list_item = not in_fence and re.match(r"^\s*([\*\-\+QC]|\d+\.)\s", actual) is not None
            next_is_list = not in_fence and re.match(r"^\s*([\*\-\+QC]|\d+\.)\s", next_actual) is not None

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


def export_all():
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Creado directorio de salida: {output_dir}")

    convo_folders = os.listdir(brain_dir)
    print(f"Conversaciones encontradas: {convo_folders}")

    exported_convos = []

    for cid in convo_folders:
        logs_path = os.path.join(brain_dir, cid, ".system_generated", "logs", "transcript.jsonl")
        if not os.path.exists(logs_path):
            continue

        print(f"Procesando conversación {cid}...")
        history = parse_transcript(logs_path)

        if not history:
            print(f"No se encontró historial en {cid}, saltando...")
            continue

        # Get metadata
        meta = CONVO_METADATA.get(cid, {
            "title": f"Conversación {cid[:8]}",
            "description": "Conversación grabada del historial."
        })

        title = meta["title"]
        description = meta["description"]

        # Build Markdown File
        filename = f"chat_{cid}.md"
        filepath = os.path.join(output_dir, filename)

        content_lines = []
        content_lines.append(f"# 💬 {title}")
        content_lines.append("")
        content_lines.append(f"> **ID de Conversación:** `{cid}`")
        content_lines.append(">")
        content_lines.append(f"> **Descripción:** {description}")
        content_lines.append(">")
        content_lines.append(f"> **Generado el:** {get_now_local_str()}")
        content_lines.append("")
        content_lines.append("---")
        content_lines.append("")

        for entry in history:
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

        raw_markdown = "\n".join(content_lines)
        normalized_markdown = normalize_markdown(raw_markdown)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(normalized_markdown)

        exported_convos.append({
            "id": cid,
            "title": title,
            "description": description,
            "filename": filename,
            "messages_count": len(history),
            "start_time": history[0]["raw_timestamp"] if history[0]["raw_timestamp"] else "",
            "start_time_formatted": history[0]["timestamp"]
        })
        print(f"Exportada con éxito a {filepath}")

    # Sort conversations by start_time (ascending - oldest to newest)
    exported_convos.sort(key=lambda x: x["start_time"])

    # Write Index file
    index_path = os.path.join(output_dir, "index.md")

    index_lines = []
    index_lines.append("# 📚 Historial de Conversaciones y Pláticas")
    index_lines.append("")
    index_lines.append("> [!NOTE]")
    index_lines.append("> **Tipo de Cuenta:** **Google AI Pro**")
    index_lines.append(">")
    index_lines.append("> **Modelo Utilizado:** `Gemini 3.5 Flash (High)` (Pair Programming de Alto Rendimiento)")
    index_lines.append("")
    index_lines.append("Este directorio contiene el registro completo y documentado de tus interacciones y consultas con el asistente inteligente Antigravity en formato Markdown (`.md`).")
    index_lines.append("")
    index_lines.append("## 🗂️ Lista de Conversaciones (Orden Cronológico)")
    index_lines.append("")
    index_lines.append("| # | Título de la Conversación | Descripción | Fecha de Inicio | Mensajes | Enlace al Archivo |")
    index_lines.append("| :-: | :--- | :--- | :--- | :---: | :--- |")

    for idx, convo in enumerate(exported_convos, start=1):
        index_lines.append(f"| {idx} | **{convo['title']}** | {convo['description']} | {convo['start_time_formatted']} | {convo['messages_count']} | [Ver Conversación](./{convo['filename']}) |")

    index_lines.append("")
    index_lines.append("---")
    index_lines.append("")
    index_lines.append(f"*Historial actualizado automáticamente el: {get_now_local_str()}*")
    index_lines.append("")
    index_lines.append("*Puedes ejecutar el script `scripts/export_conversations.py` en cualquier momento para actualizar estos documentos.*")

    raw_index = "\n".join(index_lines)
    normalized_index = normalize_markdown(raw_index)

    with open(index_path, "w", encoding="utf-8") as f:
        f.write(normalized_index)
        
    print(f"¡Indice ordenado y normalizado para markdown linter generado con éxito en {index_path}!")


if __name__ == "__main__":
    export_all()
