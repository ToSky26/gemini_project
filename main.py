import os
from google import genai

# Вставьте ваш API-ключ сюда (или добавьте его в Секреты Colab слева в меню "Ключик")
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

# Инициализируем клиента
client = genai.Client(api_key=API_KEY)

# Делаем базовый запрос к Gemini 2.5 Flash
response = client.models.generate_content(
    model="gemini-3.5-flash",
    contents="Напиши ровно фразами: 'Привет, мир! Я на связи.' и пару слов от себя.",
)

print(response.text)
