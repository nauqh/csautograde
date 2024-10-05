import pandas as pd
from functools import partial
import pandas as pd
import numpy as np
import textwrap


class Utils():

    # Function to compare numbers or arrays if values are "equal" (or closely equal)
    is_close = partial(np.isclose, atol=1e-6, equal_nan=True)
    DEBUG = True

    @classmethod
    def remove_command_line(cls, block_code):
        return '\n'.join([c for c in block_code.split('\n') if not c.startswith('!')]).strip()

    @classmethod
    def printt(cls, msg):
        if cls.DEBUG:
            print(msg)

    @classmethod
    def is_1darray_equal(
        cls,
        a_val: np.ndarray | pd.Series,
        b_val: np.ndarray | pd.Series
    ) -> bool:
        """
        Check whether two 1D arrays (or Series) are equal (or closely equal).
        Handles numeric and string arrays, and replaces NaNs with 'NAN_VALUE' for strings.
        """
        # Convert pandas Series to numpy array if needed
        a_val = a_val.values if hasattr(a_val, 'values') else a_val
        b_val = b_val.values if hasattr(b_val, 'values') else b_val

        # Handle numeric arrays
        if np.issubdtype(a_val.dtype, np.number) and np.issubdtype(b_val.dtype, np.number):
            return np.all(cls.is_close(a_val, b_val))

        # Handle string arrays
        if a_val.dtype.kind in {'U', 'S', 'O'} and b_val.dtype.kind in {'U', 'S', 'O'}:
            # Replace NaN values in string arrays with 'NAN_VALUE'
            a_val = pd.Series(a_val).fillna('NAN_VALUE').values
            b_val = pd.Series(b_val).fillna('NAN_VALUE').values

        return np.array_equal(a_val, b_val)

    @classmethod
    def is_df_equal(cls, a_val: pd.DataFrame, b_val: pd.DataFrame, **kwargs) -> bool:
        """
        Check whether two DataFrames are equal in terms of values and optionally column names.
        **kwargs:
            - same_col_name (bool): Whether to require identical column names (default: True)
        """
        # Check shape
        if a_val.shape != b_val.shape:
            return False

        # Check column names if required
        same_col_name = kwargs.get('same_col_name', True)
        if same_col_name and not a_val.columns.equals(b_val.columns):
            return False

        # Check each column (1D array) for equality
        for col_a, col_b in zip(a_val.columns, b_val.columns):
            if not cls.is_1darray_equal(a_val[col_a], b_val[col_b]):
                return False

        return True

    @classmethod
    def is_equal(cls, a_val, b_val, **kwargs) -> bool:
        """
        Check whether two values (or data) are closely equal. Handles:
        - int, float
        - list, tuple
        - np.ndarray, pd.Series
        - pd.DataFrame
        """
        if (a_val is None) or (b_val is None):
            return False
        if isinstance(a_val, (int, float)) and isinstance(b_val, (int, float)):
            return cls.is_close(a_val, b_val)
        if isinstance(a_val, (list, tuple)) and isinstance(b_val, (list, tuple)):
            return cls.is_1darray_equal(np.array(a_val), np.array(b_val))
        if isinstance(a_val, (np.ndarray, pd.Series)) and isinstance(b_val, (np.ndarray, pd.Series)):
            return cls.is_1darray_equal(a_val, b_val)
        if isinstance(a_val, pd.DataFrame) and isinstance(b_val, pd.DataFrame):
            return cls.is_df_equal(a_val, b_val, **kwargs)
        if not type(a_val) is type(b_val):
            return False
        return a_val == b_val

    @classmethod
    def check_value(cls, submission, solution):
        try:
            assert cls.is_equal(solution, submission)
            cls.printt('You passed! Good job!')
            return True
        except Exception as e:
            cls.printt('Your solution is not correct, try again')
            return False

    @classmethod
    def check_expression(cls, submission, solution, q_index, global_dict):
        if (not isinstance(submission, str)):
            cls.printt("Your expression answer must be a string")
            return 'INVALID'
        try:
            result = eval(textwrap.dedent(solution), global_dict)
            result_sub = eval(submission, global_dict)
            if cls.is_equal(result, result_sub):
                return True
            return False
        except Exception as e:
            cls.printt(f'Something went wrong for question {q_index}: {e}')
            return False

    @classmethod
    def check_function(cls, submission, solution, global_dict, test_cases=None):
        if not test_cases:
            cls.printt("No test cases input")
            return 'INVALID'

        try:
            score = 0
            exec(submission, global_dict)
            exec(solution, global_dict)
            func_name_sub = submission.split('(')[0][4:]
            func_name_sol = solution.split('(')[0][4:]
            for tc in test_cases:
                result_sub = global_dict[func_name_sub](*tc)
                result_sol = global_dict[func_name_sol](*tc)
                if cls.is_equal(result_sub, result_sol):
                    score += 1
            cls.printt(f'You have passed {score}/{len(test_cases)} test cases')
            return score/len(test_cases)
        except Exception as e:
            cls.printt('Your solution is not correct, try again')
            return 0

    @classmethod
    def check_sql(cls, answer, solution, q_index, connection=None):
        if not connection:
            cls.printt("No database connection input")
            return 'INVALID'

        if (not isinstance(solution, str)):
            cls.printt("Your SQL answer must be a string")
            return 'INVALID'

        try:
            df_sub = pd.read_sql_query(answer, connection)
            df_sol = pd.read_sql_query(solution, connection)
            if cls.is_equal(df_sub, df_sol, same_col_name=False):
                return True
            return False
        except Exception as e:
            cls.printt(f'Something went wrong for question {q_index}: {e}')
            return False

    @classmethod
    def check_available(cls, variables, dict):
        for v in variables:
            if v not in dict:
                print(
                    f'{v} is not defined. Please make sure you have run the code to define it.')
                return False
        return True
