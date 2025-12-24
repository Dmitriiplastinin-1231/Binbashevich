from flask import Flask, send_from_directory

app = Flask(__name__)
UPLOAD_DIR = "uploads"

@app.route('/files/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)