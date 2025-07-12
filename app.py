from flask import Flask, request, send_file
from io import BytesIO
import PIL
from PIL import Image, ImageDraw
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import CircleModuleDrawer,GappedSquareModuleDrawer,HorizontalBarsDrawer,RoundedModuleDrawer,SquareModuleDrawer,VerticalBarsDrawer
import urllib.parse
from qrcode.image.styles.colormasks import SolidFillColorMask

app = Flask(__name__)

drawers = {
    "squares": SquareModuleDrawer(),
    "circles": RoundedModuleDrawer(),
    "gapped-squares": GappedSquareModuleDrawer(),
    "gapped-circles": CircleModuleDrawer(),
    "vertical-bars": VerticalBarsDrawer(),
    "horizontal-bars": HorizontalBarsDrawer(),
}

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

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_rgb(rgb_color):
    rgb_color = urllib.parse.unquote(rgb_color)
    rgb_color = rgb_color.lstrip('rgb(')
    rgb_color = rgb_color.rstrip(')')
    return tuple(int(c) for c in rgb_color.split(","))



@app.route("/qr-be")
def generate_qr():
    # Read parameters
    data = request.args.get("text")

    main_color = rgb_to_rgb(request.args.get('main-color', 'rgb(255,255,255)'))
    main_bg = rgb_to_rgb(request.args.get('main-bg', 'rgb(0,0,0)'))
    main_drawer = request.args.get('main-drawer', 'squares')

    innereyes_color = rgb_to_rgb(request.args.get('innereyes-color', 'rgb(255,255,255)'))
    innereyes_bg = rgb_to_rgb(request.args.get('innereyes-bg', 'rgb(0,0,0)'))
    innereyes_drawer = request.args.get('innereyes-drawer', 'squares')

    outereyes_color = rgb_to_rgb(request.args.get('outereyes-color', 'rgb(255,255,255)'))
    outereyes_bg = rgb_to_rgb(request.args.get('outereyes-bg', 'rgb(0,0,0)'))
    outereyes_drawer = request.args.get('outereyes-drawer', 'squares')

    app.logger.info(main_bg)


    if not data:
        return "Missing 'text' parameter", 400

    # Create base QR object
    qr = qrcode.QRCode(version=10, error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(data)

    # Create base image
    qr_img = qr.make_image(image_factory=StyledPilImage, module_drawer=drawers[main_drawer],color_mask=SolidFillColorMask(front_color=main_color, back_color=main_bg))

    # Create inner eye layer
    qr_inner_eyes_img = qr.make_image(image_factory=StyledPilImage,
        eye_drawer=drawers[innereyes_drawer],
        color_mask=SolidFillColorMask(
            back_color=innereyes_bg,
            front_color=innereyes_color)
    )

    # Create outer eye layer
    qr_outer_eyes_img = qr.make_image(image_factory=StyledPilImage,
        eye_drawer=drawers[outereyes_drawer],
        color_mask=SolidFillColorMask(front_color=outereyes_color)
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
