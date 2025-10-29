import asyncio
import json
import re
from collections.abc import AsyncGenerator
from typing import Any

from config.settings import OPENAI_API_KEY
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI


class LLMAnswerAnalyzer:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo", openai_api_key=OPENAI_API_KEY, temperature=0.3
        )

        self.analysis_prompt = ChatPromptTemplate.from_template("""
Ты опытный технический интервьюер. Проанализируй ответ кандидата на техническое интервью.

ВОПРОС: {question}

ЭТАЛОННЫЙ ОТВЕТ: {expert_answer}

ОТВЕТ КАНДИДАТА: {user_answer}

Проанализируй ответ кандидата по следующим критериям:
1. Техническая точность (0-100): Насколько правильно используются технические термины и концепции
2. Полнота (0-100): Покрывает ли ответ все ключевые аспекты вопроса
3. Ясность (0-100): Насколько понятно и структурированно изложен ответ
4. Глубина понимания (0-100): Демонстрирует ли кандидат глубокое понимание темы
5. Практическое применение (0-100): Приводит ли примеры, лучшие практики

Для каждого критерия укажи:
- Оценку (0-100)
- Конкретные замечания о том, что сделано хорошо или что упущено
- Конкретные рекомендации для улучшения

ВАЖНЫЕ ПРИНЦИПЫ ОЦЕНКИ:
- НЕ снижай оценки за грамматические ошибки или опечатки
- Фокусируйся только на техническом содержании
- Если ответ кандидата противоречит эталонному ответу, техническая точность = 0
- Если ответ частично правильный - соответствующий балл по каждому критерию
- Если ответ полностью соответствует эталонному - высокие баллы по всем критериям

Отвечай СТРОГО в формате JSON:
{{
    "technical_accuracy": {{
        "score": <число от 0 до 100>,
        "positive": "<что сделано хорошо>",
        "negative": "<что неверно или упущено>",
        "recommendation": "<конкретная рекомендация>"
    }},
    "completeness": {{
        "score": <число от 0 до 100>,
        "positive": "<что сделано хорошо>",
        "negative": "<что неверно или упущено>",
        "recommendation": "<конкретная рекомендация>"
    }},
    "clarity": {{
        "score": <число от 0 до 100>,
        "positive": "<что сделано хорошо>",
        "negative": "<что неверно или упущено>",
        "recommendation": "<конкретная рекомендация>"
    }},
    "depth": {{
        "score": <число от 0 до 100>,
        "positive": "<что сделано хорошо>",
        "negative": "<что неверно или упущено>",
        "recommendation": "<конкретная рекомендация>"
    }},
    "practical_application": {{
        "score": <число от 0 до 100>,
        "positive": "<что сделано хорошо>",
        "negative": "<что неверно или упущено>",
        "recommendation": "<конкретная рекомендация>"
    }},
    "overall_score": <среднее арифметическое всех критериев>,
    "key_missing_points": ["<конкретный пункт 1>", "<конкретный пункт 2>"],
    "strengths": ["<сильная сторона 1>", "<сильная сторона 2>"],
    "priority_improvements": ["<приоритетная область 1>", "<приоритетная область 2>"],
    "is_valid": <true/false>
}}
""")

        self.feedback_prompt = ChatPromptTemplate.from_template("""
Ты виртуальный интервьюер для технического собеседования.

ВОПРОС: {question}

ОТВЕТ КАНДИДАТА: {user_answer}

ДЕТАЛЬНЫЙ АНАЛИЗ: {detailed_analysis}

Дай КРАТКУЮ конструктивную обратную связь кандидату (максимум 3-4 предложения):

1. КРАТКОЕ РЕЗЮМЕ: Общая оценка ответа в 1-2 предложениях
2. ГЛАВНАЯ ПРОБЛЕМА: Самый важный недостаток (если есть)
3. КЛЮЧЕВАЯ РЕКОМЕНДАЦИЯ: Одна конкретная рекомендация для улучшения

ВАЖНО:
- НЕ обращай внимание на грамматические ошибки
- Фокусируйся только на техническом содержании
- Будь лаконичным и конкретным
- Избегай повторений и общих фраз

Пиши от первого лица, как настоящий интервьюер.
""")

    async def analyze_answer(
        self, question: str, expert_answer: str, user_answer: str
    ) -> dict[str, Any]:
        if not user_answer or not user_answer.strip():
            return {
                "score": 0,
                "comment": "Ответ пустой",
                "is_valid": False,
                "detailed_analysis": {
                    "technical_accuracy": {
                        "score": 0,
                        "positive": "",
                        "negative": "Ответ не предоставлен",
                        "recommendation": "Предоставьте ответ на вопрос",
                    },
                    "completeness": {
                        "score": 0,
                        "positive": "",
                        "negative": "Ответ не предоставлен",
                        "recommendation": "Предоставьте ответ на вопрос",
                    },
                    "clarity": {
                        "score": 0,
                        "positive": "",
                        "negative": "Ответ не предоставлен",
                        "recommendation": "Предоставьте ответ на вопрос",
                    },
                    "depth": {
                        "score": 0,
                        "positive": "",
                        "negative": "Ответ не предоставлен",
                        "recommendation": "Предоставьте ответ на вопрос",
                    },
                    "practical_application": {
                        "score": 0,
                        "positive": "",
                        "negative": "Ответ не предоставлен",
                        "recommendation": "Предоставьте ответ на вопрос",
                    },
                    "overall_score": 0,
                    "key_missing_points": ["Ответ не предоставлен"],
                    "strengths": [],
                    "priority_improvements": ["Предоставить ответ на вопрос"],
                },
            }

        response = await self.llm.ainvoke(
            self.analysis_prompt.format(
                question=question, expert_answer=expert_answer, user_answer=user_answer
            )
        )

        try:
            json_match = re.search(r"\{.*\}", response.content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())

                # Ensure overall_score is within bounds
                overall_score = max(0, min(100, result.get("overall_score", 0)))

                # For backward compatibility, still provide old format
                return {
                    "score": overall_score,
                    "comment": self._generate_summary_comment(result),
                    "is_valid": result.get("is_valid", True),
                    "detailed_analysis": result,
                }
        except (json.JSONDecodeError, AttributeError):
            pass

        return {
            "score": 0,
            "comment": "Не удалось проанализировать ответ",
            "is_valid": True,
            "detailed_analysis": {
                "technical_accuracy": {
                    "score": 0,
                    "positive": "",
                    "negative": "Ошибка анализа",
                    "recommendation": "Попробуйте переформулировать ответ",
                },
                "completeness": {
                    "score": 0,
                    "positive": "",
                    "negative": "Ошибка анализа",
                    "recommendation": "Попробуйте переформулировать ответ",
                },
                "clarity": {
                    "score": 0,
                    "positive": "",
                    "negative": "Ошибка анализа",
                    "recommendation": "Попробуйте переформулировать ответ",
                },
                "depth": {
                    "score": 0,
                    "positive": "",
                    "negative": "Ошибка анализа",
                    "recommendation": "Попробуйте переформулировать ответ",
                },
                "practical_application": {
                    "score": 0,
                    "positive": "",
                    "negative": "Ошибка анализа",
                    "recommendation": "Попробуйте переформулировать ответ",
                },
                "overall_score": 0,
                "key_missing_points": ["Ошибка анализа"],
                "strengths": [],
                "priority_improvements": ["Попробуйте переформулировать ответ"],
            },
        }

    def _generate_summary_comment(self, detailed_analysis: dict[str, Any]) -> str:
        """Generate a summary comment from detailed analysis for backward compatibility."""
        if not detailed_analysis:
            return "Анализ недоступен"

        priority_improvements = detailed_analysis.get("priority_improvements", [])
        key_missing = detailed_analysis.get("key_missing_points", [])

        if priority_improvements:
            return f"Приоритетные области для улучшения: {', '.join(priority_improvements[:2])}"
        elif key_missing:
            return f"Ключевые упущения: {', '.join(key_missing[:2])}"
        else:
            return "Анализ завершен"

    async def generate_feedback(
        self, question: str, user_answer: str, analysis: dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        detailed_analysis = analysis.get("detailed_analysis", {})

        # Format detailed analysis for the prompt
        detailed_analysis_text = self._format_detailed_analysis(detailed_analysis)

        async for chunk in self.llm.astream(
            self.feedback_prompt.format(
                question=question,
                user_answer=user_answer,
                detailed_analysis=detailed_analysis_text,
            )
        ):
            if hasattr(chunk, "content") and chunk.content:
                yield chunk.content
                await asyncio.sleep(0.01)

    def _format_detailed_analysis(self, detailed_analysis: dict[str, Any]) -> str:
        """Format detailed analysis for the feedback prompt."""
        if not detailed_analysis:
            return "Анализ недоступен"

        formatted_sections = []

        # Criteria scores and feedback
        criteria = [
            ("Техническая точность", "technical_accuracy"),
            ("Полнота", "completeness"),
            ("Ясность", "clarity"),
            ("Глубина понимания", "depth"),
            ("Практическое применение", "practical_application"),
        ]

        formatted_sections.append("ОЦЕНКИ ПО КРИТЕРИЯМ:")
        for name, key in criteria:
            criterion = detailed_analysis.get(key, {})
            score = criterion.get("score", 0)
            positive = criterion.get("positive", "")
            negative = criterion.get("negative", "")
            recommendation = criterion.get("recommendation", "")

            formatted_sections.append(f"{name}: {score}/100")
            if positive:
                formatted_sections.append(f"  ✓ {positive}")
            if negative:
                formatted_sections.append(f"  ✗ {negative}")
            if recommendation:
                formatted_sections.append(f"  → {recommendation}")

        # Overall score
        overall_score = detailed_analysis.get("overall_score", 0)
        formatted_sections.append(f"\nОБЩАЯ ОЦЕНКА: {overall_score}/100")

        # Strengths
        strengths = detailed_analysis.get("strengths", [])
        if strengths:
            formatted_sections.append("\nСИЛЬНЫЕ СТОРОНЫ:")
            for strength in strengths:
                formatted_sections.append(f"  ✓ {strength}")

        # Key missing points
        key_missing = detailed_analysis.get("key_missing_points", [])
        if key_missing:
            formatted_sections.append("\nКЛЮЧЕВЫЕ УПУЩЕНИЯ:")
            for missing in key_missing:
                formatted_sections.append(f"  ✗ {missing}")

        # Priority improvements
        priority_improvements = detailed_analysis.get("priority_improvements", [])
        if priority_improvements:
            formatted_sections.append("\nПРИОРИТЕТНЫЕ ОБЛАСТИ ДЛЯ УЛУЧШЕНИЯ:")
            for improvement in priority_improvements:
                formatted_sections.append(f"  → {improvement}")

        return "\n".join(formatted_sections)
