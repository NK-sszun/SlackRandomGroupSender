import random, requests

WEBHOOK_URL = "https://hooks.slack.com/triggers/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"

members = [
    "김준호2", "이윤호", "홍창모", "성지윤",
    "조성국", "윤정민", "곽경석", "이송현", "최민규",
    "조경빈", "서정민2", "이우성", "황성원",
    "박인환", "김준영2", "김준호", "이상령
]

# 멤버 랜덤 섞기
random.shuffle(members)

# 3개 그룹으로 분할
group_count = 3
groups = [members[i::group_count] for i in range(group_count)]

# 그룹명 및 각 그룹의 멤버 문자열
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
