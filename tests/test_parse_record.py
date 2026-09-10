from kb_parser.records import parse_record


def test_parse_record_extracts_fields_from_quoted_multiline_body():
    record = (
        'KB0016458 Academic Integrity Turnitin Account Request "\r\n'
        'If you have used Turnitin, reset your password.\r\n'
        'Faculty may create an account.\r\n'
        '"'
    )

    result = parse_record(record)

    assert result['kb_number'] == 'KB0016458'
    assert result['category'] == 'Academic'
    assert result['subcategory'] is None
    assert result['title'] == 'Integrity Turnitin Account Request'
    assert 'If you have used Turnitin, reset your password.' in result['body']
    assert 'Faculty may create an account.' in result['body']
    assert '"' not in result['body']


def test_parse_record_detects_doubled_category():
    record = (
        'KB0018063 Adobe Adobe Express Add-ons\r\n'
        'Add-ons are not allowed to be downloaded or installed for Adobe Express.'
    )

    result = parse_record(record)

    assert result['kb_number'] == 'KB0018063'
    assert result['category'] == 'Adobe'
    assert result['subcategory'] == 'Adobe'
    assert result['title'] == 'Express Add-ons'
    assert result['body'] == (
        'Add-ons are not allowed to be downloaded or installed for Adobe Express.'
    )


def test_parse_record_unescapes_doubled_quotes_in_body():
    record = (
        'KB0099999 Network VPN Connect Button "\r\n'
        'Click ""Connect"" to proceed with the VPN setup.\r\n'
        '"'
    )

    result = parse_record(record)

    assert result['title'] == 'VPN Connect Button'
    assert result['body'] == 'Click "Connect" to proceed with the VPN setup.'
    assert '""' not in result['body']


def test_parse_record_detects_multi_word_doubled_category():
    record = (
        'KB0016872 Policies and Procedures Policies and Procedures NATO Alphabet "\r\n\r\n"'
    )

    result = parse_record(record)

    assert result['kb_number'] == 'KB0016872'
    assert result['category'] == 'Policies and Procedures'
    assert result['subcategory'] == 'Policies and Procedures'
    assert result['title'] == 'NATO Alphabet'


def test_parse_record_does_not_falsely_double_two_word_category():
    record = (
        'KB0099001 Active Directory Password Reset Instructions "\r\n'
        'Reset your password using the self-service portal.\r\n'
        '"'
    )

    result = parse_record(record)

    assert result['kb_number'] == 'KB0099001'
    assert result['category'] == 'Active'
    assert result['subcategory'] is None
    assert result['title'] == 'Directory Password Reset Instructions'
