from dataclasses import dataclass

from kobokindle.matcher import find_books


@dataclass
class FakeBook:
    Title: str
    Author: str
    RevisionId: str


BOOKS = [
    FakeBook(Title="Guards! Guards!", Author="Terry Pratchett", RevisionId="aaa"),
    FakeBook(Title="Equal Rites", Author="Terry Pratchett", RevisionId="bbb"),
    FakeBook(Title="A Hat Full of Sky", Author="Terry Pratchett", RevisionId="ccc"),
    FakeBook(Title="Carpe Jugulum", Author="Terry Pratchett", RevisionId="ddd"),
    FakeBook(Title="The Guard", Author="Someone Else", RevisionId="eee"),
]


class TestFindBooks:
    def test_exact_substring_match(self):
        results = find_books("Guards! Guards!", BOOKS)
        assert len(results) >= 1
        assert results[0][0].Title == "Guards! Guards!"

    def test_partial_match(self):
        results = find_books("Guards", BOOKS)
        assert len(results) >= 1
        assert results[0][0].Title == "Guards! Guards!"

    def test_case_insensitive(self):
        results = find_books("guards", BOOKS)
        assert len(results) >= 1
        assert results[0][0].Title == "Guards! Guards!"

    def test_no_match_returns_empty(self):
        results = find_books("zzzznotabook", BOOKS)
        assert results == []

    def test_returns_multiple_ranked(self):
        results = find_books("Guard", BOOKS)
        assert len(results) >= 2
        titles = [r[0].Title for r in results]
        assert "Guards! Guards!" in titles

    def test_max_results_limits_output(self):
        results = find_books("t", BOOKS, max_results=2)
        assert len(results) <= 2

    def test_score_is_between_0_and_1(self):
        results = find_books("Guards", BOOKS)
        for _, score in results:
            assert 0.0 <= score <= 1.0
