import os
from django.http import FileResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import AccessKey
import uuid
import logging # for debug prints with gunicorn
logger = logging.getLogger(__name__)

from .utils import parse_spreadsheet
from .services import (
    clean_and_prepare_dataframe,
    save_name_to_uuid_map,
    save_manual_uuid_map,
    run_preprocessing_pipeline,
    sort_users_with_gpt,
    translate_uuids_to_names_with_preferences,
)

# Columns with name references to be pseudonymized/translated
PREFERENCE_COLUMNS = [
    'user_id',
    'preferred_friends',
    'want_to_be_with',
    'roommate',
    'Who you you want to be paired with? (You can list multiple names, just remember to put first and last)'
]
TIMESTAMP_COLUMN = 'Timestamp'

@api_view(["POST"])
def verify_key_without_increment(request):
    key = request.data.get("key")
    device_id = request.data.get("device_id")

    if not key:
        return Response({"valid": False, "message": "Missing access key."}, status=400)

    access = AccessKey.objects.filter(key=key).first()
    if not access:
        return Response({"valid": False, "message": "Invalid access key."}, status=403)

    if access.is_expired:
        return Response({"valid": False, "message": "Key expired."}, status=403)

    if access.usage_count >= access.usage_limit:
        return Response({"valid": False, "message": "Key usage limit reached."}, status=403)

    # Still check device match
    if access.device_id and device_id != access.device_id:
        return Response({"valid": False, "message": "Key is already bound to another device."}, status=403)

    return Response({"valid": True})

@api_view(["POST"])
def validate_key(request):
    key = request.data.get("key")
    device_id = request.data.get("device_id")
    ip = (
        request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0]
        or request.META.get("REMOTE_ADDR")
        or "unknown"
    )

    if not key:
        return Response({"valid": False, "message": "Missing access key."}, status=400)

    access = AccessKey.objects.filter(key=key).first()
    if not access:
        return Response({"valid": False, "message": "Invalid access key."}, status=403)

    if access.is_expired:
        return Response({"valid": False, "message": "Key expired."}, status=403)

    if access.usage_count >= access.usage_limit:
        return Response({"valid": False, "message": "Key usage limit reached."}, status=403)

    # First-time device binding
    if access.device_id and device_id != access.device_id:
        return Response({"valid": False, "message": "This key is already bound to another device."}, status=403)

    if not access.device_id:
        generated_device_id = str(uuid.uuid4())
        access.device_id = generated_device_id
    else:
        generated_device_id = access.device_id

    # Log the IP
    if ip not in access.ip_log:
        access.ip_log.append(ip)
        if len(access.ip_log) > 20:
            access.ip_log = access.ip_log[-20:]  # keep last 20 IPs

    access.usage_count += 1
    access.save()

    return Response({
        "valid": True,
        "message": "Access granted.",
        "device_id": generated_device_id,
        "remaining_uses": access.usage_limit - access.usage_count
    })

@api_view(["POST"])
def handle_sorting(request):
    instruction = request.POST.get("comments", "").strip()
    uploaded_file = request.FILES.get("file")

    if not instruction:
        instruction = "Group people by similar vibes, energy, or common interests."

    if not uploaded_file:
        return Response({"error": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)

    df = parse_spreadsheet(uploaded_file)
    if df is None:
        return Response({"error": "Failed to parse spreadsheet."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # 🧹 Pre-clean the data
        cleaned_df, uuid_map, name_to_uuid, unmatched_map, pii_columns = clean_and_prepare_dataframe(
            df, timestamp_column=TIMESTAMP_COLUMN, preference_columns=PREFERENCE_COLUMNS
        )

        # 🤖 Run AI preprocessing
        members = cleaned_df.to_dict(orient="records")
        summaries = run_preprocessing_pipeline(members)

        # 🧠 Final sort logic
        cleaned_df["summary"] = cleaned_df["user_id"].map(summaries)
        family_map = sort_users_with_gpt(summaries, instruction)
        cleaned_df["family"] = cleaned_df["user_id"].apply(lambda uid: family_map.get(str(uid).strip(), ""))

        # 💾 Save UUID maps
        save_name_to_uuid_map(name_to_uuid)
        save_manual_uuid_map(unmatched_map)

        # 🧾 Translate UUIDs back to names
        cleaned_df.to_csv("cleaned_output.csv", index=False)
        translate_uuids_to_names_with_preferences(
            sorted_csv_path="cleaned_output.csv",
            name_to_uuid_path="name_to_uuid_map.csv",
            manual_uuid_path="manual_uuid_map.csv",
            output_path="final_with_names.csv"
        )

        return FileResponse(
            open("final_with_names.csv", "rb"),
            as_attachment=True,
            filename="final_with_names.csv"
        )

    except Exception as e:
        return Response({"error": f"Processing failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    finally:
        for path in ["cleaned_output.csv", "final_with_names.csv"]:
            if os.path.exists(path):
                os.remove(path)
