import os
import random
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = os.environ.get("SLACK_CHANNEL_ID")

EXCLUDED_MEMBERS = ["곽경석"]

client = WebClient(token=SLACK_BOT_TOKEN)


def get_channel_members(channel_id, excluded_list):
    """채널 멤버 이름 가져오기"""
    try:
        result = client.conversations_members(channel=channel_id)
        member_ids = result["members"]

        members = []
        for member_id in member_ids:
            user_info = client.users_info(user=member_id)

            if not user_info["user"]["is_bot"]:
                full_name = user_info["user"].get("real_name") or user_info["user"].get("name")
                clean_name = full_name.split('[')[0].strip()

                if clean_name not in excluded_list:
                    members.append(clean_name)

        return members

    except SlackApiError as e:
        print(f"Error fetching members: {e.response['error']}")
        return []


def unpin_previous_group_message(channel_id):
    """내가 보낸 이전 그룹 메시지만 unpin"""
    try:
        result = client.pins_list(channel=channel_id)
        items = result.get("items", [])

        for item in items:
            if "message" in item:
                msg = item["message"]
                text = msg.get("text", "")
                ts = msg["ts"]

                if "[WEEKLY_GROUP]" in text:
                    client.pins_remove(
                        channel=channel_id,
                        timestamp=ts
                    )
                    print(f"Removed old group pin: {ts}")

    except SlackApiError as e:
        print(f"Error removing pins: {e.response['error']}")


def send_group_message(channel_id, groups):
    text = f"""
[WEEKLY_GROUP]

*이번 주 그룹*

*그룹 1*
{", ".join(groups[0]) if groups[0] else "멤버 없음"}

*그룹 2*
{", ".join(groups[1]) if groups[1] else "멤버 없음"}

*그룹 3*
{", ".join(groups[2]) if groups[2] else "멤버 없음"}
"""

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


# --- 메인 로직 ---

print(f"제외할 멤버: {', '.join(EXCLUDED_MEMBERS) if EXCLUDED_MEMBERS else '없음'}")

members = get_channel_members(SLACK_CHANNEL_ID, EXCLUDED_MEMBERS)

if not members:
    print("멤버를 가져오지 못했습니다.")
else:
    print(f"그룹 생성 대상 멤버 ({len(members)}명): {', '.join(members)}")

    group_count = 3
    random.shuffle(members)

    groups = [[] for _ in range(group_count)]

    for idx, member in enumerate(members):
        groups[idx % group_count].append(member)

    # 기존 pinned 메시지 제거
    unpin_existing_messages(SLACK_CHANNEL_ID)

    # 새 메시지 전송 + pin
    send_group_message(SLACK_CHANNEL_ID, groups)
