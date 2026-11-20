# This code is Apache 2 licensed:
# https://www.apache.org/licenses/LICENSE-2.0
import os
import re
import sys

import aisuite
from dotenv import load_dotenv

from actions import known_actions

load_dotenv()

MODEL = os.getenv("MODEL")
client = aisuite.Client()

prompt = """
You run in a loop of Thought, Action, PAUSE, Observation.
At the end of the loop you output an Answer
Use Thought to describe your thoughts about the question you have been asked.
Use Action to run one of the actions available to you - then return PAUSE.
Observation will be the result of running those actions.
Always start your reply with Thought. Keep each Thought short, one to three sentences.
Write only one Action per reply, then stop and wait for the Observation.
Never give an Answer before you have at least one Observation.
Your final reply must start with "Answer:".
In the Answer, say which Wikipedia page or arXiv paper each fact came from.
If the Observations do not answer the question, say what you found and that your sources do not answer it. Do not fill the gaps from memory.

Your available actions are:

wikipedia_search:
e.g. wikipedia_search: Django
Searches Wikipedia and returns the top page titles with a short snippet

wikipedia_page:
e.g. wikipedia_page: Django (web framework)
Returns the start of a Wikipedia page and the list of its sections
e.g. wikipedia_page: Django (web framework)#History
Returns one section of the page, use a section name as listed
If a section is truncated, ask for one of its subsections

arxiv_search:
e.g. arxiv_search: chain of thought prompting
Searches arXiv for scientific papers and returns the top titles, authors, dates and abstracts

calculate:
e.g. calculate: 4 * 7 / 3
Runs a calculation and returns the number - uses Python so be sure to use floating point syntax if necessary

Always look things up with your actions instead of answering from memory.
Use Wikipedia for general knowledge and arXiv for scientific papers and research.

Example session:

Question: What is the capital of France?
Thought: I should look up France on Wikipedia
Action: wikipedia_page: France
PAUSE

You will be called again with this:

Observation: France is a country in Western Europe. Its capital is Paris.

You then output:

Answer: The capital of France is Paris
""".strip()

action_re = re.compile(r"^Action: (\w+): (.*)$")
answer_re = re.compile(r"Answer:")
FORMAT_REMINDER = 'Your reply had no Action and no Answer. Reply with a Thought and one Action, or start your final reply with "Answer:".'
OUT_OF_TURNS = "You are out of turns. Give your Answer now, using only the Observations so far."
LOOKUP_REMINDER = "You answered without looking anything up. Start with a Thought and use an Action first."


class ChatBot:
    def __init__(self, system_prompt=""):
        self.system_prompt = system_prompt
        self.messages = []
        if self.system_prompt:
            self.messages.append({"role": "system", "content": system_prompt})

    def __call__(self, message):
        self.messages.append({"role": "user", "content": message})
        result = self.execute()
        self.messages.append({"role": "assistant", "content": result})
        return result

    def execute(self):
        completion = client.chat.completions.create(
            model=MODEL, messages=self.messages, stop=["PAUSE", "Observation:"]
        )
        return completion.choices[0].message.content


def query(question, max_turns=8):
    bot = ChatBot(prompt)
    next_prompt = f"Question: {question}"
    looked_up = False
    for _ in range(max_turns):
        result = bot(next_prompt)
        print(result)
        action = parse_action(result)
        if action:
            observation = run_action(*action)
            looked_up = True
        elif answer_re.search(result) and looked_up:
            return result
        elif answer_re.search(result):
            observation = LOOKUP_REMINDER
        else:
            observation = FORMAT_REMINDER
        print("Observation:", observation)
        next_prompt = f"Observation: {observation}"
    result = bot(f"Observation: {observation}\n\n{OUT_OF_TURNS}")
    print(result)
    return result


def parse_action(result):
    actions = [action_re.match(line.strip()) for line in result.split("\n") if action_re.match(line.strip())]
    if not actions:
        return None
    return actions[0].groups()


def run_action(action, action_input):
    if action not in known_actions:
        return f"Unknown action '{action}'. Available actions: {', '.join(known_actions)}"
    print(f" -- running {action} {action_input}")
    try:
        return known_actions[action](action_input)
    except Exception as error:
        return f"Error running {action}: {error}"


if __name__ == "__main__":
    if not os.getenv("USER_AGENT"):
        sys.exit("USER_AGENT is empty. Set it in .env, see .env.example")
    query(" ".join(sys.argv[1:]) or "What does England share borders with?")
