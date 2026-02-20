import json
from pathlib import Path

from .paths import i18n_dir


class I18N:
    def __init__(self, lang: str) -> None:
        self.lang: str = lang
        self.data: dict[str, str] = self._load(self.lang)

    def _load(self, lang: str) -> dict[str, str]:
        """
        Load the language .json from i18n.
        
        Parameters
        ----------
        lang: str
            Language key ("en", "es")
        
        Returns
        ------
        dict[str, str]:
            The language dictionary
        """
        path: Path = i18n_dir() / f"{lang}.json"
        raw = json.loads(path.read_text(encoding="utf-8"))
        return {str(k): str(v) for k, v in (raw or {}).items()}

    def t(self, key: str, **kwargs) -> str:
        """
        Formats the string data at the given language.
        
        Parameters
        ----------
        key: str
            The key in the dictionary
        
        Returns
        -------
        str:
            The formated value
        """
        s = self.data.get(key, key)
        return s.format(**kwargs)
