from abc import ABC, abstractmethod
from utils import Utils
import requests
import sqlite3
import pandas as pd
import json
import yaml


class ExamMarkerBase(ABC):
    """
    Abstract base class for ExamMarker classes

    Subclasses must implement get_solutions() and mark_submission() method

    Attributes:
        solution_url (str): The URL of the solutions JSON file
        solutions (dict): A dictionary mapping question numbers to solutions
        summary (dict): A summary of student's performance
    """

    def __init__(self, solution_url: str):
        self.solution_url = solution_url
        self.solutions = self.get_solutions()
        self.summary = self.initialize_summary()

    def initialize_summary(self) -> dict:
        return {
            'Not submitted': [],
            'Incorrect': [],
            'Partial': [],
            'Correct': [],
            'Issue': [],
        }

    def get_solutions(self) -> dict:
        with open(self.solution_url, 'r') as f:
            return yaml.safe_load(f)

    @abstractmethod
    def mark_submission(self, submission: list):
        pass

    def update_summary(
        self,
        question_number: int,
        correct: bool | None | str,
        issue: str | None = None
    ):
        key = {
            None: 'Not submitted',
            True: 'Correct',
            False: 'Incorrect',
            'Partial': 'Partial'
        }[correct]

        self.summary[key].append(question_number)
        if issue:
            self.summary['Issue'].append((question_number, issue))

    def calculate_score(self, question_number: int):
        for question_range, score in self.QUESTION_SCORES.items():
            if question_number in question_range:
                return score
        return 0

    def calculate_final_score(self) -> float:
        final_score = 0
        for key, value in self.summary.items():
            for question in value:
                score = self.calculate_score(question)
                if key == 'Correct':
                    final_score += score
                elif key == 'Partial':
                    final_score += score / 2
        return final_score

    def display_summary(self, summary: dict):
        print(f"{self.exam_name} - EXAM SUMMARY")

        for key, value in summary.items():
            print(f"{key}: {len(value)}")
            for question in value:
                if key == 'Issue':
                    print(f"  - {question[1]}")
                    continue
                score = (
                    f"{self.calculate_score(question)}/{self.calculate_score(question)}"
                    if key == 'Correct'
                    else f"{self.calculate_score(question)/2:g}/{self.calculate_score(question)}"
                    if key == 'Partial'
                    else f"0/{self.calculate_score(question)}"
                )
                print(f"  - Q{question} ({score})")

        final_score = self.calculate_final_score()
        print(f"FINAL SCORE: {final_score:g}/100")


class M11Marker(ExamMarkerBase):
    QUESTION_SCORES = {
        range(1, 6): 2,
        range(6, 10): 3,
        range(10, 16): 8,
        range(16, 21): 6,
    }

    def __init__(self):
        super().__init__("solutions/M11.yml")
        self.exam_name = "M1.1"
        self.conn = sqlite3.connect("northwind.db")

    def check_submission(self, submission: list, is_sql: bool = False, start_index=1):
        for i, answer in enumerate(submission, start_index):
            solution = self.solutions.get(i)
            correct = None
            issue = None

            if answer:
                if is_sql:
                    correct, issue = Utils.check_sql(
                        answer, solution, i, self.conn)
                else:
                    correct = answer == solution

            self.update_summary(i, correct, issue)

    def mark_submission(self, submission: list) -> dict:
        self.check_submission(submission[:5], is_sql=False, start_index=1)
        self.check_submission(submission[5:], is_sql=True, start_index=6)
        return self.summary


class M12Marker(ExamMarkerBase):
    QUESTION_SCORES = {
        range(1, 6): 5,
        range(6, 7): 10,
        range(7, 8): 5,
        range(8, 10): 10,
        range(10, 13): 5,
        range(13, 15): 10,
        range(15, 16): 5
    }

    def __init__(self):
        super().__init__("solutions/M12.yml")
        self.exam_name = "M1.2"

    def check_submission(self, submission: list, start_index=1):
        for i, answer in enumerate(submission, start_index):
            solution = self.solutions.get(i)
            correct = None

            if answer:
                if isinstance(solution, list):
                    correct = answer in solution
                else:
                    correct = answer == solution

            self.update_summary(i, correct)

    def mark_submission(self, submission) -> dict:
        self.check_submission(submission)
        return self.summary


class M31Marker(ExamMarkerBase):
    QUESTION_SCORES = {
        range(1, 13): 5,
        range(13, 15): 15,
        range(15, 16): 10,
    }

    def __init__(self):
        super().__init__("solutions/M31.yml")
        self.exam_name = "M3.1"
        df = pd.read_csv(
            'https://raw.githubusercontent.com/anhquan0412/dataset/main/Salaries.csv')
        df.drop(columns=['Notes', 'Status', 'Agency'], inplace=True)
        df['JobTitle'] = df['JobTitle'].str.title()
        self.df = df

    def check_submission(self, submission: list, start_index: int, is_expression: bool = False):
        for i, answer in enumerate(submission, start_index):
            solution = self.solutions.get(i)
            correct = None
            issue = None

            if answer:
                if is_expression:
                    global_dict = globals().copy()
                    global_dict['df'] = self.df
                    correct, issue = Utils.check_expression(
                        answer, solution, i, global_dict)
                else:
                    correct = answer == solution

            self.update_summary(i, correct, issue)

    def mark_submission(self, submission: list) -> dict:
        self.check_submission(
            submission[:12], is_expression=False, start_index=1)
        self.check_submission(
            submission[12:], is_expression=True, start_index=13)
        return self.summary


class M21Marker(ExamMarkerBase):
    QUESTION_SCORES = {
        range(1, 9): 4,
        range(9, 13): 12,
        range(13, 15): 10,
    }

    def __init__(self):
        super().__init__("solutions/M21.yml")
        self.exam_name = "M2.1"
        self.test_cases = self.get_test_cases()

    def get_test_cases(self) -> dict:
        with open("solutions/M21_test_cases.json", "r") as f:
            test_cases = json.load(f)
        return test_cases

    def check_submission(self, submission: list, start_index: int, is_function: bool = False):
        for i, answer in enumerate(submission, start_index):
            solution = self.solutions.get(i)
            tests = self.test_cases.get(str(i))
            correct = None
            issue = None

            if answer:
                if is_function:
                    correct, issue = Utils.check_function(
                        answer, solution, globals(), i, tests)
                else:
                    if isinstance(solution, list):
                        answer = answer.split(",")
                        if set(answer) == set(solution):
                            correct = True
                        elif set(answer) & set(solution):
                            correct = 'Partial'
                        else:
                            correct = False
                    else:
                        correct = answer == solution
            self.update_summary(i, correct, issue)

    def mark_submission(self, submission: list) -> dict:
        self.check_submission(
            submission[:8], is_function=False, start_index=1)
        self.check_submission(
            submission[8:], is_function=True, start_index=9)
        return self.summary


# NOTE: Functions for API
def calculate_score(question_number: int, QUESTION_SCORES: dict) -> int:
    for question_range, score in QUESTION_SCORES.items():
        if question_number in question_range:
            return score
    return 0


def calculate_final_score(summary, QUESTION_SCORES: dict) -> float:
    final_score = 0
    for key, value in summary.items():
        for question in value:
            score = calculate_score(question, QUESTION_SCORES)
            if key == 'Correct':
                final_score += score
            elif key == 'Partial':
                final_score += score / 2
    return final_score


def create_summary(exam_name: str, summary: dict, rubrics: dict) -> str:
    result = f"{exam_name} - EXAM SUMMARY\n"

    for key, value in summary.items():
        result += f"{key}: {len(value)}\n"
        for question in value:
            if key == 'Issue':
                result += f"  - {question[1]}\n"
                continue
            score = (
                f"{calculate_score(question, rubrics)}/{calculate_score(question, rubrics)}"
                if key == 'Correct'
                else f"{calculate_score(question, rubrics)/2:g}/{calculate_score(question, rubrics)}"
                if key == 'Partial'
                else f"0/{calculate_score(question, rubrics)}"
            )
            result += f"  - Q{question} ({score})\n"

    final_score = calculate_final_score(summary, rubrics)
    result += f"FINAL SCORE: {final_score:g}/100\n"

    return result


if __name__ == '__main__':
    import requests
    email = "van.nguyen@coderschool.vn"
    response = requests.get(
        f"https://cspyexamclient.up.railway.app/submissions?email={email}&exam=M21")
    submission = response.json()['answers']
    s = [question['answer'] for question in submission]

    marker = M21Marker()
    marker.mark_submission(s)
    marker.display_summary(marker.summary)
