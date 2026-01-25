from src.BaiduOCR.ocr import ocr


def process(ocr_result: dict[str, list[dict[str, str]] | int]):
    word_list = ocr_result["words_result"]
    if not isinstance(word_list, list):
        raise TypeError("get something error!")
    words = ""
    for word in word_list:
        word = word.get("words")
        if not isinstance(word, str):
            raise TypeError("word not exist!")
        words = words + word + "\n"

    return words


if __name__ == "__main__":
    result = process(ocr("images/test.png"))
    print(result)
