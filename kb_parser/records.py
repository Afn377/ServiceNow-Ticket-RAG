import re

_KB_ID = re.compile(r'KBB?\d{7}')


def _is_record_boundary(body: str, start: int, end: int) -> bool:
    """A KB-number (KB followed by 7 digits) match is a genuine boundary if
    EITHER of two structural signals holds.

    Path 1 (explicit separator): the text right before the match (after
    optionally stripping ONE trailing space) ends with the structural end of
    the previous record: either an unquoted body terminator ('\\r\\n') or a
    quoted body terminator ('\\r\\n"').

    Path 2 (glued new record): the match is immediately followed by exactly
    one space and then an UPPERCASE ASCII letter, i.e. the start of the next
    record's Category field. Real exports contain records glued directly to
    the previous record's text, both body-less stubs run together on one line
    ("...campus dialing KB0014453 Desk Phone Support...") and single-line
    quoted bodies whose closing quote has no preceding '\\r\\n'
    ('...Access" KB0018545 Microsoft ...'). Both are followed by
    " <Uppercase>".

    Prose quote marks inside a body are irrelevant to this test. An inline
    citation is excluded because it is neither preceded by '\\r\\n' nor
    followed by " <Uppercase>": a citation continues in prose with a
    lowercase word ("...KB0012583 is available..."), a period ("found at
    KB0014281."), or a URL/CRLF continuation ("sysparm_article=KB0012508",
    "such as KB1234567\\r\\n")."""
    preceding = body[:start]
    if preceding.endswith(' '):
        preceding = preceding[:-1]
    if preceding.endswith('\r\n') or preceding.endswith('\r\n"'):
        return True

    following = body[end:end + 2]
    return len(following) == 2 and following[0] == ' ' and 'A' <= following[1] <= 'Z'


def split_records(text: str) -> list[str]:
    first = _KB_ID.search(text)
    body = text[first.start():]

    # The first record starts right after the file header line, with no
    # preceding boundary marker, so seed the list with its position.
    starts = [0]
    for match in _KB_ID.finditer(body):
        if match.start() == 0:
            continue
        if _is_record_boundary(body, match.start(), match.end()):
            starts.append(match.start())
    starts.append(len(body))

    return [body[start:end].strip() for start, end in zip(starts, starts[1:])]


def parse_record(record: str) -> dict:
    match = _KB_ID.match(record)
    kb_number = match.group()
    # The ID may be followed by a space ("KB0010183 General ..."), by nothing
    # at all ("KBB0010133FT - ...") or by a bare newline
    # ("KBB0010202\r\nSupervisor ..."), so slice off the matched ID and strip
    # whatever separator (or none) follows it.
    rest = record[match.end():].lstrip('\r\n ')

    tokens = rest.split(' ')

    # The KB export repeats the category back-to-back when a subcategory is
    # present (e.g. "Adobe Adobe Express Add-ons" or the multi-word
    # "Policies and Procedures Policies and Procedures NATO Alphabet"). Detect
    # the longest N-word span (N = 3, 2, 1) whose two consecutive occurrences
    # are exactly equal token-for-token.
    category_token_count = None
    for n in (3, 2, 1):
        if len(tokens) >= 2 * n and tokens[:n] == tokens[n:2 * n]:
            category_token_count = n
            break

    if category_token_count is not None:
        category = ' '.join(tokens[:category_token_count])
        subcategory = category
        rest_start = len(' '.join(tokens[:2 * category_token_count])) + 1
    else:
        category = tokens[0]
        subcategory = None
        rest_start = len(tokens[0]) + 1

    remainder = rest[rest_start:]

    quote_start = remainder.find('"')
    newline_start = remainder.find('\r\n')
    if quote_start == -1:
        title_end = newline_start
    elif newline_start == -1:
        title_end = quote_start
    else:
        title_end = min(quote_start, newline_start)

    title = remainder[:title_end].strip()
    body_raw = remainder[title_end:].strip()

    if body_raw.startswith('"') and body_raw.endswith('"'):
        body_raw = body_raw[1:-1]
    body = body_raw.replace('""', '"').replace('\r\n', '\n').strip('\n \t')
    body = body.replace('\r', '')

    return {
        'kb_number': kb_number,
        'category': category,
        'subcategory': subcategory,
        'title': title,
        'body': body,
    }
