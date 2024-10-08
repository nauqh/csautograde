from abc import ABC, abstractmethod
import requests
import sqlite3
from .utils import Utils
import pandas as pd
import json


class ExamMarkerBase(ABC):
    """
    Abstract base class for ExamMarker classes

    Subclasses must implement get_solutions() and mark_submission() method

    Attributes:
        solutions (dict): A dictionary mapping question numbers to solutions
        summary (dict): A summary of student's performance
    """

    def __init__(self):
        self.solutions = self.get_solutions()
        self.summary = self.initialize_summary()

    def initialize_summary(self) -> dict:
        return {
            'Not submitted': [],
            'Incorrect': [],
            'Partial': [],
            'Correct': [],
        }

    @abstractmethod
    def get_solutions(self) -> dict:
        pass

    @abstractmethod
    def mark_submission(self, submission: list):
        pass

    def update_summary(self, question_number: int, correct: bool | None | str):
        if correct is None:
            self.summary['Not submitted'].append(question_number)
        elif correct == True:
            self.summary['Correct'].append(question_number)
        elif correct == False:
            self.summary['Incorrect'].append(question_number)
        else:
            self.summary['Partial'].append(question_number)

    def calculate_score(self, question_number: int):
        for question_range, score in self.QUESTION_SCORES.items():
            if question_number in question_range:
                return score
        return 0

    def calculate_final_score(self) -> int:
        final_score = 0
        for key, value in self.summary.items():
            for question in value:
                score = self.calculate_score(question)
                if key == 'Correct':
                    final_score += score
                elif key == 'Partial':
                    final_score += score / 2
        return int(final_score)

    def display_summary(self, summary: dict):
        print(f"{self.exam_name} - EXAM SUMMARY")

        for key, value in summary.items():
            print(f"{key}: {len(value)}")
            for question in value:
                score = (
                    f"{self.calculate_score(question)}/{self.calculate_score(question)}"
                    if key == 'Correct'
                    else f"{int(self.calculate_score(question)/2)}/{self.calculate_score(question)}"
                    if key == 'Partial'
                    else f"0/{self.calculate_score(question)}"
                )
                print(f"  - Q{question} ({score})")

        final_score = self.calculate_final_score()
        print(f"FINAL SCORE: {final_score}/100")


class M11Marker(ExamMarkerBase):
    QUESTION_SCORES = {
        range(1, 6): 2,
        range(6, 10): 3,
        range(10, 16): 8,
        range(16, 21): 6,
    }

    def __init__(self):
        super().__init__()
        self.exam_name = "M1.1"
        self.conn = sqlite3.connect("northwind.db")

    def get_solutions(self) -> dict:
        response = requests.get(
            'https://raw.githubusercontent.com/nauqh/csautograde/refs/heads/master/solutions/M11.json')
        return response.json()

    def check_submission(self, submission: list, is_sql: bool = False, start_index=1):
        for i, answer in enumerate(submission, start_index):
            solution = self.solutions.get(str(i))
            correct = None

            if answer:
                if is_sql:
                    correct = Utils.check_sql(answer, solution, i, self.conn)
                else:
                    correct = answer == solution

            self.update_summary(i, correct)

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
        super().__init__()
        self.exam_name = "M1.2"

    def get_solutions(self) -> dict:
        return {
            "1": "B",
            "2": "B",
            "3": "D",
            "4": ["A", "B"],
            "5": "D",
            "6": ["B", "D"],
            "7": "C",
            "8": "B",
            "9": ["C", "D"],
            "10": "B",
            "11": ["A", "B"],
            "12": ["A", "D"],
            "13": "3",
            "14": "200",
            "15": "B"
        }

    def check_submission(self, submission: list, start_index=1):
        for i, answer in enumerate(submission, start_index):
            solution = self.solutions.get(str(i))
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
        super().__init__()
        self.exam_name = "M3.1"
        df = pd.read_csv(
            'https://raw.githubusercontent.com/anhquan0412/dataset/main/Salaries.csv')
        df.drop(columns=['Notes', 'Status', 'Agency'], inplace=True)
        df['JobTitle'] = df['JobTitle'].str.title()
        self.df = df

    def get_solutions(self) -> dict:
        return {
            "1": "D",
            "2": "A",
            "3": "A",
            "4": "B",
            "5": "B",
            "6": "A",
            "7": "C",
            "8": "A",
            "9": "D",
            "10": "C",
            "11": "C",
            "12": "A",
            "13": "df[df['TotalPay']>df['TotalPay'].mean()]",
            "14": "df['JobTitle'].value_counts().head()",
            "15": """
                # df['JobTitle'].value_counts().head().index
                pd.pivot_table(
                    data=df[df['JobTitle'].isin(df['JobTitle'].value_counts().head().index)],
                    index=['JobTitle'],
                    columns=['Year'],
                    values=['BasePay', 'OvertimePay', 'TotalPay']
                )
                """
        }

    def check_submission(self, submission: list, start_index: int, is_expression: bool = False):
        for i, answer in enumerate(submission, start_index):
            solution = self.solutions.get(str(i))
            correct = None

            if answer:
                if is_expression:
                    global_dict = globals().copy()
                    global_dict['df'] = self.df
                    correct = Utils.check_expression(
                        answer, solution, i, global_dict)
                else:
                    correct = answer == solution

            self.update_summary(i, correct)

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
        super().__init__()
        self.exam_name = "M2.1"
        self.test_cases = self.get_test_cases()

    def get_solutions(self) -> dict:
        return {
            "1": "A",
            "2": "B",
            "3": ["c", "e"],
            "4": "B",
            "5": "E",
            "6": ["A", "C"],
            "7": ["C", "D"],
            "8": "C",
            "9": """
        def count_min(my_list):
            return my_list.count(min(my_list))
    """,
            "10": """
        def calculate_range(my_tup):
            return max(my_tup) - min(my_tup)
    """,
            "11": """
        def extract_email(email, get_username):
            return email.split('@')[0] if get_username else email.split('@')[1]
    """,
            "12": """
        def item_calculator(item, get_weight):
            weight = item['unit_weight'] * item['number_of_units']
            cost   = item['unit_price'] * item['number_of_units']
            return weight if get_weight else cost
    """,
            "13": """
        def heaviest_item(receipt):
            def item_calculator(item, get_weight):
                weight = item['unit_weight'] * item['number_of_units']
                cost   = item['unit_price'] * item['number_of_units']
                return weight if get_weight else cost
            weight_receipt = {item:item_calculator(
                item_info, True) for item, item_info in receipt.items()}
            return max(weight_receipt, key=weight_receipt.get)
    """,
            "14": """
        def priciest_item(receipt):
            def item_calculator(item, get_weight):
                weight = item['unit_weight'] * item['number_of_units']
                cost   = item['unit_price'] * item['number_of_units']
                return weight if get_weight else cost
            price_receipt = {item:item_calculator(
                item_info, False) for item, item_info in receipt.items()}
            return max(price_receipt, key=price_receipt.get)
    """
        }

    def get_test_cases(self) -> dict:
        with open("solutions/M21_test_cases.json", "r") as f:
            test_cases = json.load(f)
        return test_cases

    def check_submission(self, submission: list, start_index: int, is_function: bool = False):
        for i, answer in enumerate(submission, start_index):
            solution = self.solutions.get(str(i))
            tests = self.test_cases.get(str(i))
            correct = None

            if answer:
                if is_function:
                    correct = Utils.check_function(
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
            self.update_summary(i, correct)

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


def calculate_final_score(summary, QUESTION_SCORES: dict) -> int:
    final_score = 0
    for key, value in summary.items():
        for question in value:
            score = calculate_score(question, QUESTION_SCORES)
            if key == 'Correct':
                final_score += score
            elif key == 'Partial':
                final_score += score / 2
    return int(final_score)


def create_summary(exam_name: str, summary: dict, rubrics: dict) -> str:
    result = f"{exam_name} - EXAM SUMMARY\n"

    for key, value in summary.items():
        result += f"{key}: {len(value)}\n"
        for question in value:
            score = (
                f"{calculate_score(question, rubrics)}/{calculate_score(question, rubrics)}"
                if key == 'Correct'
                else f"{int(calculate_score(question, rubrics)/2)}/{calculate_score(question, rubrics)}"
                if key == 'Partial'
                else f"0/{calculate_score(question, rubrics)}"
            )
            result += f"  - Q{question} ({score})\n"

    final_score = calculate_final_score(summary, rubrics)
    result += f"FINAL SCORE: {final_score}/100\n"

    return result


if __name__ == '__main__':
    import requests
    email = "quan.do@coderschool.vn"
    response = requests.get(
        f"https://cspyclient.up.railway.app/submission/{email}")
    submission = response.json()['answers']
    s = [question['answer'] for question in submission]

    marker = M21Marker()
    marker.mark_submission(s)
    marker.display_summary(marker.summary)
