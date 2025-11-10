import random, requests

WEBHOOK_URL = "https://hooks.slack.com/triggers/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"
CHANNEL_ID = "C09QKN9JUR4"

members = [
    "김준호2", "이윤호", "홍창모", "김준호", "성지윤",
    "조성국", "윤정민", "곽경석", "이송현", "최민규",
    "조경빈", "서정민2", "안승근", "이우성", "황성원",
    "박인환", "김준영2"
]

# 무작위 섞기
random.shuffle(members)

# 3개 그룹으로 분할
group_count = 3
groups = [members[i::group_count] for i in range(group_count)]

# 각 그룹별로 Slack 워크플로우 호출
for i, group_members in enumerate(groups, start=1):
    group_name = f"[그룹 {i}]"
    member_list = ", ".join(group_members)
    
    payload = {
        "channel": CHANNEL_ID,
        "group": group_name,
        "members": member_list
    }
    
    response = requests.post(WEBHOOK_URL, json=payload)
    print(f"{group_name} 전송 결과:", response.status_code, response.text)
