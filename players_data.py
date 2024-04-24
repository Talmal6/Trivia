import csv


class Data:
    def __init__(self, player: str, row: list):
        self.player = player
        self.questions = int(row[1])
        self.correct = int(row[2])

    def to_write(self):
        return [self.player, self.questions, self.correct]

    def __str__(self):
        return f'{self.player}: {self.questions} questions, {self.correct} correct'


class PlayersData:
    def __init__(self, file_name: str):
        self.file_name = file_name
        self.data = {}
        self.load_data()

    def get_percentages(self):
        return {p: (self.data[p].correct / self.data[p].questions) * 100 for p in self.data}

    def add_data(self, player: str, is_correct: bool):
        if player in self.data:
            self.data[player].questions += 1
            self.data[player].correct += 1 if is_correct else 0
        else:
            self.data[player] = Data(player, [player, 1, 1 if is_correct else 0])

    def load_data(self):
        try:
            with open(self.file_name, 'r') as file:
                reader = csv.reader(file)
                for row in reader:
                    player = row[0]
                    self.data[player] = Data(player, row)
        except:
            print('Error reading players data file')

    def update_file(self):
        try:
            with open(self.file_name, 'w', newline='') as file:
                writer = csv.writer(file)
                for p in self.data.values():
                    writer.writerow(p.to_write())
        except:
            print('Error writing players data file')


if __name__ == '__main__':
    pd = PlayersData('players_data.csv')
    pd.data['test'] = Data('test', ['test', 1, 1])
    pd.update_file()
