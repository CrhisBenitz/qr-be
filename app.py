from flask import Flask, request, send_file
from io import BytesIO
import PIL
from PIL import Image, ImageDraw
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask

app = Flask(__name__)

# Compatibility for older Pillow versions
if not hasattr(PIL.Image, 'Resampling'):
    PIL.Image.Resampling = PIL.Image

def style_inner_eyes(img):
    img_size = img.size[0]
    mask = Image.new('L', img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rectangle((60, 60, 90, 90), fill=255)
    draw.rectangle((img_size-90, 60, img_size-60, 90), fill=255)
    draw.rectangle((60, img_size-90, 90, img_size-60), fill=255)
    return mask

def style_outer_eyes(img):
    img_size = img.size[0]
    mask = Image.new('L', img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rectangle((40, 40, 110, 110), fill=255)
    draw.rectangle((img_size-110, 40, img_size-40, 110), fill=255)
    draw.rectangle((40, img_size-110, 110, img_size-40), fill=255)
    draw.rectangle((60, 60, 90, 90), fill=0)
    draw.rectangle((img_size-90, 60, img_size-60, 90), fill=0)
    draw.rectangle((60, img_size-90, 90, img_size-60), fill=0)
    return mask



@app.route("/qr-be")
def generate_qr():
    # Read parameters
    data = request.args.get("text")
    color = request.args.get('color', 'black')
    bg = request.args.get('bg', 'white')
    size = int(request.args.get('size', 10))

    if not data:
        return "Missing 'text' parameter", 400

    # Create base QR object
    qr = qrcode.QRCode(version=5, error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(data)

    # Create base image
    qr_img = qr.make_image(image_factory=StyledPilImage,
                           module_drawer=RoundedModuleDrawer())

    # Create inner eye layer
    qr_inner_eyes_img = qr.make_image(image_factory=StyledPilImage,
        eye_drawer=RoundedModuleDrawer(radius_ratio=1),
        color_mask=SolidFillColorMask(
            back_color=(255, 255, 255),
            front_color=(63, 42, 86))
    )

    # Create outer eye layer
    qr_outer_eyes_img = qr.make_image(image_factory=StyledPilImage,
        eye_drawer=RoundedModuleDrawer(),
        color_mask=SolidFillColorMask(front_color=(255, 128, 0))
    )

    # Composite inner and outer eye layers
    inner_eye_mask = style_inner_eyes(qr_img)
    outer_eye_mask = style_outer_eyes(qr_img)
    intermediate_img = Image.composite(qr_inner_eyes_img, qr_img, inner_eye_mask)
    final_image = Image.composite(qr_outer_eyes_img, intermediate_img, outer_eye_mask)

    # Return as PNG
    buf = BytesIO()
    final_image.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype='image/png')
