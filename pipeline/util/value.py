class Value:
    def __init__(self, value: str, missing: bool, wrong: bool, correct: bool):
        self.value = value
        self.missing = missing
        self.wrong = wrong
        self.correct = correct
