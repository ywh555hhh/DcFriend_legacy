from pydantic import BaseModel
from typing import List


class DialogueExample(BaseModel):
    user: str
    bot: str


class Character(BaseModel):
    name: str
    description: str
    first_message: str
    example_dialogue: List[DialogueExample]
    main_chat_prompt_template: str
