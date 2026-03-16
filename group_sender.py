import os
import random
import math
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")

SLACK_MEMBER_CHANNEL_ID = os.environ.get("SLACK_MEMBER_CHANNEL_ID")
SLACK_TARGET_CHANNEL_ID = os.environ.get("SLACK_TARGET_CHANNEL_ID")

EXCLUDED_MEMBERS = ["곽경석"]

MAX_GROUP_SIZE = 6

client = WebClient(token=SLACK_BOT_TOKEN)


def get_user_cache():
    """users.list로 전체 유저 캐시 생성"""
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
    """채널 멤버 이름 가져오기"""

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
    """최대 6명 기준 균등 그룹 분배"""

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


def unpin_previous_group_message(channel_id):
    """이전 그룹 메시지만 unpin"""

    try:
        result = client.pins_list(channel=channel_id)

        for item in result["items"]:

            if "message" not in item:
                continue

            msg = item["message"]

            text = msg.get("text", "")

            if "[WEEKLY_GROUP]" in text:

                client.pins_remove(
                    channel=channel_id,
                    timestamp=msg["ts"]
                )

                print(f"Removed old group pin: {msg['ts']}")

    except SlackApiError as e:
        print(f"Error removing pins: {e.response['error']}")


def send_group_message(channel_id, groups):

    text = "[WEEKLY_GROUP]\n\n*이번 주 그룹*\n\n"

    for idx, group in enumerate(groups, start=1):

        text += f"*그룹 {idx}*\n"
        text += ", ".join(group) if group else "멤버 없음"
        text += "\n\n"

    try:

        result = client.chat_postMessage(
            channel=channel_id,
            text=text
        )

        ts = result["ts"]

        client.pins_add(
            channel=channel_id,
            timestamp=ts
        )

        print(f"Message sent and pinned: {ts}")

    except SlackApiError as e:

        print(f"Error sending message: {e.response['error']}")


# ---------------- MAIN ----------------

print(f"제외할 멤버: {', '.join(EXCLUDED_MEMBERS) if EXCLUDED_MEMBERS else '없음'}")

user_cache = get_user_cache()

members = get_channel_members(
    SLACK_MEMBER_CHANNEL_ID,
    EXCLUDED_MEMBERS,
    user_cache
)

if not members:

    print("멤버를 가져오지 못했습니다.")

else:

    print(f"그룹 생성 대상 멤버 ({len(members)}명): {', '.join(members)}")

    groups = split_groups(members)

    unpin_previous_group_message(SLACK_TARGET_CHANNEL_ID)

    send_group_message(SLACK_TARGET_CHANNEL_ID, groups)
