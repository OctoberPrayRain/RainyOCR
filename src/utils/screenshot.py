from PIL import Image
import mss


with mss.mss() as sct:
    sct_img = sct.grab(sct.monitors[1])

    img = Image.new("RGB", sct_img.size)

    pixels = zip(sct_img.raw[2::4], sct_img.raw[1::4], sct_img.raw[::4])

    img.putdata(list(pixels))

    """
    pixels = img.load()

    for x in range(sct_img.width):
        for y in range(sct_img.height):
            pixels[x, y] = sct_img.pixel(x, y)
    """

    img.show()
