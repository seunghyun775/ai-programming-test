import pytest

from scores import load_scores


def test_valid_rows(tmp_path):
    """정상: 이름과 점수의 공백을 제거하고, 입력 순서를 유지한다."""
    path = tmp_path / "scores.csv"
    path.write_text(
        "name,score\n"
        " 민수 , 85 \n"
        '"김,하늘",92\n',
        encoding="utf-8-sig",
    )

    kept, skipped = load_scores(path)

    assert kept == [("민수", 85), ("김,하늘", 92)]
    assert skipped == []


@pytest.mark.parametrize(
    ("row", "reason"),
    [
        ("민수", "열 개수가 2가 아님"),
        ("민수,80,90", "열 개수가 2가 아님"),
        ("   ,80", "이름이 비어 있음"),
        ("민수,  ", "점수가 비어 있음"),
        ("민수,팔십", "점수가 정수가 아님"),
        ("민수,85.5", "점수가 정수가 아님"),
    ],
)
def test_invalid_row_is_recorded(tmp_path, row, reason):
    """예외 입력: 잘못된 행의 줄 번호, 원본, 사유를 기록한다."""
    path = tmp_path / "scores.csv"
    path.write_text(f"name,score\n{row}\n", encoding="utf-8")

    kept, skipped = load_scores(path)

    assert kept == []
    assert skipped == [(2, row, reason)]


def test_score_boundaries(tmp_path):
    """경계값: 0과 100은 포함하고, 바로 바깥 값인 -1과 101은 제외한다."""
    path = tmp_path / "scores.csv"
    path.write_text(
        "name,score\n"
        "가람,-1\n"
        "나래,0\n"
        "다온,100\n"
        "라온,101\n",
        encoding="utf-8",
    )

    kept, skipped = load_scores(path)

    assert kept == [("나래", 0), ("다온", 100)]
    assert skipped == [
        (2, "가람,-1", "점수가 0~100 밖"),
        (5, "라온,101", "점수가 0~100 밖"),
    ]


def test_blank_line_and_mixed_rows(tmp_path):
    """빈 줄은 기록하지 않고, 잘못된 행 뒤의 정상 행도 계속 읽는다."""
    path = tmp_path / "scores.csv"
    path.write_text(
        "name,score\n"
        "민수,70\n"
        "\n"
        "지우,abc\n"
        "서연,90\n",
        encoding="utf-8",
    )

    kept, skipped = load_scores(path)

    assert kept == [("민수", 70), ("서연", 90)]
    assert skipped == [(4, "지우,abc", "점수가 정수가 아님")]


@pytest.mark.parametrize("content", ["", "name,score\n"])
def test_no_data_rows(tmp_path, content):
    """빈 파일과 헤더만 있는 파일은 모두 빈 목록 두 개를 반환한다."""
    path = tmp_path / "scores.csv"
    path.write_text(content, encoding="utf-8")

    assert load_scores(path) == ([], [])


def test_missing_file(tmp_path):
    """파일 자체가 없으면 FileNotFoundError가 발생한다."""
    with pytest.raises(FileNotFoundError):
        load_scores(tmp_path / "missing.csv")