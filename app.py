import os
import io
import subprocess
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from pdf2image import convert_from_bytes
from pdf2docx import Converter
from PIL import Image

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/convert', methods=['POST'])
def convert():
    if 'file' not in request.files:
        return jsonify({"error": "Keine Datei hochgeladen"}), 400
    
    file = request.files['file']
    target_format = request.form.get('target_format', '').lower()
    
    if file.filename == '' or not target_format:
        return jsonify({"error": "Ungültige Parameter"}), 400

    filename, file_extension = os.path.splitext(file.filename)
    file_extension = file_extension.lower().replace('.', '')
    file_bytes = file.read()

    # --- WEG 1: Irgendwas zu PDF (Office, TXT, ODT) ---
    if target_format == 'pdf':
        # Wenn es bereits ein Bild ist
        if file_extension in ['jpg', 'jpeg', 'png']:
            img = Image.open(io.BytesIO(file_bytes))
            pdf_out = io.BytesIO()
            img.convert('RGB').save(pdf_out, format='PDF')
            pdf_out.seek(0)
            return send_file(pdf_out, mimetype='application/pdf', as_attachment=True, download_name=f"{filename}.pdf")
        
        # Wenn es ein Office-Dokument oder Text ist -> LibreOffice nutzen
        else:
            # Temporär speichern, da LibreOffice echte Dateien auf der Festplatte braucht
            input_path = f"/tmp/{file.filename}"
            with open(input_path, 'wb') as f:
                f.write(file_bytes)
            
            # LibreOffice Headless Befehl ausführen
            cmd = [
                "libreoffice",
                "--headless",
                "--invisible",
                "--nodefault",
                "--nofirststartwizard",
                "--nolockcheck",
                "--nologo",
                "--norestore",
                "--convert-to", "pdf",
                "--outdir", "/tmp",
                input_path
            ]
            subprocess.run(cmd, check=True)
            
            output_path = f"/tmp/{filename}.pdf"
            with open(output_path, 'rb') as f:
                converted_bytes = f.read()
                
            # Bereinigen
            os.remove(input_path)
            os.remove(output_path)
            
            return send_file(io.BytesIO(converted_bytes), mimetype='application/pdf', as_attachment=True, download_name=f"{filename}.pdf")

    # --- WEG 2: PDF zu BILDER (JPEG/JPG) ---
    elif target_format in ['jpg', 'jpeg', 'png'] and file_extension == 'pdf':
        images = convert_from_bytes(file_bytes)
        if not images:
            return jsonify({"error": "PDF konnte nicht gelesen werden"}), 500
        
        # Für die Einfachheit nehmen wir hier die erste Seite (bei mehreren Seiten müsste man ein ZIP zurückgeben)
        img_out = io.BytesIO()
        images[0].save(img_out, format='JPEG' if target_format in ['jpg', 'jpeg'] else 'PNG')
        img_out.seek(0)
        return send_file(img_out, mimetype=f'image/{target_format}', as_attachment=True, download_name=f"{filename}.{target_format}")

    # --- WEG 3: PDF zu WORD (DOCX) ---
    elif target_format == 'docx' and file_extension == 'pdf':
        pdf_path = f"/tmp/{file.filename}"
        docx_path = f"/tmp/{filename}.docx"
        
        with open(pdf_path, 'wb') as f:
            f.write(file_bytes)
            
        # pdf2docx Konverter nutzen
        cv = Converter(pdf_path)
        cv.convert(docx_path, start=0, end=None)
        cv.close()
        
        with open(docx_path, 'rb') as f:
            converted_bytes = f.read()
            
        os.remove(pdf_path)
        os.remove(docx_path)
        
        return send_file(io.BytesIO(converted_bytes), mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document', as_attachment=True, download_name=f"{filename}.docx")

    return jsonify({"error": f"Konvertierung von {file_extension} nach {target_format} wird noch nicht unterstützt."}), 400

if __name__ == '__main__':
    app.run(port=8080)
