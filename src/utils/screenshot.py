import mss
import mss.tools

"""
当前是对整个屏幕进行截屏
"""


# TODO: 还需要一个json文件解析，后续这个配置的json文件非常重要
def screenshot(img_x: int, img_y: int, img_width: int, img_height: int):
    """
    这是一个用于截图的函数
    """
    with mss.mss() as sct:
        monitor = {
            "top": img_x,
            "left": img_y,
            "width": img_width,
            "height": img_height,
        }
        output = "sct-{top}x{left}_{width}x{height}.png".format(**monitor)

        sct_img = sct.grab(monitor)
        mss.tools.to_png(sct_img.rgb, sct_img.size, output=output)
        print(output)


if __name__ == "__main__":
    screenshot(100, 100, 200, 130)
