import os
import re
from datetime import datetime

from doctr.io import DocumentFile
from doctr.models import ocr_predictor
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

user = os.getenv("SUPABASE_USER")
password = os.getenv("SUPABASE_USER_PASSWORD")

screenshots_dir = "screenshots/landing_area/"
processed_dir = "screenshots/processed/"
failed_dir = "screenshots/failed/"

files = [f for f in os.listdir(screenshots_dir)]

model = ocr_predictor(
    det_arch="db_mobilenet_v3_large", reco_arch="crnn_mobilenet_v3_large", pretrained=True
)

list_appliances_types = ["Waschmaschine", "Trockner"]
regex_applances_id = r"\b\d{5}\b"
list_appliances_in_use = [
    "belegt",
    "frei",
    "Laufzeit:",
]
regex_applances_times = r"\d{1,2}:\d{2}:\d{2}"


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
                    if re.search(regex_applances_id, word.value):
                        appliances_numbers.append(word.value)
                    if re.search(regex_applances_times, word.value):
                        appliances_times.append(word.value)

    if not (len(appliances_types) == len(appliances_numbers) == len(appliances_status)):
        return []

    for i in range(len(appliances_types)):
        appliances.append(
            {
                "type": appliances_types[i],
                "status": appliances_status[i],
                "appliance_external_id": appliances_numbers[i],
            }
        )

    for i in appliances:
        if i.get("status") in ["belegt", "Laufzeit:"]:
            i["running_for"] = appliances_times.pop(0)

    return appliances


def get_time_from_filename(filename):
    re_extract_date_time = r"\d{4}\d{2}\d{2}[-|_]\d{2}\d{2}\d{2}"
    update_time = re.findall(re_extract_date_time, filename)[0]

    return datetime.strptime(update_time, "%Y%m%d-%H%M%S")


if __name__ == "__main__":
    supabase = create_client(url, key)
    supabase_auth = supabase.auth.sign_in_with_password({"email": user, "password": password})

    for file in files:
        print("Processing file: " + file)
        result = model(DocumentFile.from_images(screenshots_dir + file))

        appliances = get_dict_appliances(result)
        print(appliances)

        # Check if there was an error in the OCR
        if (
            not appliances
            or not appliances[0].get("type")
            or (appliances[0].get("type") == "Waschmaschine" and len(appliances) != 4)
            or (appliances[0].get("type") == "Trockner" and len(appliances) != 2)
        ):
            os.rename(screenshots_dir + file, failed_dir + file)
            breakpoint
        else:
            for appliance in appliances:
                if appliance.get("status") in ["belegt", "Laufzeit:"]:
                    appliance["file_name"] = file

                    appliance_to_insert = {
                        "type": appliance.get("type"),
                        "running_for": appliance.get("running_for"),
                        "appliance_external_id": appliance.get("appliance_external_id"),
                        "file_name": appliance.get("file_name"),
                        "date_collected": str(
                            get_time_from_filename(file),
                        ),
                    }

                    supabase.table("appliances_use").insert(appliance_to_insert).execute()

            os.rename(screenshots_dir + file, processed_dir + file)

        supabase.table("time_updates").insert(
            {
                "file_name": file,
                "update_time": str(get_time_from_filename(file)),
            }
        ).execute()

    print("Done!")
