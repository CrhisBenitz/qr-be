from flask import Flask, request, send_file
import qrcode
from io import BytesIO

app = Flask(__name__)

@app.route('/qr-be')
def generate_qr():
    text = request.args.get('text')
    color = request.args.get('color', 'black')
    bg = request.args.get('bg', 'white')
    size = int(request.args.get('size', 10))

    if not text:
        return "Missing 'text' parameter", 400

    qr = qrcode.QRCode(box_size=size, border=4)
    qr.add_data(text)
    qr.make(fit=True)

    img = qr.make_image(fill_color=color, back_color=bg)
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)

    return send_file(buf, mimetype='image/png')
