import requests
import json
import re
from pathlib import Path
from datetime import datetime, timedelta

secrets_path = Path("access.json")
if secrets_path.exists():
    with open(secrets_path, encoding="utf-8") as f:
        secrets = json.load(f)
        OAUTH_TOKEN = secrets["OAUTH_TOKEN"]
        FOLDER_ID = secrets["FOLDER_ID"]
else:
    raise FileNotFoundError("Файл secrets.json не найден. Добавьте OAUTH_TOKEN и FOLDER_ID")

CACHE_FILE = Path("token_cache.json")

def get_iam_token_cached():
    if CACHE_FILE.exists():
        with open(CACHE_FILE, encoding="utf-8") as f:
            cache = json.load(f)
            token = cache.get("token")
            expires_at_str = cache.get("expires_at")
            if token and expires_at_str:
                expires_at = datetime.fromisoformat(expires_at_str)
                if datetime.utcnow() < expires_at:
                    return token

    response = requests.post(
        "https://iam.api.cloud.yandex.net/iam/v1/tokens",
        headers={"Content-Type": "application/json"},
        json={"yandexPassportOauthToken": OAUTH_TOKEN}
    )
    if response.status_code == 200:
        result = response.json()
        new_token = result["iamToken"]
        expires_at = datetime.utcnow() + timedelta(hours=11, minutes=50) 
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({"token": new_token, "expires_at": expires_at.isoformat()}, f)
        return new_token
    else:
        raise Exception(f"Ошибка получения IAM токена: {response.status_code} {response.text}")

PROMPT_TEMPLATE = """
По тексту ниже нужно выделить триплеты: субъект, предикат(связь), объект, а также четвертое поле - описание.
Субъект - то, кто выполняет действие
Предикат - действие
Объект - предмет/орган в системе, над которым выполняют действие
Описание - дополнительное описание, которое не вошло в субъект, предикат и объект. Если его нет, можно не заполнять
Среди найденных триплетов оставь только те, которые относятся к теме информационной безопасности.
Правила для предикатов:
1. В качестве предикатов всегда пиши глаголы в активном залоге.
2. Предикат должен выражать действие субъекта над объектом.
3. В предикате не должно быть существительных

Правила для субъектов и объектов:
1. Обязательно сокращай субъект и объект до 5-7 слов без утраты ценной информации.
2. Сохраняй описание важных именнованных сущностей (названия организаций, названия программных продуктов, фио, номера документов, даты, географические названия).
3. Если в субъекте или объекте есть перечисление нескольких сущностей (однородные члены предложения), то разделяй их. Например, "организации и учения" запиши в два разных триплета с объектами "организации" и "учения"
4. Обязательно храни субъект и объект в именительном падеже
Подготовь эти данные в форматe JSON с ключами subject, predicate, object, description
Пример:
Текст: ФСТЭК России утверждает компенсирующие меры и инструкции.
Вывод:
[
  {{
    "subject": "ФСТЭК России",
    "predicate": "утверждает",
    "object": "компенсирующие меры",
    "description": ""
  }},
  {{
    "subject": "ФСТЭК России",
    "predicate": "утверждает",
    "object": "инструкции",
    "description": ""
  }}
]
Текст: {text}
"""

def extract_json_block(text):
    match = re.search(r"```(?:json)?\s*([\[{].*?[\]}])\s*```", text, re.DOTALL)
    if match:
        return match.group(1)
    return text.strip()

def get_triplets_from_yandex(text):
    iam_token = get_iam_token_cached()
    headers = {
        "Authorization": f"Bearer {iam_token}",
        "Content-Type": "application/json"
    }

    full_prompt = PROMPT_TEMPLATE.format(text=text)
    data = {
        "modelUri": f"gpt://{FOLDER_ID}/yandexgpt-lite/latest",
        "completionOptions": {
            "stream": False,
            "temperature": 0.3,
            "maxTokens": 800
        },
        "messages": [
            {"role": "user", "text": full_prompt}
        ]
    }

    response = requests.post(
        url="https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
        headers=headers,
        json=data
    )

    if response.status_code == 200:
        try:
            raw_answer = response.json()["result"]["alternatives"][0]["message"]["text"]
            cleaned_json = extract_json_block(raw_answer)
            triplets = json.loads(cleaned_json)
            if isinstance(triplets, dict):
                return [triplets]
            elif isinstance(triplets, list):
                return triplets
            else:
                return []
        except Exception as e:
            print(f"Ошибка: {e}")
            return []
    else:
        print(f"HTTP {response.status_code}: {response.text}")
        return []
