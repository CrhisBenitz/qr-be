from flask import Flask, request, send_file
import qrcode
from io import BytesIO

app = Flask(__name__)

@app.route('/qr')
def generate_qr():
    text = request.args.get('text', 'https://example.com')  # default if empty
    img = qrcode.make(text)

    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)

    return send_file(buf, mimetype='image/png')
