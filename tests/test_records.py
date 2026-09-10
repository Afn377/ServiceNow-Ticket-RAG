from kb_parser.records import parse_record, split_records


def test_split_records_splits_two_quoted_multiline_records():
    text = (
        'Number Category Short description Article body '
        'KB0016458 Academic Integrity Turnitin Account Request "\r\n'
        'If you have used Turnitin, reset your password.\r\n'
        'Faculty may create an account.\r\n'
        '" '
        'KB0016624 Academic Integrity Turnitin Canvas Pairing "\r\n'
        'Pair your Canvas account with Turnitin.\r\n'
        '" '
    )

    records = split_records(text)

    assert len(records) == 2
    assert records[0].startswith('KB0016458')
    assert 'Faculty may create an account.' in records[0]
    assert records[1].startswith('KB0016624')
    assert 'Pair your Canvas account with Turnitin.' in records[1]


def test_split_records_ignores_kb_reference_cited_inside_a_body():
    text = (
        'Number Category Short description Article body '
        'KB0012345 Network VPN Setup "\r\n'
        'See also KB0099999 for troubleshooting steps.\r\n'
        'Contact the help desk if issues persist.\r\n'
        '" '
        'KB0054321 Network VPN Teardown "\r\n'
        'Disconnect the VPN client.\r\n'
        '" '
    )

    records = split_records(text)

    assert len(records) == 2
    assert records[0].startswith('KB0012345')
    assert 'See also KB0099999 for troubleshooting steps.' in records[0]
    assert records[1].startswith('KB0054321')


def test_split_records_handles_unquoted_single_line_body():
    text = (
        'Number Category Short description Article body '
        'KB0018063 Adobe Adobe Express Add-ons\r\n'
        'Add-ons are not allowed to be downloaded or installed for Adobe Express.\r\n'
        'KB0018009 Adobe Discontinuation of Acrobat\r\n'
        'Acrobat is being discontinued.\r\n'
    )

    records = split_records(text)

    assert len(records) == 2
    assert records[0].startswith('KB0018063')
    assert 'Add-ons are not allowed' in records[0]
    assert records[1].startswith('KB0018009')


def test_split_records_not_confused_by_unescaped_prose_quotes_in_body():
    text = (
        'Number Category Short description Article body '
        'KB0018308 Accessibility General Support "\r\n'
        'Click the setting labeled "Advanced, then enable it.\r\n'
        '" '
        'KB0016624 Academic Integrity Turnitin Canvas Pairing "\r\n'
        'Pair your Canvas account with Turnitin.\r\n'
        '" '
    )

    records = split_records(text)

    assert len(records) == 2
    assert records[0].startswith('KB0018308')
    assert records[1].startswith('KB0016624')


def test_split_records_recognizes_kbb_prefixed_records():
    text = (
        'Number Category Short description Article body '
        'KB0016183 General Some Prior Article "\r\n'
        'Body text for the prior article.\r\n'
        '" '
        'KBB0010183 General General - Help Desk and Labs Knowledge PDF "\r\n'
        'This is an archive/admin article using the KBB prefix.\r\n'
        '" '
        'KB0018211 IT Help Desk Next Real Article "\r\n'
        'Body text for the next article.\r\n'
        '" '
    )

    records = split_records(text)

    assert len(records) == 3
    assert records[0].startswith('KB0016183')
    assert records[1].startswith('KBB0010183')
    assert 'KBB prefix' in records[1]
    assert records[2].startswith('KB0018211')


def test_split_records_recovers_records_glued_together_with_no_separator():
    # Real pattern: several short, body-less stub records run together on one
    # line with only a single space between them and no CRLF anywhere.
    text = (
        'Number Category Short description Article body '
        'KB0014457 Desk Phone Support Speed dialing and campus dialing '
        'KB0014453 Desk Phone Support Using Cisco phones '
        'KB0014456 Desk Phone Support Using Cisco Unity Voicemail '
        'KB0015261 Desktop and Mobile Device Support Change your AirDrop settings "\r\n'
        'AirDrop is a fast and convenient way to share files.\r\n'
        '" '
    )

    records = split_records(text)

    assert len(records) == 4
    assert records[0] == 'KB0014457 Desk Phone Support Speed dialing and campus dialing'
    assert records[1] == 'KB0014453 Desk Phone Support Using Cisco phones'
    assert records[2] == 'KB0014456 Desk Phone Support Using Cisco Unity Voicemail'
    assert records[3].startswith('KB0015261')


def test_split_records_does_not_split_on_inline_citation_followed_by_lowercase_word():
    # Real pattern: a KB number used as the grammatical subject of a
    # sentence, e.g. "...password. KB0012583 is available for assistance
    # with logging into LinkedIn Learning." This must NOT be treated as a
    # new record just because it's glued to the previous text with a space.
    text = (
        'Number Category Short description Article body '
        'KB0012345 Connect LinkedIn Learning Login "\r\n'
        'Members of the university login to LinkedIn Learning using their '
        'NetID and password. KB0012583 is available for assistance with '
        'logging into LinkedIn Learning.\r\n'
        '" '
        'KB0012999 Connect Next Real Article "\r\n'
        'Body text.\r\n'
        '" '
    )

    records = split_records(text)

    assert len(records) == 2
    assert 'KB0012583 is available for assistance' in records[0]
    assert records[1].startswith('KB0012999')


def test_split_records_recovers_record_whose_quoted_body_has_no_trailing_newline():
    # Real pattern: a short single-line quoted body (here, just a product
    # name) whose closing quote directly follows the last word, with no CRLF
    # before it - unlike the multi-line case where the closing quote is on
    # its own line.
    text = (
        'Number Category Short description Article body '
        'KB0011708 Microsoft "Microsoft Azure Dev Tools for Teaching - Visio, Project, and Access" '
        'KB0018545 Microsoft Microsoft Copilot Pro License "\r\n'
        'Copilot Pro is currently not a part of our license with Microsoft.\r\n'
        '" '
    )

    records = split_records(text)

    assert len(records) == 2
    assert records[0].startswith('KB0011708')
    assert 'Visio, Project, and Access' in records[0]
    assert records[1].startswith('KB0018545')


def test_parse_record_extracts_kbb_prefixed_kb_number():
    record = (
        'KBB0010183 General General - Help Desk and Labs Knowledge PDF "\r\n'
        'This is an archive/admin article using the KBB prefix.\r\n'
        '"'
    )

    result = parse_record(record)

    assert result['kb_number'] == 'KBB0010183'
    assert result['category'] == 'General'
    assert result['subcategory'] == 'General'


def test_parse_record_handles_id_glued_directly_to_category_with_no_space():
    record = 'KBB0010133FT - Data Security Incident - Experian IdentityWorks\r\n\r\n\r\n\r\n"'

    result = parse_record(record)

    assert result['kb_number'] == 'KBB0010133'
    assert result['category'] == 'FT'


def test_parse_record_handles_id_glued_directly_to_next_line_category():
    record = 'KBB0010202\r\nSupervisor Documentation - Level 1 CIT Training\r\n\r\n\r\n\r\n"'

    result = parse_record(record)

    assert result['kb_number'] == 'KBB0010202'
    assert result['category'] == 'Supervisor'
