import os
import webbrowser
import threading

from flask import (
    Flask,
    render_template,
    request,
    send_file,
    redirect,
    url_for,
    flash,
)
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
from docx import Document

app = Flask(__name__)

# Basic configuration
app.config["SECRET_KEY"] = "change-this-secret-key"
app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "uploads")
app.config["OUTPUT_FOLDER"] = os.path.join(app.root_path, "converted")

ALLOWED_EXTENSIONS = {"pdf"}

# Ensure folders exist
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["OUTPUT_FOLDER"], exist_ok=True)


def allowed_file(filename: str) -> bool:
    """Check if the uploaded file has an allowed extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def convert_pdf_to_docx(pdf_path: str, output_path: str) -> str:
    """
    Convert a PDF file to a Word (.docx) file using extracted text.

    This function extracts text from each page and writes it into a
    Word document as paragraphs. It does not preserve complex layout,
    images, or tables.
    """
    reader = PdfReader(pdf_path)
    document = Document()

    for page in reader.pages:
        text = page.extract_text()
        if text:
            # Add each non-empty line as a paragraph
            lines = text.splitlines()
            for line in lines:
                if line.strip():
                    document.add_paragraph(line.strip())
            # Page break between pages
            document.add_page_break()

    document.save(output_path)
    return output_path

def open_browser():
    webbrowser.open("http://127.0.0.1:5000")

@app.route("/", methods=["GET"])
def index():
    """Render the upload page."""
    return render_template("index.html")


@app.route("/convert", methods=["POST"])
def convert():
    """
    Handle the PDF upload and return the converted Word document.

    Steps:
    - Validate that a file has been uploaded.
    - Ensure it is a PDF.
    - Save it to UPLOAD_FOLDER.
    - Convert to .docx in OUTPUT_FOLDER.
    - Send the .docx file as a download.
    """
    if "pdf_file" not in request.files:
        flash("No file part in the request.")
        return redirect(url_for("index"))

    file = request.files["pdf_file"]

    if file.filename == "":
        flash("No file selected.")
        return redirect(url_for("index"))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        pdf_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(pdf_path)

        base_name, _ = os.path.splitext(filename)
        output_filename = base_name + ".docx"
        output_path = os.path.join(app.config["OUTPUT_FOLDER"], output_filename)

        convert_pdf_to_docx(pdf_path, output_path)

        return send_file(
            output_path,
            as_attachment=True,
            download_name=output_filename,
            mimetype=(
                "application/"
                "vnd.openxmlformats-officedocument.wordprocessingml.document"
            ),
        )

    flash("Invalid file type. Please upload a PDF file.")
    return redirect(url_for("index"))


if __name__ == "__main__":
    threading.Timer(1.0, open_browser).start()
    app.run(debug=True)

