import os


def validate_csv(filename: str):
    """
    Validate uploaded file type.
    """

    extension = os.path.splitext(filename)[1].lower()

    if extension != ".csv":
        raise ValueError("Only CSV files are allowed.")