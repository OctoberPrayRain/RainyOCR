# RainyOCR
A simple OCR tools to translate game texts
# How to install
- Execute ```git clone https://github.com/OctoberPrayRain/RainyOCR.git``` to clone the repository in local environment. <br>
- Execute ```uv sync``` in project files to download the requirements.
- Use ```cp .env.example .env``` to create a ```.env``` file,then edit ```.env``` to use your own LLM with API Keys.
- Execute ```uv run python main.py``` or ```python main.py``` to open ```RainyOCR```
# How to use
- Click the ```Select Region``` button to select a window that you want to capture.
- Then click the ```Capture + Translate``` button to upload the captured picture and translate.
- Wait for the result of translated text.
