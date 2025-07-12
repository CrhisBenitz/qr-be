from flask import Flask, request, send_file
from io import BytesIO
import PIL
from PIL import Image, ImageDraw
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import CircleModuleDrawer,GappedSquareModuleDrawer,HorizontalBarsDrawer,RoundedModuleDrawer,SquareModuleDrawer,VerticalBarsDrawer
import urllib.parse
from qrcode.image.styles.colormasks import SolidFillColorMask
from  qrcode.image.styles.colormasks import ImageColorMask
import re
import requests

app = Flask(__name__)

# Compatibility for older Pillow versions
if not hasattr(PIL.Image, 'Resampling'):
    PIL.Image.Resampling = PIL.Image

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

def parse_color(value):
    """Return (r, g, b) tuple from #rrggbb, #rgb, or rgb(r,g,b)."""
    if not value or value=="None":
        return None

    value = urllib.parse.unquote_plus(value.strip())


    # Hex formats ----------------------------------------------------------------
    if value.startswith('#'):
        value = value.lstrip('#')
        print(value)
        print(tuple(int(value[i:i+2], 16) for i in (0, 2, 4)))
        return tuple(int(value[i:i+2], 16) for i in (0, 2, 4))

    # rgb(r, g, b) ----------------------------------------------------------------
    m = re.match(r'rgb\(\s*(\d{1,3})\s*,'
                 r'\s*(\d{1,3})\s*,'
                 r'\s*(\d{1,3})\s*\)', value, re.I)
    if m:
        return tuple(int(n) for n in m.groups())

    raise ValueError(f"Unsupported colour format: {value}")



@app.route("/qr-be")
def generate_qr():

    # Read parameters
    data = request.args.get("text")
    if not data:
        return "Missing 'text' parameter", 400


    main_color = parse_color(request.args.get('main-color', 'rgb(255,255,255)'))
    main_bg = parse_color(request.args.get('main-bg', 'rgb(0,0,0)'))
    main_drawer = request.args.get('main-drawer', 'squares')

    innereyes_color = parse_color(request.args.get('innereyes-color', 'None'))
    innereyes_bg = parse_color(request.args.get('innereyes-bg', 'None'))
    innereyes_drawer = request.args.get('innereyes-drawer', 'squares')

    outereyes_color = parse_color(request.args.get('outereyes-color', None))
    outereyes_bg = parse_color(request.args.get('outereyes-bg', None))
    outereyes_drawer = request.args.get('outereyes-drawer', 'squares')

    logo_url = request.args.get('logoURL',"")
    image_url = request.args.get('imageURL',"")

    logo = mimage = None

    if logo_url:
        try:
            logo_url = urllib.parse.unquote(logo_url)
            logo_response = requests.get(logo_url, timeout=5)
            logo_response.raise_for_status()
            logo = Image.open(BytesIO(logo_response.content)).convert("RGBA")
        except Exception as e:
            return f"Failed to fetch image from URL: {str(e)}", 400

    if image_url:
        try:
            image_url = urllib.parse.unquote(image_url)
            mimage_response = requests.get(image_url, timeout=5)
            mimage_response.raise_for_status()
            mimage = Image.open(BytesIO(mimage_response.content)).convert("RGBA")
        except Exception as e:
            return f"Failed to fetch image from URL: {str(e)}", 400


    # Create base QR object
    qr = qrcode.QRCode(version=6, error_correction=qrcode.constants.ERROR_CORRECT_H)
    # qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(data)

    # Create base image
    main_mask = SolidFillColorMask(front_color=main_color, back_color=main_bg)

    if mimage:
        main_mask = ImageColorMask(color_mask_image=mimage,back_color=main_bg)

    qr_img = qr.make_image(image_factory=StyledPilImage, module_drawer=drawers[main_drawer],color_mask=main_mask)
    # qr_img = qr.make_image(fit=True, image_factory=StyledPilImage, module_drawer=drawers[main_drawer],color_mask=SolidFillColorMask(front_color=main_color, back_color=main_bg))

    if logo:
        # Resize logo
        qr_width, qr_height = qr_img.size
        logo_size = int(qr_width * 0.25)
        logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)

        # Paste logo into the center of the QR
        pos = ((qr_width - logo_size) // 2, (qr_height - logo_size) // 2)
        qr_img.paste(logo, pos, mask=logo)

    inner_eyes_mask = outer_eyes_mask = main_mask

    if not innereyes_bg:
        innereyes_bg = main_bg
    if not outereyes_bg:
        outereyes_bg =  main_bg

    if innereyes_color and innereyes_bg:
        inner_eyes_mask = SolidFillColorMask(back_color=innereyes_bg,front_color=innereyes_color)
    if outereyes_color and outereyes_bg:
        outer_eyes_mask = SolidFillColorMask(back_color=outereyes_bg,front_color=outereyes_color)

    # Create inner eye layer
    qr_inner_eyes_img = qr.make_image(image_factory=StyledPilImage,
        eye_drawer=drawers[innereyes_drawer],
        color_mask=inner_eyes_mask)

    # Create outer eye layer
    qr_outer_eyes_img = qr.make_image(image_factory=StyledPilImage,
        eye_drawer=drawers[outereyes_drawer],
        color_mask=outer_eyes_mask)

    # Composite inner and outer eye layers
    inner_eye_mask = style_inner_eyes(qr_img)
    outer_eye_mask = style_outer_eyes(qr_img)
    intermediate_img = Image.composite(qr_inner_eyes_img, qr_img, inner_eye_mask)
    final_image = Image.composite(qr_outer_eyes_img, intermediate_img, outer_eye_mask)

    # Return as PNG
    buf = BytesIO()
    final_image.save(buf, format="PNG")
    buf.seek(0)
    # return parse_color(request.args.get('main-color', 'rgb(255,255,255)'))
    return send_file(buf, mimetype='image/png')
