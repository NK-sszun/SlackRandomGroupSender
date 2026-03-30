import os
import random
import math
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from flask import Flask, request, jsonify

# ---------------- ENV ----------------

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_MEMBER_CHANNEL_ID = os.environ.get("SLACK_MEMBER_CHANNEL_ID")
SLACK_TARGET_CHANNEL_ID = os.environ.get("SLACK_TARGET_CHANNEL_ID")

EXCLUDED_MEMBERS = ["곽경석"]
MAX_GROUP_SIZE = 6

client = WebClient(token=SLACK_BOT_TOKEN)

app = Flask(__name__)

# ---------------- CORE ----------------

def get_user_cache():
    cache = {}

    try:
        result = client.users_list()

        for user in result["members"]:
            if user["is_bot"] or user["deleted"]:
                continue

            full_name = user.get("real_name") or user.get("name")
            clean_name = full_name.split('[')[0].strip()

            cache[user["id"]] = clean_name

    except SlackApiError as e:
        print(f"users.list error: {e.response['error']}")

    return cache


def get_channel_members(channel_id, excluded_list, user_cache):
    members = []

    try:
        result = client.conversations_members(channel=channel_id)

        for member_id in result["members"]:
            if member_id not in user_cache:
                continue

            name = user_cache[member_id]

            if name not in excluded_list:
                members.append(name)

    except SlackApiError as e:
        print(f"Error fetching members: {e.response['error']}")

    return members


def split_groups(members):
    random.shuffle(members)

    n = len(members)
    group_count = math.ceil(n / MAX_GROUP_SIZE)

    base_size = n // group_count
    remainder = n % group_count

    groups = []
    idx = 0

    for i in range(group_count):
        size = base_size + (1 if i < remainder else 0)
        groups.append(members[idx:idx + size])
        idx += size

    return groups


def send_group_message(channel_id, groups):
    text = "[WEEKLY_GROUP]\n\n*이번 주 그룹*\n\n"

    for idx, group in enumerate(groups, start=1):
        text += f"*그룹 {idx}*\n"
        text += ", ".join(group) if group else "멤버 없음"
        text += "\n\n"

    result = client.chat_postMessage(channel=channel_id, text=text)

    ts = result["ts"]

    client.pins_add(channel=channel_id, timestamp=ts)

    return ts


def unpin_previous_group_message(channel_id):
    try:
        result = client.pins_list(channel=channel_id)

        for item in result["items"]:
            if "message" not in item:
                continue

            msg = item["message"]
            text = msg.get("text", "")

            if "[WEEKLY_GROUP]" in text:
                client.pins_remove(channel=channel_id, timestamp=msg["ts"])

    except SlackApiError as e:
        print(f"Error removing pins: {e.response['error']}")

# ---------------- UPDATE LOGIC ----------------

def get_latest_group_message(channel_id):
    latest_msg = None
    latest_ts = "0"

    result = client.pins_list(channel=channel_id)

    for item in result["items"]:
        if "message" not in item:
            continue

        msg = item["message"]
        text = msg.get("text", "")

        if "[WEEKLY_GROUP]" not in text:
            continue

        if msg["ts"] > latest_ts:
            latest_ts = msg["ts"]
            latest_msg = msg

    return latest_msg


def parse_groups_from_message(msg):
    groups = []
    current_group = []

    lines = msg.get("text", "").split("\n")

    for line in lines:
        line = line.strip()

        if line.startswith("*그룹"):
            if current_group:
                groups.append(current_group)
                current_group = []

        elif "," in line:
            names = [name.strip() for name in line.split(",")]
            current_group.extend(names)

    if current_group:
        groups.append(current_group)

    return groups

def remove_members_from_groups(groups, removed_members):
    new_groups = []

    for group in groups:
        filtered = [m for m in group if m not in removed_members]
        if filtered:
            new_groups.append(filtered)

    return new_groups

# 최소인원 그룹 중 랜덤 배정
def add_new_members_balanced(groups, new_members):
    for member in new_members:
        # 그룹을 인원 기준으로 정렬
        groups.sort(key=lambda g: len(g))

        # 항상 groups[0] = 최소인원 그룹
        min_size = len(groups[0])

        # 후보 그룹 선택 : 최소 인원 그룹 and 최대 인원 안 넘은 그룹
        candidates = [g for g in groups if len(g) == min_size and len(g) < MAX_GROUP_SIZE]

        if candidates:
            target = random.choice(candidates)
        else:
            target = random.choice(groups)

        target.append(member)

    return groups


def update_group_message(channel_id, ts, groups):
    text = "[WEEKLY_GROUP]\n\n*이번 주 그룹*\n\n"

    for idx, group in enumerate(groups, start=1):
        text += f"*그룹 {idx}*\n"
        text += ", ".join(group)
        text += "\n\n"

    client.chat_update(channel=channel_id, ts=ts, text=text)


def notify_group_update(channel_id):
    text = "랜덤 점심 그룹을 갱신했습니다.\n"
    text += "채널의 고정 메시지를 확인해주세요.\n\n"

    client.chat_postMessage(channel=channel_id, text=text)

# ---------------- SLASH COMMAND ----------------

def handle_slash_command():
    user_cache = get_user_cache()

    members = get_channel_members(
        SLACK_MEMBER_CHANNEL_ID,
        EXCLUDED_MEMBERS,
        user_cache
    )

    if not members:
        return "멤버를 가져오지 못했습니다."

    prev_msg = get_latest_group_message(SLACK_TARGET_CHANNEL_ID)

    if not prev_msg:
        groups = split_groups(members)
        send_group_message(SLACK_TARGET_CHANNEL_ID, groups)
        return "기존 그룹이 없어 새로 생성했습니다."

    groups = parse_groups_from_message(prev_msg)

    prev_members = set()
    for g in groups:
        prev_members.update(g)

    current_members = set(members)

    removed_members = prev_members - current_members
    new_members = current_members - prev_members

    # 삭제 먼저
    if removed_members:
        groups = remove_members_from_groups(groups, removed_members)

    # 신규 멤버 추가 (최소인원 그룹부터 균등 배치)
    if new_members:
        groups = add_new_members_balanced(groups, new_members)

    if not new_members and not removed_members:
        return "변경된 멤버가 없습니다."

    update_group_message(
        SLACK_TARGET_CHANNEL_ID,
        prev_msg["ts"],
        groups
    )

    if new_members or removed_members:
        notify_group_update(SLACK_TARGET_CHANNEL_ID)

    return f"그룹을 갱신했습니다."

# ---------------- FLASK ENTRY ----------------

@app.route("/api/group_sender", methods=["POST"])
def slack_handler():
    try:
        command = request.form.get("command")

        if command == "/그룹갱신":
            result_text = handle_slash_command()

            return jsonify({
                "response_type": "ephemeral",
                "text": result_text
            })

        return jsonify({
            "response_type": "ephemeral",
            "text": "알 수 없는 명령어"
        })

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({
            "response_type": "ephemeral",
            "text": "에러 발생"
        })

# ---------------- RESET GROUP ----------------

def reset_random_group():
    user_cache = get_user_cache()

    members = get_channel_members(
        SLACK_MEMBER_CHANNEL_ID,
        EXCLUDED_MEMBERS,
        user_cache
    )

    if not members:
        print("멤버 없음")
        return

    groups = split_groups(members)

    unpin_previous_group_message(SLACK_TARGET_CHANNEL_ID)

    send_group_message(SLACK_TARGET_CHANNEL_ID, groups)

    print("점심 그룹 재생성 완료")
    
if __name__ == "__main__":
    reset_random_group()
