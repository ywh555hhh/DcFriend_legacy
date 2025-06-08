import json
import aiofiles
from pathlib import Path
from .character_model import Character


class CharacterManager:
    def __init__(self, characters_dir: Path):
        self.characters_dir = characters_dir
        if not self.characters_dir.exists():
            raise FileNotFoundError(
                f"Characters directory not found: {self.characters_dir}"
            )

    async def load_character(self, name: str) -> Character:
        character_path = self.characters_dir / f"{name}.json"
        try:
            async with aiofiles.open(character_path, mode="r", encoding="utf-8") as f:
                data = json.loads(await f.read())
            return Character.model_validate(data)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Character card '{name}.json' not found at {character_path}"
            )
        except Exception as e:
            raise ValueError(f"Error parsing character card '{name}.json': {e}")
