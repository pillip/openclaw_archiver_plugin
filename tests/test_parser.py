"""Tests for parser module — URL extraction, /p option, save args."""

from openclaw_archiver.parser import extract_project_option, extract_url, parse_save


class TestExtractProjectOption:
    """Verify /p <project> extraction from end of string."""

    def test_basic_project_extraction(self) -> None:
        text, project = extract_project_option("text /p Backend")
        assert text == "text"
        assert project == "Backend"

    def test_no_project_option(self) -> None:
        text, project = extract_project_option("text without project")
        assert text == "text without project"
        assert project is None

    def test_project_with_trailing_whitespace(self) -> None:
        text, project = extract_project_option("title /p MyProject   ")
        assert text == "title"
        assert project == "MyProject"

    def test_project_not_matched_in_middle(self) -> None:
        """Ensure /p inside a word (e.g. 'a/p') is not matched."""
        text, project = extract_project_option("check a/p value")
        assert text == "check a/p value"
        assert project is None

    def test_empty_string(self) -> None:
        text, project = extract_project_option("")
        assert text == ""
        assert project is None

    def test_only_project_option(self) -> None:
        text, project = extract_project_option(" /p Solo")
        assert text == ""
        assert project == "Solo"

    def test_project_with_hyphen(self) -> None:
        text, project = extract_project_option("title /p my-project")
        assert text == "title"
        assert project == "my-project"

    def test_project_with_underscore(self) -> None:
        text, project = extract_project_option("title /p my_project")
        assert text == "title"
        assert project == "my_project"


class TestExtractUrl:
    """Verify URL extraction from text."""

    def test_basic_url_extraction(self) -> None:
        remaining, url = extract_url(
            "제목 https://slack.com/archives/C01/p123"
        )
        assert remaining == "제목"
        assert url == "https://slack.com/archives/C01/p123"

    def test_no_url(self) -> None:
        remaining, url = extract_url("just some text")
        assert remaining == "just some text"
        assert url is None

    def test_url_only(self) -> None:
        remaining, url = extract_url("https://example.com")
        assert remaining == ""
        assert url == "https://example.com"

    def test_http_url(self) -> None:
        remaining, url = extract_url("title http://example.com")
        assert remaining == "title"
        assert url == "http://example.com"

    def test_url_in_middle(self) -> None:
        remaining, url = extract_url("before https://example.com after")
        assert remaining == "before  after"
        assert url == "https://example.com"

    def test_empty_string(self) -> None:
        remaining, url = extract_url("")
        assert remaining == ""
        assert url is None

    def test_whitespace_only(self) -> None:
        remaining, url = extract_url("   ")
        assert remaining == ""
        assert url is None

    def test_multiple_urls_extracts_first(self) -> None:
        remaining, url = extract_url(
            "https://first.com https://second.com"
        )
        assert url == "https://first.com"

    def test_slack_angle_bracket_url(self) -> None:
        """Slack wraps URLs in <...> — strip angle brackets."""
        remaining, url = extract_url(
            "제목 <https://slack.com/archives/C01/p123>"
        )
        assert remaining == "제목"
        assert url == "https://slack.com/archives/C01/p123"

    def test_slack_angle_bracket_url_with_trailing_text(self) -> None:
        remaining, url = extract_url(
            "before <https://example.com/path> after"
        )
        assert remaining == "before  after"
        assert url == "https://example.com/path"

    def test_url_with_only_trailing_angle_bracket(self) -> None:
        """URL ending with > but no leading < — still strip >."""
        remaining, url = extract_url(
            "제목 https://slack.com/archives/C01/p123>"
        )
        assert remaining == "제목"
        assert url == "https://slack.com/archives/C01/p123"

    def test_url_with_query_params(self) -> None:
        remaining, url = extract_url(
            "title https://slack.com/path?foo=bar&baz=1"
        )
        assert remaining == "title"
        assert url == "https://slack.com/path?foo=bar&baz=1"


class TestParseSave:
    """Verify parse_save combines extraction correctly."""

    def test_full_save_with_title_url_project(self) -> None:
        title, link, project = parse_save(
            "스프린트 회의록 https://slack.com/archives/C01/p123 /p Backend"
        )
        assert title == "스프린트 회의록"
        assert link == "https://slack.com/archives/C01/p123"
        assert project == "Backend"

    def test_url_and_project_no_title(self) -> None:
        title, link, project = parse_save(
            "https://slack.com/archives/C01/p123 /p Backend"
        )
        assert title is None
        assert link == "https://slack.com/archives/C01/p123"
        assert project == "Backend"

    def test_title_and_url_no_project(self) -> None:
        title, link, project = parse_save(
            "회의록 https://slack.com/archives/C01/p123"
        )
        assert title == "회의록"
        assert link == "https://slack.com/archives/C01/p123"
        assert project is None

    def test_url_only(self) -> None:
        title, link, project = parse_save(
            "https://slack.com/archives/C01/p123"
        )
        assert title is None
        assert link == "https://slack.com/archives/C01/p123"
        assert project is None

    def test_empty_string(self) -> None:
        title, link, project = parse_save("")
        assert title is None
        assert link is None
        assert project is None

    def test_whitespace_only(self) -> None:
        title, link, project = parse_save("   ")
        assert title is None
        assert link is None
        assert project is None

    def test_title_with_spaces_and_url_and_project(self) -> None:
        title, link, project = parse_save(
            "긴 제목 여러 단어 https://slack.com/archives/C01/p123 /p Dev"
        )
        assert title == "긴 제목 여러 단어"
        assert link == "https://slack.com/archives/C01/p123"
        assert project == "Dev"

    def test_project_option_only(self) -> None:
        title, link, project = parse_save(" /p Backend")
        assert title is None
        assert link is None
        assert project == "Backend"
