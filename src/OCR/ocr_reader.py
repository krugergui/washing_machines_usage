import os
import re

from doctr.io import DocumentFile
from doctr.models import ocr_predictor

screenshots_dir = "screenshots/landing_area/"

files = [f for f in os.listdir(screenshots_dir)]

model = ocr_predictor(
    det_arch="db_mobilenet_v3_large", reco_arch="crnn_mobilenet_v3_large", pretrained=True
)

list_appliances_types = ["Waschmaschine", "Trockner"]
regex_applances_numbers = r"\b\d{5}\b"
list_appliances_in_use = [
    "belegt",
    "frei",
    "Laufzeit:",
]
regex_applances_times = r"\d{2}:\d{2}:\d{2}"


def get_dict_appliances(result):
    appliances = []

    appliances_types = []
    appliances_numbers = []
    appliances_status = []
    appliances_times = []

    for page in result.pages:
        for block in page.blocks:
            for line in block.lines:
                for word in line.words:
                    if word.value in list_appliances_types:
                        appliances_types.append(word.value)
                    if word.value in list_appliances_in_use:
                        appliances_status.append(word.value)
                    if re.search(regex_applances_numbers, word.value):
                        appliances_numbers.append(word.value)
                    if re.search(regex_applances_times, word.value):
                        appliances_times.append(word.value)

    for i in range(len(appliances_numbers)):
        appliances.append(
            {
                "type": appliances_types[i],
                "status": appliances_status[i],
                "number": appliances_numbers[i],
            }
        )

    for i in appliances:
        if i.get("status") in ["belegt", "Laufzeit:"]:
            i["time"] = appliances_times.pop(0)

    return appliances


if __name__ == "__main__":
    for file in files:
        result = model(DocumentFile.from_images(screenshots_dir + file))

        appliances = get_dict_appliances(result)

        print(appliances)

        breakpoint()
