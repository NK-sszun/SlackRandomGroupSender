import random
import requests

WEBHOOK_URL = "https://hooks.slack.com/triggers/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"

members = [
    "김준호2", "이윤호", "홍창모", "성지윤",
    "조성국", "윤정민", "이송현", "최민규",
    "조경빈", "서정민2", "이우성", "황성원",
    "박인환", "김준영2", "이상령", "안승근", "신동헌"
]

group_count = 3

random.shuffle(members)

groups = [[] for _ in range(group_count)]

# 라운드 로빈 배치 (모든 멤버 동일 취급)
for idx, member in enumerate(members):
    groups[idx % group_count].append(member)

payload = {
    "group1": "[그룹 1]",
    "group2": "[그룹 2]",
    "group3": "[그룹 3]",
    "members1": ", ".join(groups[0]),
    "members2": ", ".join(groups[1]),
    "members3": ", ".join(groups[2])
}

response = requests.post(WEBHOOK_URL, json=payload)
print("전송 결과:", response.status_code, response.text)
