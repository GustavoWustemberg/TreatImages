import os
import zipfile
import uuid
import shutil
import logging
import tempfile
import threading
from flask import Flask, render_template, request, send_file, flash, redirect, url_for, after_this_request, jsonify
from werkzeug.utils import secure_filename
from PIL import Image
from rembg import remove as rembg_remove

from Class.tools import functionalities

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Usar pasta temp do sistema evita que o watchdog do Flask reinicie o servidor
# toda vez que um ZIP é criado dentro do diretório do projeto.
_TMP_BASE       = tempfile.gettempdir()
UPLOAD_FOLDER   = os.path.join(_TMP_BASE, "treatimages", "uploads")
PROCESSED_FOLDER = os.path.join(_TMP_BASE, "treatimages", "processed")
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "jfif"}

app = Flask(__name__)
app.secret_key = "treatimages-secret-2024"
app.config["UPLOAD_FOLDER"]    = UPLOAD_FOLDER
app.config["PROCESSED_FOLDER"] = PROCESSED_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB

logging.basicConfig(level=logging.INFO)

# Ensure required directories exist
os.makedirs(UPLOAD_FOLDER,   exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# Global task state for tracking asynchronous processes
tasks = {}
tasks_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Image helpers
# ---------------------------------------------------------------------------

EXT_TO_PIL = {
    "jpg": "JPEG",
    "jpeg": "JPEG",
    "png": "PNG",
    "webp": "WEBP",
    "jfif": "JPEG",
}

def normalize_mode(img: Image.Image, pil_format: str) -> Image.Image:
    """Convert RGBA / P images to RGB when the target format doesn't support alpha."""
    if pil_format in ("JPEG",) and img.mode in ("RGBA", "P", "LA"):
        return img.convert("RGB")
    return img


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploads(files, session_id: str) -> tuple[str, list[str]]:
    """Save uploaded files to a session-specific upload folder.
    Returns (session_upload_dir, list_of_saved_paths).
    """
    session_dir = os.path.join(app.config["UPLOAD_FOLDER"], session_id)
    os.makedirs(session_dir, exist_ok=True)
    saved = []
    for f in files:
        if f and allowed_file(f.filename):
            filename = secure_filename(f.filename)
            dest = os.path.join(session_dir, filename)
            f.save(dest)
            saved.append(dest)
    return session_dir, saved


def create_zip(source_dir: str, zip_name: str) -> str:
    """Zip all files in source_dir and return the zip path."""
    zip_path = os.path.join(app.config["PROCESSED_FOLDER"], zip_name)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in os.listdir(source_dir):
            fpath = os.path.join(source_dir, fname)
            if os.path.isfile(fpath):
                zf.write(fpath, fname)
    return zip_path


def cleanup_session(session_id: str):
    """Remove temporary upload & processed directories for this session."""
    for base in (app.config["UPLOAD_FOLDER"], app.config["PROCESSED_FOLDER"]):
        session_dir = os.path.join(base, session_id)
        if os.path.isdir(session_dir):
            shutil.rmtree(session_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


# ── Task Tracking & Status ───────────────────────────────────────────────

@app.route("/task-status/<task_id>")
def task_status(task_id):
    with tasks_lock:
        task = tasks.get(task_id)
    if not task:
        return jsonify({"status": "failed", "error": "Tarefa não encontrada."}), 404
    return jsonify(task)


@app.route("/task-download/<task_id>")
def task_download(task_id):
    with tasks_lock:
        task = tasks.get(task_id)
    if not task or task.get("status") != "completed":
        return "Tarefa não concluída ou inválida.", 404

    zip_path = task.get("zip_path")
    if not zip_path or not os.path.exists(zip_path):
        return "Arquivo não encontrado.", 404

    @after_this_request
    def cleanup(response):
        try:
            os.remove(zip_path)
            with tasks_lock:
                tasks.pop(task_id, None)
        except OSError:
            pass
        return response

    return send_file(zip_path, as_attachment=True,
                     download_name=task.get("download_name", "imagens.zip"),
                     mimetype="application/zip")


# ── Background Task Workers ─────────────────────────────────────────────

def bg_resize(task_id, saved, new_width, out_dir, upload_dir, zip_name):
    errors = []
    total = len(saved)
    for i, img_path in enumerate(saved):
        filename = os.path.basename(img_path)
        ext = filename.rsplit(".", 1)[-1].lower()
        pil_format = EXT_TO_PIL.get(ext, "JPEG")
        try:
            with Image.open(img_path) as img:
                img.load()
                width, height = img.size
                new_height = functionalities.calc_new_height(width, height, new_width)
                resized = img.resize((new_width, new_height), Image.LANCZOS)
                resized = normalize_mode(resized, pil_format)
                save_kwargs = {"format": pil_format, "optimize": True}
                if pil_format in ("JPEG", "WEBP"):
                    save_kwargs["quality"] = 95
                resized.save(os.path.join(out_dir, filename), **save_kwargs)
        except Exception as e:
            logging.error(f"Erro ao redimensionar {filename}: {e}")
            errors.append(filename)

        with tasks_lock:
            if task_id in tasks:
                tasks[task_id]["progress"] = i + 1
                tasks[task_id]["errors"] = errors

    zip_path = create_zip(out_dir, zip_name)
    shutil.rmtree(upload_dir, ignore_errors=True)
    shutil.rmtree(out_dir,    ignore_errors=True)

    with tasks_lock:
        if task_id in tasks:
            tasks[task_id]["status"] = "completed"
            tasks[task_id]["zip_path"] = zip_path


def bg_convert(task_id, saved, target_format, out_dir, upload_dir, zip_name):
    errors = []
    total = len(saved)
    for i, img_path in enumerate(saved):
        filename_base, _ = os.path.splitext(os.path.basename(img_path))
        new_filename = f"{filename_base}.{target_format}"
        pil_format = EXT_TO_PIL.get(target_format, target_format.upper())
        try:
            with Image.open(img_path) as img:
                img.load()
                out_img = normalize_mode(img, pil_format)
                save_kwargs = {"format": pil_format, "optimize": True}
                if pil_format in ("JPEG", "WEBP"):
                    save_kwargs["quality"] = 90
                out_img.save(os.path.join(out_dir, new_filename), **save_kwargs)
        except Exception as e:
            logging.error(f"Erro ao converter {img_path}: {e}")
            errors.append(os.path.basename(img_path))

        with tasks_lock:
            if task_id in tasks:
                tasks[task_id]["progress"] = i + 1
                tasks[task_id]["errors"] = errors

    zip_path = create_zip(out_dir, zip_name)
    shutil.rmtree(upload_dir, ignore_errors=True)
    shutil.rmtree(out_dir,    ignore_errors=True)

    with tasks_lock:
        if task_id in tasks:
            tasks[task_id]["status"] = "completed"
            tasks[task_id]["zip_path"] = zip_path


def bg_compress(task_id, saved, quality, out_dir, upload_dir, zip_name):
    errors = []
    total = len(saved)
    for i, img_path in enumerate(saved):
        filename = os.path.basename(img_path)
        ext = filename.rsplit(".", 1)[-1].lower()
        pil_format = EXT_TO_PIL.get(ext, "JPEG")
        try:
            with Image.open(img_path) as img:
                img.load()
                out_img = normalize_mode(img, pil_format)
                save_kwargs = {"format": pil_format, "optimize": True}
                if pil_format in ("JPEG", "WEBP"):
                    save_kwargs["quality"] = quality
                out_img.save(os.path.join(out_dir, filename), **save_kwargs)
        except Exception as e:
            logging.error(f"Erro ao comprimir {img_path}: {e}")
            errors.append(filename)

        with tasks_lock:
            if task_id in tasks:
                tasks[task_id]["progress"] = i + 1
                tasks[task_id]["errors"] = errors

    zip_path = create_zip(out_dir, zip_name)
    shutil.rmtree(upload_dir, ignore_errors=True)
    shutil.rmtree(out_dir,    ignore_errors=True)

    with tasks_lock:
        if task_id in tasks:
            tasks[task_id]["status"] = "completed"
            tasks[task_id]["zip_path"] = zip_path


def bg_remove_bg(task_id, saved, out_dir, upload_dir, zip_name):
    errors = []
    total = len(saved)
    for i, img_path in enumerate(saved):
        filename_base, _ = os.path.splitext(os.path.basename(img_path))
        out_filename = f"{filename_base}.png"
        try:
            with open(img_path, "rb") as f_in:
                input_data = f_in.read()
            output_data = rembg_remove(input_data)
            out_path = os.path.join(out_dir, out_filename)
            with open(out_path, "wb") as f_out:
                f_out.write(output_data)
        except Exception as e:
            logging.error(f"Erro ao remover fundo de {os.path.basename(img_path)}: {e}")
            errors.append(os.path.basename(img_path))

        with tasks_lock:
            if task_id in tasks:
                tasks[task_id]["progress"] = i + 1
                tasks[task_id]["errors"] = errors

    zip_path = create_zip(out_dir, zip_name)
    shutil.rmtree(upload_dir, ignore_errors=True)
    shutil.rmtree(out_dir,    ignore_errors=True)

    with tasks_lock:
        if task_id in tasks:
            tasks[task_id]["status"] = "completed"
            tasks[task_id]["zip_path"] = zip_path


# ── Resize Route ──────────────────────────────────────────────────────────

@app.route("/resize", methods=["POST"])
def resize():
    files = request.files.getlist("images")
    new_width = request.form.get("width", type=int)

    if not files or not any(f.filename for f in files):
        return jsonify({"error": "Nenhuma imagem enviada."}), 400
    if not new_width or new_width <= 0:
        return jsonify({"error": "Informe uma largura válida."}), 400

    session_id = str(uuid.uuid4())
    upload_dir, saved = save_uploads(files, session_id)

    if not saved:
        return jsonify({"error": "Nenhuma imagem válida encontrada (aceitos: jpg, jpeg, png, webp, jfif)."}), 400

    out_dir = os.path.join(app.config["PROCESSED_FOLDER"], session_id)
    os.makedirs(out_dir, exist_ok=True)

    task_id = str(uuid.uuid4())
    zip_name = f"resized_{session_id}.zip"

    with tasks_lock:
        tasks[task_id] = {
            "status": "processing",
            "progress": 0,
            "total": len(saved),
            "zip_path": None,
            "download_name": "imagens_redimensionadas.zip",
            "errors": []
        }

    threading.Thread(
        target=bg_resize,
        args=(task_id, saved, new_width, out_dir, upload_dir, zip_name)
    ).start()

    return jsonify({"task_id": task_id}), 202


# ── Convert Route ─────────────────────────────────────────────────────────

@app.route("/convert", methods=["POST"])
def convert():
    files = request.files.getlist("images")
    target_format = request.form.get("format", "webp").lower()

    if not files or not any(f.filename for f in files):
        return jsonify({"error": "Nenhuma imagem enviada."}), 400

    session_id = str(uuid.uuid4())
    upload_dir, saved = save_uploads(files, session_id)

    if not saved:
        return jsonify({"error": "Nenhuma imagem válida encontrada."}), 400

    out_dir = os.path.join(app.config["PROCESSED_FOLDER"], session_id)
    os.makedirs(out_dir, exist_ok=True)

    task_id = str(uuid.uuid4())
    zip_name = f"converted_{session_id}.zip"

    with tasks_lock:
        tasks[task_id] = {
            "status": "processing",
            "progress": 0,
            "total": len(saved),
            "zip_path": None,
            "download_name": "imagens_convertidas.zip",
            "errors": []
        }

    threading.Thread(
        target=bg_convert,
        args=(task_id, saved, target_format, out_dir, upload_dir, zip_name)
    ).start()

    return jsonify({"task_id": task_id}), 202


# ── Compress Route ────────────────────────────────────────────────────────

@app.route("/compress", methods=["POST"])
def compress():
    files = request.files.getlist("images")
    quality = request.form.get("quality", type=int, default=75)

    if not files or not any(f.filename for f in files):
        return jsonify({"error": "Nenhuma imagem enviada."}), 400

    quality = max(1, min(quality, 100))

    session_id = str(uuid.uuid4())
    upload_dir, saved = save_uploads(files, session_id)

    if not saved:
        return jsonify({"error": "Nenhuma imagem válida encontrada."}), 400

    out_dir = os.path.join(app.config["PROCESSED_FOLDER"], session_id)
    os.makedirs(out_dir, exist_ok=True)

    task_id = str(uuid.uuid4())
    zip_name = f"compressed_{session_id}.zip"

    with tasks_lock:
        tasks[task_id] = {
            "status": "processing",
            "progress": 0,
            "total": len(saved),
            "zip_path": None,
            "download_name": "imagens_comprimidas.zip",
            "errors": []
        }

    threading.Thread(
        target=bg_compress,
        args=(task_id, saved, quality, out_dir, upload_dir, zip_name)
    ).start()

    return jsonify({"task_id": task_id}), 202


# ── Remove Background Route ──────────────────────────────────────────────

@app.route("/remove-bg", methods=["POST"])
def remove_bg():
    files = request.files.getlist("images")

    if not files or not any(f.filename for f in files):
        return jsonify({"error": "Nenhuma imagem enviada."}), 400

    session_id = str(uuid.uuid4())
    upload_dir, saved = save_uploads(files, session_id)

    if not saved:
        return jsonify({"error": "Nenhuma imagem válida encontrada (aceitos: jpg, jpeg, png, webp, jfif)."}), 400

    out_dir = os.path.join(app.config["PROCESSED_FOLDER"], session_id)
    os.makedirs(out_dir, exist_ok=True)

    task_id = str(uuid.uuid4())
    zip_name = f"sem_fundo_{session_id}.zip"

    with tasks_lock:
        tasks[task_id] = {
            "status": "processing",
            "progress": 0,
            "total": len(saved),
            "zip_path": None,
            "download_name": "imagens_sem_fundo.zip",
            "errors": []
        }

    threading.Thread(
        target=bg_remove_bg,
        args=(task_id, saved, out_dir, upload_dir, zip_name)
    ).start()

    return jsonify({"task_id": task_id}), 202


# ── Crop (Recortar) ──────────────────────────────────────────────────────

@app.route("/crop", methods=["POST"])
def crop():
    # O frontend envia o blob recortado no campo 'images' (mesmo nome dos outros forms)
    f = request.files.get("images")
    if not f or not f.filename:
        flash("Nenhuma imagem recebida.", "error")
        return redirect(url_for("index"))

    session_id = str(uuid.uuid4())
    out_dir = os.path.join(app.config["PROCESSED_FOLDER"], session_id)
    os.makedirs(out_dir, exist_ok=True)

    filename = secure_filename(f.filename)
    dest = os.path.join(out_dir, filename)
    f.save(dest)

    @after_this_request
    def cleanup(response):
        try:
            shutil.rmtree(out_dir, ignore_errors=True)
        except OSError:
            pass
        return response

    return send_file(dest, as_attachment=True, download_name=f"recorte_{filename}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, port=5000)
