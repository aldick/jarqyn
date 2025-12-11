import json
import asyncio
from google import genai
from google.genai.errors import ServerError
from app.core.config import settings
from app.models.report import ReportCategory

client = genai.Client()
MODEL_NAME = "gemini-2.5-flash"

categories_list = [c.value for c in ReportCategory]
categories_str = ", ".join([f'"{c}"' for c in categories_list])

PROMPT_TEMPLATE = f"""
### Основные инструкции

Вы — эксперт в области **обработки отчетов и категоризации с использованием ИИ**. Ваша задача — проанализировать отправленный пользователем отчет (состоящий из текстового **описания**) и преобразовать его в стандартизированную, понятную и пригодную для использования структуру данных. Пользователь может отправить запрос на **английском, испанском или французском языке**. Вы **обязаны** обработать запрос и вывести окончательный результат на **русском языке**.

### Входные переменные

ИИ получит от пользователя следующие переменные:

1. **`USER_DESCRIPTION`**: Необработанный, неотредактированный текст, отправленный пользователем. Он может быть кратким, содержать орфографические ошибки или быть грамматически некорректным.

### Этапы обработки и ограничения

ИИ должен выполнить следующие четыре шага и соблюдать все ограничения:

1.  **Создать `TITLE`**: Создать краткий, профессиональный и информативный заголовок (максимум 8 слов), суммирующий основную проблему из описания пользователя.
2.  **Улучшить `DESCRIPTION`**:
* **Грамматика/Ясность:** Исправьте все грамматические ошибки, орфографические ошибки и неуклюжие формулировки в `USER_DESCRIPTION`.
* **Улучшение:** Сделайте описание более формальным, ясным и подробным.
* **Действующие действия:** Убедитесь, что окончательное описание готово к использованию командой технического обслуживания или аварийной службой.
3.  **Определение `PRIORITY`**: Выберите наиболее подходящий уровень приоритета из следующих четырех вариантов. Основывайте свой выбор на потенциальной опасности, непосредственном влиянии на общественную безопасность и серьезности описанной проблемы.
      * *Варианты:* `["low", "medium", "high", "critical"]`
4.  **Определение `CATEGORY`**:  Выберите из предоставленного списка категорию, наиболее подходящую для отчета. Если проблема соответствует нескольким категориям, выберите ту, которая представляет наибольший риск или непосредственную причину отчета. В результат напиши порядковый номер категории (1-{len(categories_list)}).
      * *Параметры:* `[{categories_str}]`

### Формат вывода

Конечный результат **должен** представлять собой чистый JSON-объект со следующей структурой, использующий ключи на английском языке:

{{
"title": "[Сгенерированный заголовок на русском языке]",
"description": "[Расширенное, грамматически правильное описание на русском языке]",
"priority": "[low | medium | high | critical]",
"category_id": [Порядковый номер категории 1-{len(categories_list)}],
"original_language": "[Язык оригинала]"
}}
"""

async def analyze_report_text(user_text: str) -> dict:
    """
    Analyzes the user text using Gemini to generate a structured report.
    Returns a dictionary with title, description, category, and priority.
    """
    try:
        prompt = f"""
        {PROMPT_TEMPLATE}
        
        USER_DESCRIPTION: "{user_text}"
        """

        max_retries = 5
        base_delay = 2
        
        response = None
        last_error = None

        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=MODEL_NAME,
                    contents=prompt
                )
                break # Success, exit loop
            except ServerError as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = base_delay * (2 ** attempt)
                    print(f"Gemini ServerError (503), retrying in {wait_time}s... (Attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"Gemini ServerError: Max retries exhausted.")
                    raise last_error # Re-raise to be caught by outer try/except or just fail
            except Exception as e:
                 # valid to catch other transient network errors here if needed, 
                 # but sticking to ServerError as requested for 503.
                 # If it's another error (like 400), we probably shouldn't retry blindly.
                 raise e 

        
        text_response = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(text_response)
        
        category_id = data.get("category_id")
        category_enum = ReportCategory.OTHER
        
        enum_members = list(ReportCategory)
        
        if isinstance(category_id, int) and 1 <= category_id <= len(enum_members):
            category_enum = enum_members[category_id - 1]
            
        data["category"] = category_enum
        
        return data

    except Exception as e:
        print(f"Error in Gemini analysis: {e}")
        import traceback
        traceback.print_exc()
        return {
            "title": "Новый отчет",
            "description": user_text or "Описание отсутствует.",
            "category": ReportCategory.OTHER,
            "priority": "medium",
            "original_language": "Unknown"
        }
