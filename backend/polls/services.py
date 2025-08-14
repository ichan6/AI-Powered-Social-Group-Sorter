import uuid
import re
import pandas as pd
from typing import List, Dict
import os
from openai import OpenAI
from django.conf import settings
import json
import csv

# OpenAI API Key
client = OpenAI(api_key=settings.OPENAI_API_KEY)

# Keywords to identify PII columns

PII_KEYWORDS = {
    'name', 'email', 'phone', 'number', 'contact', 'student_id', 'netid',
    'username', 'discord', 'social_media', 'messenger', 'instagram',
    "Is there anything else you want us to know? (This is the end of the form!)"
}

# Columns to retain even if they contain "PII-ish" keywords
PREFERENCE_COLUMNS = [
    'user_id',
    'preferred_friends',
    'want_to_be_with',
    'roommate',
    'Who you you want to be paired with? (You can list multiple names, just remember to put first and last)',
    "Is there anything else you want us to know? (This is the end of the form!)"
]

# Normalize a name: lowercased + underscores
def normalize_name(name: str) -> str:
    return name.strip().lower().replace(" ", "_")

def _inject_default_group_count(instruction: str, default_count: int = 5) -> str:
    """
    If no specific group count is mentioned in the instruction,
    inject a default request for `default_count` groups.
    """
    if not instruction:
        return f"Group people into {default_count} meaningful families based on similar vibes, energy, or shared interests."
    
    pattern = r"\b(\d+)\s+groups?\b"
    if re.search(pattern, instruction.lower()):
        return instruction  # User already specified group count
    return f"{instruction.strip()} Group everyone into {default_count} total families unless otherwise specified."

# Step 1: Identify columns containing PII
def is_pii_column(col_name: str) -> bool:
    col_name = col_name.strip().lower().replace(" ", "_").replace("-", "")
    return any(keyword in col_name for keyword in PII_KEYWORDS)

# Step 2: Remove duplicate responses, keeping the latest
def deduplicate_responses(df: pd.DataFrame, timestamp_column: str = 'timestamp') -> pd.DataFrame:
    if timestamp_column not in df.columns:
        raise ValueError(f"Timestamp column '{timestamp_column}' not found in DataFrame.")
    df = df.sort_values(timestamp_column)
    df = df.drop_duplicates(subset=["First and Last Name"], keep="last")
    return df

# Step 3: Pseudonymize by assigning UUIDs and storing name mapping
def pseudonymize_and_generate_uuid(df: pd.DataFrame):
    uuid_map = {}
    name_to_uuid = {}
    user_ids = []

    # Normalize and collect all names first
    name_series = df["First and Last Name"].fillna("").astype(str)
    normalized_names = name_series.apply(normalize_name)

    for norm_name in normalized_names.unique():
        if norm_name:
            uid = str(uuid.uuid4())
            name_to_uuid[norm_name] = uid
            uuid_map[uid] = {"name": norm_name}

    # Assign UUIDs to DataFrame using the map
    for norm_name in normalized_names:
        user_ids.append(name_to_uuid.get(norm_name, ""))

    df.insert(loc=0, column="user_id", value=user_ids)

    pii_columns = [col for col in df.columns if is_pii_column(col) and col not in PREFERENCE_COLUMNS]
    df = df.drop(columns=pii_columns, errors="ignore")

    return df, uuid_map, name_to_uuid, pii_columns

# Step 4: Replace comma-separated names in free-response with UUIDs
def is_uuid(string):
    try:
        uuid.UUID(string)
        return True
    except ValueError:
        return False

def replace_names_with_uuids(df: pd.DataFrame, name_to_uuid: Dict[str, str], columns_to_check: List[str]):
    unmatched_map = {}  # cache to reuse manual UUIDs for unmatched values

    for col in columns_to_check:
        if col not in df.columns:
            print(f"⚠️ Column not found for UUID translation: '{col}'")
            continue

        def replace_cell(cell):
            if not isinstance(cell, str):
                return cell

            results = []

            chunks = [normalize_name(part) for part in cell.split(",")]

            for chunk in chunks:
                # Skip if it's already a UUID (real or manual)
                if is_uuid(chunk) or chunk.startswith("manual-"):
                    results.append(chunk)
                elif chunk in name_to_uuid:
                    results.append(name_to_uuid[chunk])
                elif chunk in unmatched_map:
                    results.append(unmatched_map[chunk])
                else:
                    # Generate and store a manual UUID
                    new_uuid = f"manual-{str(uuid.uuid4())}"
                    unmatched_map[chunk] = new_uuid
                    results.append(new_uuid)

            return ", ".join(results)

        df[col] = df[col].apply(replace_cell)

    return df, unmatched_map

# EOF Column Encryption
def encrypt_manual_column(df: pd.DataFrame, column_name: str):
    manual_encryption_map = {}

    if column_name not in df.columns:
        print(f"⚠️ Column '{column_name}' not found for encryption.")
        return df, manual_encryption_map

    for idx, val in df[column_name].items():
        if isinstance(val, str) and val.strip():  # only encrypt non-empty text
            if val not in manual_encryption_map:
                manual_encryption_map[val] = f"manual-{str(uuid.uuid4())}"
            df.at[idx, column_name] = manual_encryption_map[val]
        else:
            df.at[idx, column_name] = ""

    return df, manual_encryption_map

# Main pipeline entrypoint
def clean_and_prepare_dataframe(df: pd.DataFrame, timestamp_column: str, preference_columns: List[str]):
    df.columns = [col.strip().replace("\n", " ").replace("\r", " ").strip() for col in df.columns]
    df = deduplicate_responses(df, timestamp_column)
    df, uuid_map, name_to_uuid, pii_columns = pseudonymize_and_generate_uuid(df)
    df, unmatched_map = replace_names_with_uuids(df, name_to_uuid, preference_columns)

    # Encrypt "End of Form" free response
    extra_column = "Is there anything else you want us to know? (This is the end of the form!)"
    df, extra_manual_map = encrypt_manual_column(df, extra_column)

    # Merge both manual maps
    unmatched_map.update(extra_manual_map)

    return df, uuid_map, name_to_uuid, unmatched_map, pii_columns

# Optional: Debugging output of name → UUID mapping
def save_name_to_uuid_map(name_to_uuid: Dict[str, str], filepath="name_to_uuid_map.csv"):
    """
    Saves name → UUID mapping to a CSV file.
    """
    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "UUID"])
        for name, uid in name_to_uuid.items():
            writer.writerow([name, uid])

def save_manual_uuid_map(unmatched_map: Dict[str, str], filepath="manual_uuid_map.csv"):
    """
    Saves original text → manually assigned UUID mapping to a CSV file.
    """
    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Original Text", "Manual UUID"])
        for original_text, manual_uuid in unmatched_map.items():
            writer.writerow([original_text, manual_uuid])

# ---- Start of AI Pipeline ----

# Step 1: Pre-Processing
def run_preprocessing_pipeline(members: List[Dict]) -> Dict[str, str]:
    summaries = {}

    for member in members:
        user_id = member.get("user_id")
        if not user_id:
            continue

        content_parts = []

        for field, val in member.items():
            if field == "user_id":
                continue
            if isinstance(val, str):
                trimmed = val.strip()
                # Skip UUID-like entries (including manual-UUIDs)
                if not trimmed or is_uuid(trimmed) or trimmed.startswith("manual-"):
                    continue
                content_parts.append(f"{field}: {trimmed}")

        if not content_parts:
            summaries[user_id] = ""
            continue

        prompt = (
            "You are summarizing a user's form responses.\n"
            "Your goal is to compress the content into 1–2 bullet points **without losing emotional tone or subtle personal preferences.**\n"
            "Preserve important feelings, intentions, and context even if they seem casual or emotional.\n"
            "Do not over-formalize or flatten the voice too much.\n\n"
            + "\n".join(content_parts)
        )


        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
            )
            summary = response.choices[0].message.content.strip()
            summaries[user_id] = summary

        except Exception as e:
            print(f"❌ Error summarizing user {user_id}: {e}")
            summaries[user_id] = "[summary failed]"

    return summaries

# Step 2: Sorting
def sort_users_with_gpt(summaries: Dict[str, str], instruction: str, batch_size: int = 40) -> Dict[str, str]:
    """
    Smart wrapper for sorting users with GPT.
    Uses batch-based sorting if the number of users exceeds batch_size.
    """
    formatted_summaries = {
        user_id: summary
        for user_id, summary in summaries.items()
        if summary.strip() and summary != "[summary failed]"
    }

    if len(formatted_summaries) <= batch_size:
        print(f"🔹 Sorting {len(formatted_summaries)} users directly (no batching)...")
        return sort_users_with_gpt_single_batch(formatted_summaries, instruction)
    else:
        print(f"🔸 Sorting {len(formatted_summaries)} users in batches of {batch_size}...")
        return sort_users_in_batches(formatted_summaries, instruction, batch_size)

def sort_users_with_gpt_single_batch(summaries: Dict[str, str], instruction: str) -> Dict[str, str]:
    """
    Sends a single batch of summaries to GPT and returns user_id → group mapping.
    """
    formatted_entries = [
        f"- {user_id}: {summary}"
        for user_id, summary in summaries.items()
    ]

    instruction = _inject_default_group_count(instruction)

    prompt = (
        "You are a personality-based group formation expert.\n"
        "Your job is to create meaningful, compatible groups of people based solely on their summaries and the general instruction provided.\n"
        "Each summary contains emotionally rich clues about the individual's preferences, tone, and interpersonal dynamics.\n"
        "\n"
        "You are NOT distributing people evenly or rotating group names — you are clustering people like a social matchmaker.\n"
        "Group count or labels (e.g., '5 groups') should be treated as flexible guidance unless extremely specific. Do not default to cycling through groups.\n"
        "\n"
        "Assign people into families or social groups based on shared energy, values, or complementarity.\n"
        "Avoid any repetitive or modulo-like assignment patterns. Let compatibility guide you.\n"
        "\n"
        "Here is a brief example of personality-based grouping:\n"
        "- user_001: Group A  # outgoing, club-heavy lifestyle, likes social games\n"
        "- user_002: Group B  # chill, introverted, loves journaling and quiet nights\n"
        "- user_003: Group A  # passionate, community-centered, expressive tone\n"
        "- user_004: Group B  # emotionally reflective, enjoys solitude and depth\n"
        "\n"
        "Unless otherwise instructed, use lettered group names: 'Group A', 'Group B', etc.\n"
        "Use consistent naming — DO NOT mix formats (e.g., don't use 'Group 3' and 'Group C' together).\n"
        "Do NOT invent creative group names unless explicitly told to.\n"
        "\n"
        f"Instruction:\n{instruction}\n"
        f"\nParticipants:\n{chr(10).join(formatted_entries)}\n"
        "\nReturn the result as a JSON dictionary with the format:\n"
        "{\n"
        "  \"user_id\": {\n"
        "    \"family\": \"Group A\",\n"
        "    \"notes\": \"Matched with uuid123 due to shared interests in reflection and quiet hobbies.\"\n"
        "  },\n"
        "  ...\n"
        "}\n"
        "You MUST return valid JSON only — no explanation, just the mapping.\n"
        "Make sure every user_id is assigned to one of the group names you use.\n"
        "Each 'notes' entry should be one sentence giving a reason for the assignment — short, meaningful, and human-readable.\n"
        "If you reference other users in the notes, use their user_id exactly as written."
    )


    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a friendly, intuitive and reliable AI sorting assistant.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
        )

        content = response.choices[0].message.content.strip()
        print("🔍 Raw GPT response:\n", content)
        cleaned_content = re.sub(r"^```(?:json)?|```$", "", content.strip(), flags=re.IGNORECASE).strip()

        result = json.loads(cleaned_content)
        print("✅ Parsed result:", result)
        return result

    except Exception as e:
        print("❌ Error during GPT sorting:", e)
        return {}

# Step 2.1: Batch Sorting
def sort_users_in_batches(summaries: Dict[str, str], instruction: str, batch_size: int = 40) -> Dict[str, str]:
    """
    Splits summaries into manageable batches and sorts them using GPT.
    Returns a combined mapping of user_id -> assigned family.
    """
    import re

    def batch_dict(d: Dict[str, str], size: int):
        items = list(d.items())
        for i in range(0, len(items), size):
            yield dict(items[i:i + size])

    full_result = {}
    batches = list(batch_dict(summaries, batch_size))
    total_batches = len(batches)

    # Detect if user explicitly asked for a specific number of groups
    group_count_match = re.search(r"\b([2-9]|1[0-9])\s+groups?\b", instruction.lower())
    use_custom_groups = group_count_match is not None

    if not use_custom_groups:
        group_count = 5  # <- DEFAULT GROUP COUNT
        group_names = [f"Group {chr(ord('A') + i)}" for i in range(group_count)]

    # If a number was found (like "7 groups"), we enforce it across batches
    if use_custom_groups:
        group_count = int(group_count_match.group(1))
        group_names = [f"Group {chr(ord('A') + i)}" for i in range(group_count)]
    else:
        group_names = []  # let default logic in prompt handle this

    for idx, batch in enumerate(batches):
        print(f"\n📦 Sorting batch {idx + 1}/{total_batches} with {len(batch)} users...")

        if use_custom_groups:
            batch_instruction = (
                f"{instruction.strip()}\n\n"
                f"You are sorting batch {idx + 1} of {total_batches}. "
                f"The total number of groups across all batches must be exactly {len(group_names)}.\n"
                f"Do not create new group names. Only assign participants to the following:\n"
                + ", ".join(group_names) + "."
            )
        else:
            batch_instruction = (
                f"{_inject_default_group_count(instruction)}\n\n"
                f"You are sorting batch {idx + 1} of {total_batches}. "
                f"The total number of groups across all batches must be exactly {len(group_names)}.\n"
                f"Do not create new group names. Only assign participants to the following:\n"
                + ", ".join(group_names) + "."
            )

        result = sort_users_with_gpt(batch, batch_instruction)

        if result is None:
            print(f"❌ GPT failed to return results for batch {idx + 1}. Skipping...")
            continue

        # Check for skipped users
        expected = set(batch)
        received = set(result)
        missing = expected - received

        if missing:
            print(f"⚠️ GPT skipped {len(missing)} users in batch {idx + 1}: {missing}")

        full_result.update(result)

    # Final check for unsorted users
    final_missing = set(summaries) - set(full_result)
    if final_missing:
        print(f"\n🚨 Total unsorted users after batching: {len(final_missing)}")

    return full_result

# Step 3: UUID -> Name Translations
def translate_uuids_to_names_with_preferences(
    sorted_csv_path: str,
    name_to_uuid_path: str,
    manual_uuid_path: str,
    output_path: str = "sorted_by_name.csv"
):
    """
    Replaces UUIDs in a sorted CSV with real names using both the standard and manual UUID CSV maps.
    Also translates UUIDs in the preference field.
    """

    # === LOAD UUID → Name MAP ===
    uuid_to_name = {}

    # Standard map
    with open(name_to_uuid_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            uuid = row["UUID"]
            name = row["Name"]
            uuid_to_name[uuid] = name

    # Manual map
    with open(manual_uuid_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            uuid = row["Manual UUID"]
            original = row["Original Text"]
            uuid_to_name[uuid] = f"[manual:{original}]"

    # === LOAD INPUT CSV ===
    df = pd.read_csv(sorted_csv_path)

    # Translate user_id to name
    df.insert(0, "name", df["user_id"].map(lambda uid: uuid_to_name.get(uid, f"[UNKNOWN:{uid}]")))

    # === TRANSLATE UUIDs in the preference column ===
    PREFERENCE_COLUMN = "Who you you want to be paired with? (You can list multiple names, just remember to put first and last)"

    def translate_preference_cell(cell):
        if pd.isna(cell):
            return ""
        parts = [part.strip() for part in cell.split(",")]
        translated = [uuid_to_name.get(p, f"[UNKNOWN:{p}]") for p in parts]
        return ", ".join(translated)

    if PREFERENCE_COLUMN in df.columns:
        df[PREFERENCE_COLUMN] = df[PREFERENCE_COLUMN].apply(translate_preference_cell)
        print(f"✅ Translated UUIDs in preference column: '{PREFERENCE_COLUMN}'")
    else:
        print(f"⚠️ Column not found: '{PREFERENCE_COLUMN}'")

    # === SAVE FINAL OUTPUT ===
    df.to_csv(output_path, index=False)
    print(f"✅ Full UUID translation complete. Saved to {output_path}")
