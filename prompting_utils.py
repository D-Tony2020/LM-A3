import os
import re


def read_schema(schema_path):
    """Return the schema file as a single string for prompting use."""
    with open(schema_path, 'r', encoding='utf-8') as f:
        return f.read()


_SQL_FENCE_RE = re.compile(r'```(?:sql)?\s*(.*?)```', re.DOTALL | re.IGNORECASE)
_SELECT_RE = re.compile(r'(SELECT\b[^;]*;?)', re.IGNORECASE | re.DOTALL)


def extract_sql_query(response):
    """Pull the first plausible SQL query out of an LLM response.

    Handles fenced code blocks, inline `SQL:` prefixes, and bare SELECT
    statements. Returns a single-line SQL string, or an empty string when
    nothing SQL-shaped is found.
    """
    if response is None:
        return ''

    text = response.strip()

    fence_match = _SQL_FENCE_RE.search(text)
    if fence_match:
        text = fence_match.group(1).strip()

    for prefix in ('SQL:', 'sql:', 'Query:', 'Answer:'):
        idx = text.find(prefix)
        if idx >= 0:
            text = text[idx + len(prefix):].lstrip()
            break

    select_match = _SELECT_RE.search(text)
    if select_match:
        text = select_match.group(1)

    text = text.replace('\n', ' ').replace('\r', ' ')
    text = re.sub(r'\s+', ' ', text).strip()
    text = text.rstrip(';').strip()
    return text


def save_logs(output_path, sql_em, record_em, record_f1, error_msgs):
    """Save the logs of the experiment to files."""
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(
            f'SQL EM: {sql_em}\n'
            f'Record EM: {record_em}\n'
            f'Record F1: {record_f1}\n'
            f'Model Error Messages: {error_msgs}\n'
        )
