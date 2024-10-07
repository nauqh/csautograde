from abc import ABC, abstractmethod
import requests
import sqlite3
from .utils import Utils
import pandas as pd


class ExamMarkerBase(ABC):
    def __init__(self):
        self.solutions = self.get_solutions()
        self.summary = self.initialize_summary()

    def initialize_summary(self):
        return {
            'Not submitted': [],
            'Incorrect': [],
            'Partial': [],
            'Correct': [],
        }

    @abstractmethod
    def get_solutions(self):
        pass

    @abstractmethod
    def mark_submission(self, submission):
        pass

    @abstractmethod
    def display_summary(self, submission):
        pass

    def update_summary(self, question_number, correct):
        if correct is None:
            self.summary['Not submitted'].append(question_number)
        elif correct:
            self.summary['Correct'].append(question_number)
        else:
            self.summary['Incorrect'].append(question_number)

    def calculate_score(self, question_number):
        for question_range, score in self.QUESTION_SCORES.items():
            if question_number in question_range:
                return score
        return 0

    def calculate_final_score(self):
        return sum(self.calculate_score(q) for q in self.summary['Correct'])

    def display_summary(self, summary):
        print(f"{self.exam_name} - EXAM SUMMARY")

        for key, value in summary.items():
            print(f"{key}: {len(value)}")
            for question in value:
                score = (
                    f"{self.calculate_score(question)}/{self.calculate_score(question)}"
                    if key == 'Correct'
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

    def get_solutions(self):
        response = requests.get(
            'https://raw.githubusercontent.com/nauqh/csautograde/refs/heads/master/solutions/M11.json')
        return response.json()

    def check_submission(self, submission, is_sql=False, start_index=1):
        for i, answer in enumerate(submission, start_index):
            solution = self.solutions.get(str(i))
            correct = None

            if answer:
                if is_sql:
                    correct = Utils.check_sql(answer, solution, i, self.conn)
                else:
                    correct = answer == solution

            self.update_summary(i, correct)

    def mark_submission(self, submission):
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

    def get_solutions(self):
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

    def check_submission(self, submission, start_index=1):
        for i, answer in enumerate(submission, start_index):
            solution = self.solutions.get(str(i))
            correct = None

            if answer:
                if isinstance(solution, list):
                    correct = answer in solution
                else:
                    correct = answer == solution

            self.update_summary(i, correct)

    def mark_submission(self, submission):
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

    def get_solutions(self):
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

    def check_submission(self, submission, start_index, is_expression=False):
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

    def mark_submission(self, submission):
        self.check_submission(
            submission[:12], is_expression=False, start_index=1)
        self.check_submission(
            submission[12:], is_expression=True, start_index=13)
        return self.summary


class M21Marker(ExamMarkerBase):
    QUESTION_SCORES = {
        range(1, 7): 4,
        range(7, 13): 12,
        range(13, 15): 10,
    }

    def __init__(self):
        super().__init__()
        self.exam_name = "M2.1"
        self.test_cases = self.get_test_cases()

    def get_solutions(self):
        return {
            "1": "B",
            "2": "B",
            "3": "D",
            "4": ["A", "B"],
            "5": "D",
            "6": ["B", "D"],
            "7": "C",
            "8": "B",
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

    def get_test_cases(self):
        return {
            "9": [
                [
                    [
                        0,
                        1,
                        3,
                        2,
                        8,
                        0,
                        9,
                        10,
                        0,
                        5
                    ]
                ],
                [
                    [
                        -3,
                        0,
                        3,
                        4,
                        2,
                        -1,
                        9,
                        6
                    ]
                ],
                [
                    [
                        -55,
                        4,
                        -87,
                        65,
                        -60,
                        -56,
                        62,
                        83,
                        -50,
                        29,
                        9,
                        39,
                        59,
                        5,
                        70,
                        47,
                        9,
                        3,
                        69,
                        -31
                    ]
                ],
                [
                    [
                        -40,
                        -40,
                        -40,
                        -40,
                        -40,
                        -40,
                        -40,
                        -40,
                        -40,
                        -40,
                        -40,
                        -40,
                        -40,
                        -40,
                        -40
                    ]
                ],
                [
                    [
                        7
                    ]
                ]
            ],
            "10": [
                [
                    [
                        0,
                        1,
                        3,
                        2,
                        8,
                        0,
                        9,
                        10,
                        0,
                        5
                    ]
                ],
                [
                    [
                        -3,
                        0,
                        3,
                        4,
                        2,
                        -1,
                        9,
                        6
                    ]
                ],
                [
                    [
                        -55,
                        4,
                        -87,
                        65,
                        -60,
                        -56,
                        62,
                        83,
                        -50,
                        29,
                        9,
                        39,
                        59,
                        5,
                        70,
                        47,
                        9,
                        3,
                        69,
                        -31
                    ]
                ],
                [
                    [
                        -10,
                        -10,
                        -10,
                        -10,
                        -10,
                        -10
                    ]
                ],
                [
                    [
                        7,
                        3
                    ]
                ]
            ],
            "11": [
                [
                    "chinh.nguyen@coderschool.vn",
                    True
                ],
                [
                    "alexa1234@gmail.com",
                    False
                ],
                [
                    "Joh*_D03+14/12@obviousscam.com",
                    True
                ],
                [
                    "a@z.vn",
                    True
                ],
                [
                    "abigbutt@xxx.com",
                    False
                ],
                [
                    "minh_is_handsome@gmail.com",
                    True
                ],
                [
                    "helpmeTuanH@yahoo.com.vn",
                    False
                ],
                [
                    "keepingmeinhisbasement@hotmail.org.vn",
                    False
                ]
            ],
            "12": [
                [
                    {
                        "unit_weight": 1,
                        "unit_price": 2,
                        "number_of_units": 5
                    },
                    True
                ],
                [
                    {
                        "unit_weight": 1,
                        "unit_price": 2,
                        "number_of_units": 5
                    },
                    False
                ],
                [
                    {
                        "unit_weight": 2.3,
                        "unit_price": 0.4,
                        "number_of_units": 3
                    },
                    True
                ],
                [
                    {
                        "unit_weight": 2.3,
                        "unit_price": 0.4,
                        "number_of_units": 3
                    },
                    False
                ],
                [
                    {
                        "unit_weight": 0.2,
                        "unit_price": 2,
                        "number_of_units": 20
                    },
                    False
                ],
                [
                    {
                        "unit_weight": 0.5,
                        "unit_price": 7,
                        "number_of_units": 2
                    },
                    True
                ],
                [
                    {
                        "unit_weight": 10,
                        "unit_price": 200,
                        "number_of_units": 1
                    },
                    False
                ],
                [
                    {
                        "unit_weight": 0.08,
                        "unit_price": 5,
                        "number_of_units": 4
                    },
                    True
                ]
            ],
            "13": [
                [
                    {
                        "milk": {
                            "unit_weight": 1,
                            "unit_price": 10,
                            "number_of_units": 3
                        },
                        "rice": {
                            "unit_weight": 2,
                            "unit_price": 5,
                            "number_of_units": 4
                        },
                        "cookie": {
                            "unit_weight": 0.2,
                            "unit_price": 2,
                            "number_of_units": 10
                        },
                        "sugar": {
                            "unit_weight": 0.5,
                            "unit_price": 7,
                            "number_of_units": 2
                        }
                    }
                ],
                [
                    {
                        "chair": {
                            "unit_weight": 10,
                            "unit_price": 55,
                            "number_of_units": 4
                        },
                        "desk": {
                            "unit_weight": 64,
                            "unit_price": 144,
                            "number_of_units": 1
                        }
                    }
                ],
                [
                    {
                        "laptop": {
                            "unit_weight": 2.5,
                            "unit_price": 2000,
                            "number_of_units": 1
                        }
                    }
                ],
                [
                    {
                        "lily": {
                            "unit_weight": 0.2,
                            "unit_price": 10,
                            "number_of_units": 20
                        },
                        "tulip": {
                            "unit_weight": 0.22,
                            "unit_price": 12,
                            "number_of_units": 18
                        },
                        "rose": {
                            "unit_weight": 0.3,
                            "unit_price": 15,
                            "number_of_units": 10
                        }
                    }
                ],
                [
                    {
                        "iPhone": {
                            "unit_weight": 1.3,
                            "unit_price": 1500,
                            "number_of_units": 100
                        },
                        "Samsung": {
                            "unit_weight": 1.2,
                            "unit_price": 1440,
                            "number_of_units": 100
                        },
                        "Xiaomi": {
                            "unit_weight": 1.4,
                            "unit_price": 1380,
                            "number_of_units": 100
                        }
                    }
                ]
            ],
            "14": [
                [
                    {
                        "milk": {
                            "unit_weight": 1,
                            "unit_price": 10,
                            "number_of_units": 3
                        },
                        "rice": {
                            "unit_weight": 2,
                            "unit_price": 5,
                            "number_of_units": 4
                        },
                        "cookie": {
                            "unit_weight": 0.2,
                            "unit_price": 2,
                            "number_of_units": 10
                        },
                        "sugar": {
                            "unit_weight": 0.5,
                            "unit_price": 7,
                            "number_of_units": 2
                        }
                    }
                ],
                [
                    {
                        "chair": {
                            "unit_weight": 10,
                            "unit_price": 55,
                            "number_of_units": 4
                        },
                        "desk": {
                            "unit_weight": 64,
                            "unit_price": 144,
                            "number_of_units": 1
                        }
                    }
                ],
                [
                    {
                        "laptop": {
                            "unit_weight": 2.5,
                            "unit_price": 2000,
                            "number_of_units": 1
                        }
                    }
                ],
                [
                    {
                        "lily": {
                            "unit_weight": 0.2,
                            "unit_price": 10,
                            "number_of_units": 20
                        },
                        "tulip": {
                            "unit_weight": 0.22,
                            "unit_price": 12,
                            "number_of_units": 18
                        },
                        "rose": {
                            "unit_weight": 0.3,
                            "unit_price": 15,
                            "number_of_units": 10
                        }
                    }
                ],
                [
                    {
                        "iPhone": {
                            "unit_weight": 1.3,
                            "unit_price": 1500,
                            "number_of_units": 100
                        },
                        "Samsung": {
                            "unit_weight": 1.2,
                            "unit_price": 1440,
                            "number_of_units": 100
                        },
                        "Xiaomi": {
                            "unit_weight": 1.4,
                            "unit_price": 1380,
                            "number_of_units": 100
                        }
                    }
                ]
            ]
        }

    def check_submission(self, submission, start_index, is_function=False):
        for i, answer in enumerate(submission, start_index):
            solution = self.solutions.get(str(i))
            tests = self.test_cases.get(str(i))
            correct = None

            if answer:
                if is_function:
                    correct = Utils.check_function(
                        answer,
                        solution,
                        globals(),
                        i,
                        tests
                    )
                else:
                    correct = answer == solution

            self.update_summary(i, correct)

    def mark_submission(self, submission):
        self.check_submission(
            submission[:8], is_function=True, start_index=1)
        self.check_submission(
            submission[8:], is_function=True, start_index=9)
        return self.summary


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
