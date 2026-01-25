from src.TranslateAgent import translate
from src.utils import baidu_ocr_result_processor
from src.BaiduOCR.ocr import ocr


def process(translate_result: dict[str, list[dict[str, str]] | int]):
    word_list = translate_result["trans_result"]
    if not isinstance(word_list, list):
        raise TypeError("get something error!")
    words = ""
    for word in word_list:
        word = word.get("dst")
        if not isinstance(word, str):
            raise TypeError("word not exist!")
        words = words + word + "\n"

    return words


if __name__ == "__main__":
    result = process(
        translate.translate(baidu_ocr_result_processor.process(ocr("images/test.png")))
    )
    print(result)
