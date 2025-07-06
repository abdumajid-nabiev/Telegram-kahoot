import json
import os
import random

# Your vocabulary list: each tuple is (English, Korean)
vocab_list = [
    ("basic", "기초적"),
    ("infer", "추론하다"),
    ("expand", "확장하다"),
    ("reading", "독해"),
    ("criticize", "비판하다"),
    ("reorganize", "재구성하다"),
    ("fill", "채우다"),
    ("border", "테두리"),
    ("wave", "파동"),
    ("spread", "퍼지다"),
    ("each", "각각의"),
    ("rub", "문지르다"),
    ("shape", "형태"),
    ("freeze", "얼어붙다"),
    ("revitalize", "활성화하다"),
    ("small", "소형"),
    ("a bit", "약간"),
    ("noisy", "요란하다"),
    ("frown", "눈살을 찌푸리다"),
    ("handicapped seating", "노약자석"),
    ("hard", "힘겹다"),
    ("thoughtlessly", "무심코"),
    ("consider", "배려하다"),
    ("spectacle", "광경"),
    ("get rained on", "비를 맞다"),
    ("glow", "화끈거리다"),
    ("at least", "최소한"),
    ("impressed", "감격스럽다"),
    ("surrender", "항복하다"),
    ("humanity", "인류"),
    ("impure", "불순하다"),
    ("double-edged sword", "양날의 칼"),
    ("pipe dream", "그림의 떡"),
    ("right", "옳다"),
    ("exist", "존재하다"),
    ("profit", "이익"),
    ("both hands", "양손"),
    ("float", "떠오르다"),
    ("unemployment", "취업난"),
    ("enjoy pleasure", "기쁨을 누리다"),
    ("minority", "소수"),
    ("recruitment", "채용"),
    ("reason", "사유"),
    ("fairness", "공정"),
    ("side", "측"),
    ("difficult", "곤란하다"),
    ("supplement", "보완하다"),
    ("many", "수많은"),
    ("job seeker", "구직자"),
    ("reliability", "신뢰성"),
    ("demand", "요구하다"),
    ("secure", "확보하다"),
    ("objectify", "객관화하다"),
    ("take exam", "응시"),
    ("just in time", "마침"),
    ("avoid", "꺼리다"),
    ("reveal", "드러내다"),
    ("growth", "성장"),
    ("systematic", "체계적"),
    ("sudden", "급격하다"),
    ("majority", "압도적인"),
    ("uptrend", "상승세"),
    ("yearly", "연간의"),
    ("investigate", "조사하다"),
    ("world", "전 세계"),
    ("scale", "규모"),
    ("consumption", "소비량"),
    ("statistics", "통계"),
    ("exceed", "넘다"),
    ("clearly", "분명히"),
    ("finish", "마무리하다"),
    ("finally", "결국"),
    ("pain", "고통"),
    ("flow through", "통하다"),
    ("precious", "소중하다"),
    ("lecture", "강좌"),
    ("background", "배경"),
    ("appreciate", "감상하다"),
    ("principle", "원리"),
    ("abundant", "풍성하다"),
    ("cool", "멋지다"),
    ("angle", "각도"),
    ("thank you", "수고하셨습니다"),
    ("naturally", "저절로"),
    ("on the spot", "즉석에서"),
    ("of course", "물론"),
    ("include", "비롯하다"),
    ("different color", "이색"),
    ("all sorts", "각종의"),
    ("attractive", "매력적"),
    ("trend", "추세"),
    ("synthesis", "합성"),
    ("high prices", "고물가"),
    ("method", "수단"),
    ("or", "혹은"),
    ("church", "성당"),
    ("investment", "재테크"),
    ("utilize", "활용하다"),
    ("valuable", "유용하다"),
    ("attention", "주목받다"),
    ("point", "포인트"),
    ("phenomenon", "현상"),
    ("mainly", "주로"),
    ("collect taxes", "세금 걷다"),
    ("understand current situation", "현황을 파악하다"),
    ("found business", "창업하다"),
    ("warning", "예고"),
    ("countermeasure", "대책"),
    ("war", "전쟁"),
    ("noticeable", "눈에 띄다"),
    ("genocide", "대량 학살"),
    ("die", "사망하다"),
    ("so", "그다지"),
    ("carry out", "시행하다"),
    ("caused by", "인하다"),
    ("broadcast", "내보내다"),
    ("extensive", "대대적"),
    ("firm stand", "단호한 태도"),
    ("partner", "동반자"),
    ("donation", "기부금"),
    ("evade", "기피하다"),
    ("living expenses", "생계비"),
    ("exhibit", "출품하다"),
    ("joke", "장난")
]

# Generate quiz
quiz = []
for eng, kor in vocab_list:
    correct = kor
    options = [correct]
    while len(options) < 4:
        wrong = random.choice(vocab_list)[1]
        if wrong != correct and wrong not in options:
            options.append(wrong)
    random.shuffle(options)
    quiz.append({
        "text": f"What is the Korean word for '{eng}'?",
        "options": options,
        "answer": correct,
        "time_limit": 10
    })

# Save JSON
os.makedirs("data/quizzes", exist_ok=True)
filename = "english_korean_vocab_quiz.json"
filepath = os.path.join("data/quizzes", filename)

with open(filepath, "w", encoding="utf-8") as f:
    json.dump(quiz, f, ensure_ascii=False, indent=2)

filepath
