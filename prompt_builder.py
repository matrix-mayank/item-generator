"""
Dynamic prompt builder for Reading Comprehension Item Generator.
Builds prompts based on configuration and includes example items from NY/Texas assessments.
"""

import pandas as pd
import os

# Example items from NY/Texas Grade 4 assessments (from CSV analysis)
EXAMPLE_ITEM_1 = """
**Example Item (NY/Texas Grade 4):**

**Passage:** (450 words, 8 paragraphs)
"No one but a man can do this," the business manager of the World, a New York newspaper, said to the young woman. The year was 1888. A popular book at the time told about a character who traveled around the world in 80 days. Now Nellie Bly, a young reporter for the newspaper, wanted to do it in real life.

"Very well," said Nellie. "Start the man, and I'll start the same day for some other newspaper and beat him."

In those days it was very unusual for a woman to travel alone. But Nellie Bly was an unusual woman. Her real name was Elizabeth Jane Cochran. When she was 20, she wrote a fiery letter to the editor of the Pittsburgh Dispatch. The editor was so impressed with her letter that he offered her a job as a writer.

It wasn't considered "proper" to use a woman's name in a newspaper. So the editor signed Elizabeth's work Nellie Bly, a name from a popular song.

Back then, women were only supposed to write about things considered to be "women's topics," such as fashion and society. But Nellie had other ideas. She reported on issues that were important, even controversial. Newspaper readers were fascinated—but they didn't believe that Nellie Bly was really a woman. They thought men were writing the articles!

After Nellie threatened to make the trip for another newspaper, her editor gave in and allowed her to do it for the World. One year after asking to do the trip, Nellie set out. Traveling east across the Atlantic, Nellie took just one bag in order to move quickly. As she traveled, she wrote. She telegraphed her articles about people and places to the newspaper. Schoolchildren followed her route across Europe and Asia. Geography became a national fad as readers tracked her around the world.

On day 68 of her trip, Nellie reached San Francisco. Quickly, she dashed across the country on a train hired by her newspaper. She reached New York in 4 1/2 days.

She met her challenge! Along the way, every train stop was a "maze of happy greetings, happy wishes, congratulating telegrams, fruit, flowers, loud cheers, wild hurrahs, rapid hand-shaking," she wrote. While traveling through France, Nellie was thrilled to meet Jules Verne, author of the book that inspired her trip, Around the World in 80 Days.

Nellie Bly beat the 80-day goal. She also invented a new style of journalism. She reported to her readers what she saw, thought, and felt during her adventure. She also proved that a woman is as competent and resourceful as a man. Her journey around the world was a journey toward equal opportunity for both women and men.

**Question:** What does the phrase "set out" mean as it is used in paragraph 6 of the article?

**Correct Answer:** began her journey

**Distractor 1:** grabbed her suitcase

**Distractor 2:** accepted work

**Distractor 3:** started writing

**Type:** Vocabulary in context
**Flesch-Kincaid Grade Level:** 7.6
**Difficulty (p-value):** 0.85 (easier item)
"""

# Four more diverse examples from data_passage_ques_options_pv.csv (NY/Texas released items)
EXAMPLE_ITEM_2 = """
**Example 2 (Vocabulary in context):**
**Passage (excerpt):** King Tiger thought he was the greatest tiger in the world. He was certainly the greediest. He called three of his strongest tigers and said, "I have a job for you." He demanded they bring him food from the Island of Borneo.
**Question:** What does the word "demand" mean as it is used in paragraphs 2 and 21?
**Target Answer:** to insist
**Distractor 1:** to correct
**Distractor 2:** to look for
**Distractor 3:** to work on
"""

EXAMPLE_ITEM_3 = """
**Example 3 (Comprehension / author's craft):**
**Passage (excerpt):** In the days when farmers worked with ox and sled and cut the dark with lantern light, there lived a boy who loved snow more than anything. Willie Bentley's happiest days were snowstorm days. He watched snowflakes on his mittens, on the dried grass of Vermont farm fields.
**Question:** Read this sentence from paragraph 1: "In the days when farmers worked with ox and sled and cut the dark with lantern light, there lived a boy who loved snow more than anything." How does this sentence help the reader?
**Target Answer:** by showing that the events in the passage happened long ago
**Distractor 1:** by suggesting that the ideas in the passage are made up
**Distractor 2:** by showing that the subject of the passage became famous
**Distractor 3:** by suggesting that the topic of the passage is familiar
"""

EXAMPLE_ITEM_4 = """
**Example 4 (Comprehension / structure):**
**Passage (excerpt):** In a valley in the highlands of Scotland, there once lived a young tenant farmer, Gregor, and his widowed mother. Although they worked hard, they could never accumulate enough money to buy the flock of sheep they longed to have. Later, Gregor's fortunes change through the story.
**Question:** How do paragraphs 1 and 23 relate to each other?
**Target Answer:** They show the change in Gregor's life during the story.
**Distractor 1:** They show what Gregor has learned in the story.
**Distractor 2:** They show how MacTavish changes in the story.
**Distractor 3:** They show the growth of MacTavish's fortune during the story.
"""

EXAMPLE_ITEM_5 = """
**Example 5 (Main idea / idea developed):**
**Passage (excerpt):** "Come," Wangari's mother called. She beckoned her daughter to a tall tree with a wide trunk and a crown of green, oval leaves. "Feel," her mother whispered. Wangari spread her hands over the tree's trunk. "This is the mugumo," her mother said. The tree was important to the people and animals.
**Question:** What idea is developed in paragraphs 4 through 7?
**Target Answer:** Mugumo trees are important to people and animals.
**Distractor 1:** Wangari and her mother want to plant more trees.
**Distractor 2:** Mugumo trees can provide shade to many people.
**Distractor 3:** Wangari and her mother think education is important.
"""

def build_system_prompt(config, user_message, custom_manual=None):
    """
    Build a dynamic system prompt based on configuration settings.
    
    Args:
        config: Dictionary containing configuration settings
        user_message: User's request/message
        custom_manual: Optional text from uploaded manual
    
    Returns:
        Complete system prompt string
    """
    
    word_count = config.get('passage_word_count', 20)
    # Ensure we have a valid integer (session might have stored something unexpected)
    try:
        word_count = int(word_count)
    except (TypeError, ValueError):
        word_count = 20
    word_count = max(10, min(1000, word_count))
    
    try:
        num_distractors = int(config.get('distractors_per_question', 2))
    except (TypeError, ValueError):
        num_distractors = 2
    num_distractors = max(2, min(4, num_distractors))
    print(f"[prompt_builder] num_distractors={num_distractors}, raw config={config.get('distractors_per_question')}")
    grade_level = config.get('grade_level', 4)
    standards = ', '.join(config.get('state_standards', ['NY', 'TX']))
    inference_type = config.get('inference_type', 'all')
    question_types = ', '.join(config.get('question_types', ['vocabulary', 'comprehension', 'inference']))
    
    # Build inference type guidance
    inference_guidance = ""
    if inference_type == 'text-explicit':
        inference_guidance = """
**INFERENCE TYPE: Text-Explicit**
- Answers should be verbatim or near-verbatim in the passage
- Create grammatical links between questions and answers
- Use exact passage wording
"""
    elif inference_type == 'text-implicit':
        inference_guidance = """
**INFERENCE TYPE: Text-Implicit**
- Combine adjacent passage details
- No grammatical link between question and answer
- Use passage vocabulary (no synonyms or elevated terms)
- Local coherence only
"""
    elif inference_type == 'script-implicit':
        inference_guidance = """
**INFERENCE TYPE: Script-Implicit**
- Requires world knowledge combined with passage
- No grammatical link between question and answer
- Global coherence
- May use terms not in passage
"""
    else:  # all
        inference_guidance = """
**INFERENCE TYPES: Mix of all types**
- Include Text-Explicit (verbatim answers from passage)
- Include Text-Implicit (combine adjacent details, use passage vocabulary)
- Include Script-Implicit (world knowledge + passage, global coherence)
"""
    
    # When a manual is uploaded, put it FIRST so the model prioritizes it
    prompt = ""
    if custom_manual:
        prompt += f"""**PRIORITY — CUSTOM GUIDELINES (uploaded manual). YOU MUST FOLLOW THESE FOR EVERY ITEM:**
The user has uploaded custom guidelines. Apply these rules to every item you generate. For wording, style, vocabulary, question types, content rules, and rubrics, the manual overrides default instructions.

{custom_manual}

**PRECEDENCE:** Only passage length, number of distractors, and grade level come from CONFIGURATION below; for everything else (style, wording, content, question types), follow the manual above.

---

"""

    prompt += f"""You are an expert educational assessment designer creating reading comprehension items for standardized assessments.

**CONFIGURATION (you MUST follow these exactly):**
- Passage Length: EXACTLY {word_count} words — count the words; the passage must not exceed {word_count} words.
- Number of Questions: 1 (one question per passage)
- Distractors per Question: {num_distractors}
- Grade Level: Grade {grade_level}
- Standards: {standards}
- Question Types: {question_types}
"""
    if custom_manual:
        prompt += "\n- **Style and content:** Follow the CUSTOM GUIDELINES (uploaded manual) at the top of these instructions for every item.\n"

    prompt += """
**BEHAVIOR:**
- Do NOT ask the user to clarify or choose between options. The configuration above is fixed (from the settings bar). Always generate one item that matches it.
- When the user gives a topic (e.g. "climate change", "space exploration"), create an item on that topic using these exact settings. Do not offer "Option 1 vs Option 2" or different word counts—use the passage length and 1 question from the configuration.
- When the user asks for a change (e.g. "change the names", "make it harder", "generate a new one", "different topic"), output the revised or new item in the same format below so it can be displayed. Again, follow the configuration; do not ask for clarification.

"""
    prompt += f"""
**ITEM FORMAT (Based on {standards} Grade {grade_level} assessments):**

**Passage Requirements (STRICT):**
- The passage MUST be exactly {word_count} words. No more, no less. Count carefully.
- Divide into clear paragraphs (for short passages like {word_count} words, use 1-3 paragraphs)
- Age-appropriate content for Grade {grade_level} students
- Engaging and educational topic
- Clear narrative or expository structure
- Target Flesch-Kincaid reading level around Grade {grade_level + 2} to {grade_level + 4}

**CRITICAL:** If the user asked for {word_count} words, your passage must be exactly {word_count} words. Count before submitting.

**Question Requirements:**
- Create ONE question for the passage
- Question type should be: {question_types}
- Question should test comprehension at an appropriate level
- Reference specific paragraphs when appropriate
- Format questions clearly (e.g., "What does X mean as used in paragraph Y?" or "Read this sentence...")

{inference_guidance}

**Answer Format:**
- 1 correct answer + {num_distractors} plausible distractors
- All distractors must be plausible but clearly incorrect
- Distractors should reflect common misconceptions or partial understanding
- Avoid "none of the above" or obvious wrong answers
- Use proper capitalization: capitalise the first letter of the Target Answer and each Distractor (sentence case).

**Question Style Examples (from authentic {standards} items):**
- Vocabulary: "What does the phrase 'set out' mean as it is used in paragraph 6?"
- Comprehension: "Read this sentence from paragraph 6... How is this detail important to paragraph 1?"
- Inference: "Why did [character] [action]? Use details from the passage."
- Main Idea: "What is the main idea of this passage?"
- Detail: "According to the passage, what happened after [event]?"

---

**Example items (NY/Texas released items — vary question type and style):**

{EXAMPLE_ITEM_1}

{EXAMPLE_ITEM_2}

{EXAMPLE_ITEM_3}

{EXAMPLE_ITEM_4}

{EXAMPLE_ITEM_5}

---
"""

    prompt += f"""
**USER REQUEST:** {user_message}

**CRITICAL: This item MUST have exactly {num_distractors} wrong-answer options (distractors).** Output Distractor 1, Distractor 2{f", Distractor 3" if num_distractors >= 3 else ""}{f", Distractor 4" if num_distractors >= 4 else ""}—no more, no fewer.
"""
    if custom_manual:
        prompt += "\n**REMINDER: Apply the CUSTOM GUIDELINES (uploaded manual) at the top of these instructions to this item—wording, style, vocabulary, question types, and content must follow the manual.**\n\n"

    prompt += f"""
**OUTPUT FORMAT:**

Output ONLY the item below. You MUST include exactly {num_distractors} distractors (Distractor 1, Distractor 2{f", Distractor 3" if num_distractors >= 3 else ""}{f", Distractor 4" if num_distractors >= 4 else ""}). Do not add design notes, explanations, or metadata—only this block.

```
Passage: [Your passage here, exactly {word_count} words, divided into paragraphs]

Question: [Your question]

Target Answer: [Correct answer]

Distractor 1: [First wrong answer]

Distractor 2: [Second wrong answer]
{f'''
Distractor 3: [Third wrong answer]''' if num_distractors >= 3 else ""}{f'''
Distractor 4: [Fourth wrong answer]''' if num_distractors >= 4 else ""}
```

Generate a high-quality assessment item that is fair, unbiased, and appropriate for Grade {grade_level} students.

Reply with only the item in the format above (Passage, Question, Target Answer, Distractor 1, 2, ...). No preamble, no "Which would you prefer?", no options—just the item.
"""

    return prompt


def build_chat_system_message(has_custom_manual=False):
    """Build the system message for the chat interface.
    has_custom_manual: if True, the user has uploaded guidelines; add a reminder to follow them."""
    base = """You are an expert educational content designer assistant helping create reading comprehension items for standardized assessments.

When a user asks you to create or revise an item, you should:
1. Always follow the CONFIGURATION in your instructions (passage length, 1 question, distractors, grade level). Do not ask the user to choose between options or clarify—those settings are already set in the app.
2. When the user names a topic (e.g. "climate change", "space exploration"), generate one item on that topic using the configured settings. Output the item in the exact format: Passage:, Question:, Target Answer:, Distractor 1:, Distractor 2:, etc. so it appears in the right panel.
3. When the user asks for a revision (e.g. "change the names", "make it harder", "generate a new one", "different topic"), produce the revised or new item in the same format. The right panel will update when you output that format—no need to ask what they want.
4. Output only the item block (Passage, Question, Target Answer, Distractors). No "Which would you prefer?", no options, no design notes. Just the item.

Remember:
- Follow the specified standards (NY/Texas format by default) and the configuration from the settings bar.
- Ensure all items are appropriate for the target grade level."""
    if has_custom_manual:
        base += """

**If the instructions below include CUSTOM GUIDELINES (uploaded manual), you MUST follow those guidelines for every item—wording, style, vocabulary, question types, and content rules from the manual are required.**"""
    return base
