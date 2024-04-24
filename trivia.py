import csv
import random


class Question:
    def __init__(self, question: str, answer: bool):
        self.question = question
        self.answer = answer


class Trivia:
    """
    A class to represent a trivia game
    """
    def __init__(self, file_name: str):
        """
        Initializes a trivia game with questions from a file.
        :param file_name: The name of the file containing the questions.
        """
        self.file_name = file_name
        self.questions = {}

    def load_questions(self):
        """
        Loads the questions from the questions file
        """
        with open(self.file_name, mode='r', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            qid = 0
            for row in csv_reader:
                self.questions[qid] = Question(row[0], row[1] == 'TRUE')
                qid += 1

    def get_question(self) -> Question:
        """
        Gets a random question from the questions list.
        :return: A tuple containing the question ID, the question, and the answer.
        """
        qid = random.choice(list(self.questions.keys()))
        return self.questions.pop(qid)

    def is_empty(self) -> bool:
        """
        Checks if there are no more questions left.
        :return: True if there are no more questions left, False otherwise.
        """
        return len(self.questions) == 0
