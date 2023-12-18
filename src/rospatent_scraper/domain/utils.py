import re
from typing import Optional


def remove_xml_tags(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    return re.sub(r'<(.*?)>', '', text)


def clean_id(id: str):
    return id.replace('\n', '')
