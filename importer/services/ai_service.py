import os

from openai import OpenAI


class AIService:
    """
    Converts extracted textbook content into
    well-structured classroom notes.
    """

    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
        )

        self.model = "openai/gpt-5"

    def generate_notes(
        self,
        grade,
        subject,
        topic,
        title,
        extracted_text,
    ):
        """
        Convert textbook pages into classroom-ready HTML notes.
        """

        prompt = f"""
You are an experienced teacher, curriculum developer, and textbook author.

Your task is to rewrite textbook pages into engaging classroom notes for students.

==========================
CONTEXT
==========================

Grade: {grade}
Subject: {subject}
Topic: {topic}
Lesson Title: {title}

==========================
IMPORTANT RULES
==========================

1. Never invent facts.

2. Keep all important concepts.

3. Explain difficult ideas using simple English.

4. Remove:
   - page numbers
   - headers
   - footers
   - copyright notices
   - repeated titles

5. Combine broken sentences.

6. Organize the lesson naturally.

7. Use proper educational language.

8. Add headings where necessary.

9. Keep examples from the textbook.

10. If the explanation is too short, improve it WITHOUT changing the meaning.

==========================
OUTPUT FORMAT
==========================

Return ONLY valid HTML.

Do NOT return Markdown.

Do NOT wrap the response inside ```html.

Use only these HTML tags:

<h2>
<h3>
<h4>
<p>
<ul>
<ol>
<li>
<strong>
<em>
<table>
<tr>
<th>
<td>
<hr>

==========================
LESSON STRUCTURE
==========================

<h2>Lesson Title</h2>

Short introduction.

Definitions.

Main explanation.

Important points.

Worked examples.

Conclusion.

Summary.

==========================
TEXTBOOK CONTENT
==========================

{extracted_text}
"""

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0.2,
            max_tokens=8000,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert teacher who produces "
                        "high-quality classroom notes in HTML."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        return response.choices[0].message.content.strip()