# 0601 Final ver.

# 爬蟲
from bs4 import BeautifulSoup
import requests
from urllib.request import urlopen

# GUI
import tkinter as tk
from tkinter import ttk
from collections import defaultdict
from tkinter import messagebox
from tkinter import simpledialog
from PIL import Image, ImageTk

# 遊戲與其他相關
import random
import pygame
import time
import sys
import io
import subprocess

hand_size = 7
board_size = 15
played_limit = 100
pass_conti_limit = 5
round = 1
scores = {
    'A': 1, 'B': 3, 'C': 3, 'D': 2, 'E': 1, 'F': 4, 'G': 2, 'H': 4,
    'I': 1, 'J': 8, 'K': 5, 'L': 1, 'M': 3, 'N': 1, 'O': 1, 'P': 3,
    'Q': 10, 'R': 1, 'S': 1, 'T': 1, 'U': 1, 'V': 4, 'W': 4, 'X': 8,
    'Y': 4, 'Z': 10
}

double_cnt = 10
triple_cnt = 5
sec_per_round = 45


def createmessage(message_in):
    tk.messagebox.showinfo("Output", message=message_in)

class Card:
    def __init__(self, alphabet):
        self.alphabet = alphabet

    def __str__(self):
        return self.alphabet


class Deck:
    def __init__(self):
        self.cards = []

    def __str__(self):
        cards = []
        for card in self.cards:
            cards.append(card.__str__())
        return ' '.join(cards)

    def shuffle(self):
        for i in range(len(self.cards)):
            index = random.randrange(len(self.cards))
            temp_card = self.cards[i]
            self.cards[i] = self.cards[index]
            self.cards[index] = temp_card

    def deal_a_card(self):  # 發牌
        return self.cards.pop()

    def get_card_cnt(self):
        return len(self.cards)

    def refresh_the_deck(self):
        letter_frequencies = {
            'E': 12.02, 'T': 9.10, 'A': 8.12, 'O': 7.68, 'I': 7.31, 'N': 6.95, 'S': 6.28, 'R': 6.02,
            'H': 5.92, 'D': 4.32, 'L': 3.98, 'U': 2.88, 'C': 2.71, 'M': 2.61, 'F': 2.30, 'Y': 2.11,
            'W': 2.09, 'G': 2.03, 'P': 1.82, 'B': 1.49, 'V': 0.98, 'K': 0.77, 'X': 0.15, 'Q': 0.10, 'J': 0.10, 'Z': 0.07
        }

        self.cards = []
        for alphabet, frequency in letter_frequencies.items():
            for _ in range(int(frequency * 5)):
                self.cards.append(Card(alphabet))

    def remove_a_given_card(self, alphabet):
        for card in self.cards:
            if card.alphabet == alphabet:
                target_card = card
                return target_card
        raise Exception(f'The card {alphabet} is not in the deck.')

    def add_a_card(self, alphabet):
        self.cards.append(Card(alphabet))

    def return_card(self, tmp_list):  # 移除此回合出的牌並回到手牌中
        # tmp_list = [[alphabet, row, col], [alphabet, row, col], ...]
        # 只留下非空的sublist
        tmp_list = [x for x in tmp_list if x]
        for i in range(0, len(tmp_list)):
            self.add_a_card(tmp_list[i][0])


class Board:
    REGULAR_CELL = 1
    DOUBLE_WORD_CELL = 2
    TRIPLE_WORD_CELL = 3

    def __init__(self):
        self.board = []
        for i in range(board_size):
            self.board.append([' '] * board_size)
        self.cell_multipliers = [[0 for _ in range(board_size)] for _ in range(board_size)]
        self.initialize_special_cells()

    def __str__(self):
        board_str = "   " + " ".join(f"{i:02}" for i in range(board_size)) + "\n"
        for row in range(board_size):
            board_str += f"{row:02}"
            for col in range(board_size):
                cell = self.board[row][col]
                board_str += "  " + cell
            board_str += "\n"
        return board_str

    def placeCard(self, card, row, col):
        self.board[row][col] = card.__str__()

    def removeCard(self, row, col):
        self.board[row][col] = ' '

    def find_row_start(self, tmp_list):  # 在固定row上找尋開始column
        if len(tmp_list) == 1:
            row = tmp_list[0][1]
            start = tmp_list[0][2]
        else:
            sorted_list = sorted(tmp_list, key=lambda x: (x[1], x[2]))
            row = sorted_list[0][1]
            start = sorted_list[0][2]
        while start > 0 and self.board[row][start - 1] != ' ':
            start -= 1
        return row, start

    def find_col_start(self, tmp_list):  # 固定column找尋row
        if len(tmp_list) == 1:
            col = tmp_list[0][2]
            start = tmp_list[0][1]
        else:
            sorted_list = sorted(tmp_list, key=lambda x: (x[2], x[1]))
            col = sorted_list[0][2]
            start = sorted_list[0][1]
        while start > 0 and self.board[start - 1][col] != ' ':
            start -= 1
        return col, start

    def checkRowWord(self, row, start):
        row_word = ''
        for i in range(start, board_size):
            row_word += self.board[row][i]
            if self.board[row][i] == ' ':
                break
        return row_word

    def checkColWord(self, col, start):
        col_word = ''
        for i in range(start, board_size):
            col_word += self.board[i][col]
            if self.board[i][col] == ' ':
                break
        return col_word

    def reset_round(self, tmp_list):  # 清空當回合出牌的格子
        tmp_list = [x for x in tmp_list if x]
        for i in range(len(tmp_list)):
            self.board[tmp_list[i][1]][tmp_list[i][2]] = ' '

    def initialize_special_cells(self):
        # 在棋盤上隨機分布 double_cnt 個雙倍格子和 triple_cnt 個三倍格子
        double_word_cells = random.sample(range(board_size * board_size), double_cnt)
        triple_word_cells = random.sample(range(board_size * board_size), triple_cnt)

        for i in range(board_size):
            for j in range(board_size):
                index = i * board_size + j
                if index in double_word_cells:
                    self.cell_multipliers[i][j] = self.DOUBLE_WORD_CELL
                elif index in triple_word_cells:
                    self.cell_multipliers[i][j] = self.TRIPLE_WORD_CELL
                else:
                    self.cell_multipliers[i][j] = self.REGULAR_CELL

    def get_cell_multiplier(self, row, col):
        return self.cell_multipliers[row][col]

    def calculate_word_score(self, word, tmp_list):
        base_score = sum(scores[letter.upper()] for letter in word)
        word_multiplier = 1

        # 檢查這一回合放置的字母所落在的加倍格子類型
        for alphabet, row, col in tmp_list:
            cell_multiplier = self.get_cell_multiplier(row, col)
            if cell_multiplier == self.DOUBLE_WORD_CELL:
                word_multiplier *= 2
            elif cell_multiplier == self.TRIPLE_WORD_CELL:
                word_multiplier *= 3

        return base_score * word_multiplier


class Player:
    def __init__(self, name):
        self.name = name
        self.hand = Deck()
        self.score = 0
        self.played_cnt = 0
        self.game = None

    def __str__(self):
        return f'{self.name}: {self.hand.__str__()}'

    def draw_a_card(self, deck):  # 抽牌
        if deck.get_card_cnt() == 0:
            deck.refresh_the_deck()
            deck.shuffle()
        self.hand.cards.append(deck.deal_a_card())

    def refill(self, deck):
        if self.hand.get_card_cnt() < hand_size:
            refill_cnt = hand_size - self.hand.get_card_cnt()
            for i in range(refill_cnt):
                self.draw_a_card(deck)

    def play_a_card(self, alphabet, row, col, board):
        if alphabet in self.hand.__str__() and board.board[row][col] == ' ':
            # 檢查是否有相鄰的字母
            if not self.has_adjacent_letter(row, col, board):
                print(f'{self.name}, you can only place a card adjacent to an existing letter on the board.')
                return False

            card = self.hand.remove_a_given_card(alphabet)
            board.placeCard(card, row, col)
            self.hand.cards.remove(card)
            return True  # 返回 True 表示成功放置牌
        elif alphabet in self.hand.__str__() and board.board[row][col] != ' ':
            print(f'{self.name}, the position ({row}, {col}) is already occupied.')
        else:
            print(f'{self.name},You do not have the card {alphabet} in hand.')
        return False

    def has_adjacent_letter(self, row, col, board):
        # 檢查上下左右四個位置是否有字母
        if row > 0 and board.board[row - 1][col] != ' ':
            return True
        if row < board_size - 1 and board.board[row + 1][col] != ' ':
            return True
        if col > 0 and board.board[row][col - 1] != ' ':
            return True
        if col < board_size - 1 and board.board[row][col + 1] != ' ':
            return True
        return False

class Dictionary:
    @staticmethod
    def part_of_speach(soup):
        pos = soup.find('span', class_='pos').text
        return pos

    def check_definition(soup):
        types = soup.find('ol', class_='senses_multiple')
        senses = types.find_all('li', class_='sense')  # 多個definition
        def_order = 1
        mes = []
        for s in senses:
            definition = s.find('span', class_='def').text
            mes.append(str(def_order) + ': ' + str(definition) + '\n')
            def_order += 1
        return mes

    def simple_definition(soup):
        senses = soup.find_all('li', class_='sense')  # 單個definition
        def_order = 1
        mes = []
        for s in senses:
            definition = s.find('span', class_='def').text
            mes.append(str(def_order) + ': ' + str(definition) + '\n')
            def_order += 1
        return mes

    def isValidWord(word):
        scrape_url = 'https://www.oxfordlearnersdictionaries.com/definition/english/' + word.lower()

        headers = {"User-Agent": ""}
        web_response = requests.get(scrape_url, headers=headers)

        soup = BeautifulSoup(web_response.content, 'html.parser')

        try:  # 當此字不存在於字典裡時，會多一個div class= 'results'之項目
            result = soup.find('div', class_='results').text
            mes = str('')
            mes += "\n"
            mes = mes + f'{word} is invalid! Please try another word' + '\n'
            mes += "\n"
            createmessage(message_in=mes)
            return False
        except AttributeError:  # 此字存在於字典中
            try:
                mes = str('')
                mes += "\n"
                mes = mes + f"Word available! Here's the definition of {word}" + '\n'
                mes += "\n"
                mes += word.upper() + ' (' + str(Dictionary.part_of_speach(soup)) + ')' + '\n'
                a = Dictionary.check_definition(soup)  # 把check_definition回傳的字串裝起來
                mes += ' '.join(a) + "\n"
                createmessage(message_in=mes)
            except AttributeError:  # 若該單字只有一個意思時，Oxford字典的程式編排不同
                try:
                    mes = str('')
                    mes += f"Word available! Here's the definition of {word}" + '\n'
                    a = Dictionary.simple_definition(soup)
                    mes += ' '.join(a)
                    createmessage(message_in=mes)
                except:
                    mes = str('')
                    mes += "\n"
                    mes += f'{word} is invalid! Please try another word' + '\n'
                    mes += "\n"
                    createmessage(message_in=mes)
                    return False

class Scrabble:
    def __init__(self):
        self.deck = Deck()
        self.deck.refresh_the_deck()
        self.deck.shuffle()
        self.board = Board()
        self.players = []
        self.consecutive_passes = 0
        self.round = 1

    def add_player(self, player):
        self.players.append(player)

    def submit_word(self, player, tmp_list, cards_played, word_list):
        initial_score = player.score
        if cards_played == 0:
            # 處理沒有放置字母的情況
            print('Please play at least one card.')
            return cards_played, tmp_list, word_list, initial_score

        elif cards_played == 1:
            tmp_list = tmp_list[:cards_played]
            row, startr = self.board.find_row_start(tmp_list)
            col, startc = self.board.find_col_start(tmp_list)
            wordr = self.board.checkRowWord(row, startr).strip()
            wordc = self.board.checkColWord(col, startc).strip()
            self.consecutive_passes = 0

            if len(wordr) > 1 and len(wordc) > 1:
                if Dictionary.isValidWord(wordr) == False or Dictionary.isValidWord(wordc) == False:
                    cards_played = 0
                    word_list = []
                    return cards_played, tmp_list, word_list, initial_score
                else:
                    word_list.append(wordr)
                    word_list.append(wordc)

            elif len(wordr) == 1:
                if Dictionary.isValidWord(wordc) == False:
                    cards_played = 0
                    word_list = []
                    return cards_played, tmp_list, word_list, initial_score
                else:
                    word_list.append(wordc)

            elif len(wordc) == 1:
                if Dictionary.isValidWord(wordr) == False:
                    cards_played = 0
                    word_list = []
                    return cards_played, tmp_list, word_list, initial_score
                else:
                    word_list.append(wordr)

            # 計算每個單詞的分數
            for word in word_list:
                score = self.board.calculate_word_score(word, tmp_list)
                player.score += score
                player.played_cnt += len(word)
                print(f"{player.name}, Score for playing '{word}': {score}")
                print(f"{player.name}, Total score: {player.score}")
                self.round += 0.5

            return cards_played, tmp_list, word_list, initial_score

        else:
            self.consecutive_passes = 0
            tmp_list = tmp_list[:cards_played]
            all_same_row = True
            all_same_col = True
            for i in range(0, len(tmp_list) - 1):
                if tmp_list[i][1] != tmp_list[i + 1][1]:
                    all_same_row = False
                if tmp_list[i][2] != tmp_list[i + 1][2]:
                    all_same_col = False

            if all_same_row == False and all_same_col == False:
                print("Please make sure all of your letters are in the same row or column")
                player.hand.return_card(tmp_list)
                self.board.reset_round(tmp_list)
                cards_played = 0
                word_list = []
                return cards_played, tmp_list, word_list, initial_score

            elif all_same_row == True:
                row, startr = self.board.find_row_start(tmp_list)
                word = self.board.checkRowWord(row, startr).strip()

                if Dictionary.isValidWord(word) == False:
                    cards_played = 0
                    word_list = []
                    return cards_played, tmp_list, word_list, initial_score
                else:
                    word_list.append(word)
                    for i in range(len(tmp_list)):
                        db_check_list = []
                        db_check_list.append(tmp_list[i])
                        col, startc = self.board.find_col_start(db_check_list)
                        word = self.board.checkColWord(col, startc).strip()
                        if len(word) != 1:
                            if Dictionary.isValidWord(word) == False:
                                print("One or more of your word combinations are invalid!")
                                print()
                                cards_played = 0
                                word_list = []
                                return cards_played, tmp_list, word_list, initial_score
                            else:
                                word_list.append(word)

            elif all_same_col == True:
                col, startc = self.board.find_col_start(tmp_list)
                word = self.board.checkColWord(col, startc).strip()

                if Dictionary.isValidWord(word) == False:
                    cards_played = 0
                    word_list = []
                    return cards_played, tmp_list, word_list, initial_score
                else:
                    word_list.append(word)
                    for i in range(len(tmp_list)):
                        db_check_list = []
                        db_check_list.append(tmp_list[i])
                        row, startr = self.board.find_row_start(db_check_list)
                        word = self.board.checkRowWord(row, startr).strip()
                        if len(word) != 1:
                            if Dictionary.isValidWord(word) == False:
                                print("One or more of your word combinations are invalid!")
                                print()
                                cards_played = 0
                                word_list = []
                                return cards_played, tmp_list, word_list, initial_score
                            else:
                                word_list.append(word)

            # 計算每個單詞的分數
            for word in word_list:
                score = self.board.calculate_word_score(word, tmp_list)
                player.score += score
                player.played_cnt += len(word)
                print(f"{player.name}, Score for playing '{word}': {score}")
                print(f"{player.name}, Total score: {player.score}")
                self.round += 0.5
                # 檢查玩家是否達到 50 分或以上
                if player.score >= 50:
                    self.end_game(f"{player.name} has reached 50 points or more!")
                    break
            return cards_played, tmp_list, word_list, initial_score

    def undo_play(self, player, tmp_list, cards_played):
        if cards_played == 0:
            print('You do not have any card to remove.')
            return cards_played, tmp_list, 0
        else:
            player.hand.add_a_card(tmp_list[cards_played - 1][0])
            self.board.removeCard(tmp_list[cards_played - 1][1], tmp_list[cards_played - 1][2])
            tmp_list[cards_played - 1] = []
            cards_played -= 1
            print(self.board)
            return cards_played, tmp_list, 1

    def pass_turn(self, player, cards_played, tmp_list):
        if cards_played == 0:
            print(f'{player.name} skipped his/her turn!')
            print(self.board)
            self.consecutive_passes += 1
            self.round += 0.5
            if self.consecutive_passes == pass_conti_limit:
                self.end_game()  # 連續pass達到5次,遊戲結束
            return cards_played, tmp_list
        else:
            player.hand.return_card(tmp_list)
            self.board.reset_round(tmp_list)
            print(f'{player.name} skipped his/her turn!')
            print(self.board)
            self.consecutive_passes = 0  # 有玩家出牌，重置連續pass次數
            self.round += 0.5
            return 0, [[] for i in range(hand_size)]

    def end_game(self, message=None):
        max_score = max(player.score for player in self.players)
        winners = [player for player in self.players if player.score == max_score]

        if len(winners) == 1:
            winner_name = winners[0].name
            if message:
                print(message)
                tk.messagebox.showinfo("Game Over", message)
            else:
                print(f'Game Over! The winner is {winner_name} with a score of {max_score}!')
                tk.messagebox.showinfo("Game Over", f"The winner is {winner_name} with a score of {max_score}!")
        else:
            winner_names = [winner.name for winner in winners]
            winner_names_str = " and ".join(winner_names)
            print(f'Game Over! It\'s a tie with a score of {max_score}!')
            tk.messagebox.showinfo("Game Over", f"It's a tie between {winner_names_str} with a score of {max_score}!")
        
        # 禁用所有按鈕,只留下restart可以被玩家按
        self.gui.start_button.config(state='disabled')
        self.gui.pass_button.config(state='disabled')
        self.gui.submit_button.config(state='disabled')
        self.gui.undo_button.config(state='disabled')
        self.gui.swap_button.config(state='disabled')  # 禁用 swap_button
        self.gui.restart_button.config(state='normal')

        # 自動重置遊戲
        self.reset_game()

    def get_round(self):
        return self.round
    
    def reset_game(self):
        self.deck = Deck()
        self.deck.refresh_the_deck()
        self.deck.shuffle()
        self.board = Board()
        self.consecutive_passes = 0

        for player in self.players:
            player.hand = Deck()
            player.score = 0
            player.played_cnt = 0


class ScrabbleGUI:
    def __init__(self, master):
        self.master = master
        master.title("Scrabble Game")
        pygame.mixer.init()
        pygame.mixer.music.load("music.mp3")
        pygame.mixer.music.play(-1)

        window_width = 1280
        window_height = 1280
        screen_width = master.winfo_screenwidth()
        screen_height = master.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2) - 30

        master.geometry(f"{window_width}x{window_height}+{x}+{y}")
        master.resizable(1, 1)

        self.canvas = tk.Canvas(master)
        self.scrollbar_y = ttk.Scrollbar(master, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollbar_x = ttk.Scrollbar(master, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.scrollbar_y.set, xscrollcommand=self.scrollbar_x.set)

        self.main_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.main_frame, anchor='nw')

        self.game = Scrabble()
        self.game.gui = self  # 將 ScrabbleGUI 實例指定給 Scrabble 的 gui 屬性
        player1 = Player('Player 1')
        player2 = Player('Player 2')
        self.game.add_player(player1)
        self.game.add_player(player2)
        self.turn_label = None
        self.create_turn_label()
        self.player_turn = 0
        self.cards_played = 0
        self.tmp_list = [[] for _ in range(hand_size)]
        self.word_list = []
        self.selected_card = None
        self.vocabulary_list = []
        self.round = 1

        tip_frame = ttk.Frame(self.main_frame, padding=5)
        tip_frame.grid(row=3, column=0, columnspan=2, sticky='nwes')
        self.tip_label = ttk.Label(tip_frame, text="", font=('Segoe UI', 12), foreground='orange', background='white')
        self.tip_label.pack()

        self.volume_frame = ttk.LabelFrame(self.main_frame, padding=5, text='Volume')
        self.volume_frame.grid(row=3, column=1, columnspan=2, sticky='nwes')
        volume_slider = ttk.Scale(self.volume_frame, from_=0, to=1,orient='horizontal', value=1, command=self.volume, length=125)
        volume_slider.grid(row=0, column=0, sticky='N')
        volume_value = ttk.Label(self.volume_frame, text='100%', font=('Segoe UI', 12), foreground='black', background = '#d9d9d9')
        volume_value.grid(row=0, column=1, sticky='N', pady=0)
        self.vocabulary_labels = []

        style = ttk.Style()
        style.theme_use('alt')
        style.configure('TLabel', font=('Segoe UI', 12), foreground='royalblue', background='white', padding=6, anchor='center')
        style.configure('TButton', font=('Segoe UI', 12), foreground='Black')
        style.configure('TFrame', background='lightgray')

        style.map('TButton', foreground=[('active', 'royalblue'), ('disabled', 'gray')],
                background=[('active', 'powderblue'), ('disabled', 'lightgray')])

        self.create_board_labels()
        self.create_hand_labels()
        self.create_score_labels()
        self.create_control_buttons()
        self.create_vocabulary_labels()
        self.create_round_label()

        self.main_frame.bind('<Configure>', self.on_frame_configure)

        self.canvas.grid(row=0, column=0, sticky='nsew')
        self.scrollbar_y.grid(row=0, column=1, sticky='ns')
        self.scrollbar_x.grid(row=1, column=0, sticky='ew')

        master.grid_rowconfigure(0, weight=1)
        master.grid_columnconfigure(0, weight=1)

        self.volume_value = ttk.Label(self.volume_frame, text='100%', font=('Segoe UI', 12), foreground='black', background='#d9d9d9')
        self.volume_value.grid(row=0, column=1, sticky='N', pady=0)

        self.timer_label = ttk.Label(self.round_frame, font=('Segoe UI', 16), foreground='Black', background='lightgray')
        self.timer_label.grid(row=0, column=0, padx=(0, 5))
        self.timer = Timer(master, self.timer_label, sec_per_round, self.on_timeout)
        self.has_swapped = False



    def on_timeout(self):
        player = self.game.players[self.player_turn]
        createmessage(f"Time is up for {player.name}!")
        self.switch_turn()
        self.update_round_label()

    def start_timer(self):
        self.timer.reset()
        self.timer.start()

    def volume(self, value):
        volume = float(value)
        pygame.mixer.music.set_volume(volume)
        self.volume_value.config(text=f"{int(volume * 100)}%")

    def __del__(self):
        if pygame.mixer.get_init() is not None:
            pygame.mixer.music.stop()
            pygame.mixer.quit()

    def on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def create_round_label(self):
        # 創建最上方Frame區
        self.round_frame = ttk.Frame(self.main_frame, padding=10, relief='ridge')
        self.round_frame.grid(row=0, column=0, sticky='nsew')
        
        # 創建倒計時標籤
        self.timer_label = ttk.Label(self.round_frame, text="", font=('Segoe UI', 16), foreground='Black', background='lightgray')
        self.timer_label.grid(row=0, column=0, padx=(0, 5))

        #創建回合數Label
        self.round_label = ttk.Label(self.round_frame, text="R O U N D  1", font=('Segoe UI', 16, 'bold'), background='lightgray', foreground='Black')
        self.round_label.place(relx=0.5, rely=0.5, anchor='center')

    def update_round_label(self):
        self.round_label.config(text=f'R O U N D  {str(int(self.round//1))}')

    def create_turn_label(self):
        turn_frame = ttk.Frame(self.main_frame, padding=10, relief='ridge')
        turn_frame.grid(row=0, column=1, columnspan=2, sticky='nwes')
        self.turn_label = ttk.Label(turn_frame, text="", font=('Segoe UI',14), background='lightgray')
        self.turn_label.pack()

    def update_turn_label(self):
        current_player = self.game.players[self.player_turn]
        self.turn_label.config(text=f"{current_player.name}'s turn")

    def create_board_labels(self):
        if hasattr(self, 'board_frame'):
            self.board_frame.destroy()

        self.board_frame = ttk.Frame(self.main_frame, padding=10, relief='raised')
        self.board_frame.grid(row=1, column=0, sticky='nsew')
        self.board_labels = defaultdict(dict)
        for row in range(board_size):
            for col in range(board_size):
                cell_multiplier = self.game.board.get_cell_multiplier(row, col)
                if cell_multiplier == self.game.board.REGULAR_CELL:
                    label_bg = 'white'
                elif cell_multiplier == self.game.board.DOUBLE_WORD_CELL:
                    label_bg = 'lightgreen'
                elif cell_multiplier == self.game.board.TRIPLE_WORD_CELL:
                    label_bg = 'lightblue'
                label = ttk.Label(self.board_frame, text=self.game.board.board[row][col], relief='sunken', width=2, background=label_bg)
                label.grid(row=row, column=col, sticky='nwes')
                label.bind('<Button-1>', lambda event, r=row, c=col: self.play_card(r, c))
                self.board_labels[row][col] = label

    def create_hand_labels(self):
        if hasattr(self, 'hand_frame'):
            self.hand_frame.destroy()

        self.hand_frame = ttk.LabelFrame(self.main_frame, text='Your Hand', padding=6, relief='raised')
        self.hand_frame.grid(row=2, column=0, sticky='nsew', padx=2, pady=2)
        self.hand_labels = []
        for i in range(hand_size):
            label = ttk.Label(self.hand_frame, text='', relief='raised', width=2)
            label.grid(row=0, column=i, padx=2, pady=2)
            label.bind('<Button-1>', lambda event, index=i: self.select_card(index))
            self.hand_labels.append(label)
        
    def create_score_labels(self):
        score_frame = ttk.LabelFrame(self.main_frame, text='Scores', padding=5, relief='raised')
        score_frame.grid(row=1, column=1, sticky='nsew', padx=2, pady=2)  # 設置 sticky 屬性
        self.score_labels = []
        for i, player in enumerate(self.game.players):
            label = ttk.Label(score_frame, text=f'{player.name}: 0')
            label.grid(row=i, column=0, sticky='w')
            self.score_labels.append(label)

    def create_control_buttons(self):
        control_frame = ttk.Frame(self.main_frame, padding=5)
        control_frame.grid(row=2, column=1, sticky='nsew')  # 設置 sticky 屬性
        self.start_button = ttk.Button(control_frame, text='Start', command=self.start_game)
        self.start_button.pack(pady=2)
        self.restart_button = ttk.Button(control_frame, text='Restart', command=self.restart_game, state='disabled')
        self.restart_button.pack(pady=2)
        self.pass_button = ttk.Button(control_frame, text='Pass', command=self.pass_turn, state='disabled')
        self.pass_button.pack(pady=2)
        self.submit_button = ttk.Button(control_frame, text='Submit', command=self.submit_word, state='disabled')
        self.submit_button.pack(pady=2)
        self.undo_button = ttk.Button(control_frame, text='Undo', command=self.undo_play, state='disabled')
        self.undo_button.pack(pady=2)
        self.swap_button = ttk.Button(control_frame, text='Swap', command=self.swap_cards, state='disabled')
        self.swap_button.pack(pady=2)

    def set_layout_weights(self):
        self.master.rowconfigure(0, weight=1)
        self.master.rowconfigure(1, weight=1)
        self.master.columnconfigure(0, weight=1)
        self.master.columnconfigure(1, weight=1)

    def Name_Input_Window(self):

        names = ['Bob', 'Alice', 'Tim', 'Kyle', 'Nannie', 'Ruby', 'Aaliyah', 'Elena', 'Sean', 'Johnny', 'Jean', 'Nismo',
                 'Jason', 'LeBron', 'Jamal', 'Kaylee', 'Trump', '徐芷嫄', '憤怒金針菇', 'Jordan', '北投大火鍋',
                 '可莉玩家','卡卡羅', 'Karon', 'Mike', 'Will', 'James', '小波波', '日月大賢者', '公館劉德華']

        namewindow = tk.Toplevel()
        namewindow.title("ENTER PLAYER NAMES")

        # 使輸入玩家姓名頁面生成時可以置中
        window_width = 500
        window_height = 200
        screen_width = namewindow.winfo_screenwidth()
        screen_height = namewindow.winfo_screenheight()
        namewindow.resizable(0, 0)
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2) - 30
        namewindow.geometry(f"{window_width}x{window_height}+{x}+{y}")

        
        l2 = tk.Label(namewindow, text="Player 1: ", font=('Segoe UI', 14))
        l3 = tk.Label(namewindow, text="Player 2: ", font=('Segoe UI', 14))
        emptyl = tk.Label(namewindow)
        footnote = tk.Label(namewindow, text="Click R to use a randomly generated name", font=('Segoe UI', 12))

        l2.grid(row=1, column=0, padx=20, pady=5)
        l3.grid(row=2, column=0, padx=20, pady=5)
        footnote.grid(row=3, column=1)
        emptyl.grid(row=4, column=1, columnspan=300)

        p1id = tk.StringVar()
        p2id = tk.StringVar()
        p1 = tk.Entry(namewindow, textvariable=p1id, font=('Segoe UI', 14))
        p2 = tk.Entry(namewindow, textvariable=p2id, font=('Segoe UI', 14))
        p1.grid(row=1, column=1, columnspan=1)
        p2.grid(row=2, column=1, columnspan=1)

        def submit():
            if p1id.get().isspace() == True or len(p1id.get()) == 0 or p2id.get().isspace() == True or len(
                    p2id.get()) == 0:
                emptyl.config(text="Player name cannot be blank!", font=('Segoe UI', 14), fg='red')
            elif p1id.get() == p2id.get():
                emptyl.config(text="Player names cannot be the same!", font=('Segoe UI', 14), fg='red')
            else:
                player1 = p1id.get()
                player2 = p2id.get()
                player_count = 1
                for player in self.game.players:
                    if player_count == 1:
                        player.name = player1
                    else:
                        player.name = player2
                    player_count += 1

                for player in self.game.players:
                    player.refill(self.game.deck)

                 # 在棋盤正中間放置一個隨機字母
                center_row = board_size // 2
                center_col = board_size // 2
                random_letter = random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
                self.game.board.placeCard(Card(random_letter), center_row, center_col)

                # 一系列更新ＧUI玩家名稱的動作
                self.update_scores()
                self.update_hands()
                self.update_board()
                self.update_turn_label()
                namewindow.destroy()
                # 啟動計時器
                self.timer.start()

        def cancel():
            namewindow.destroy()
            self.restart_game()

        def random_name1():
            random_num = random.randint(0, len(names) - 1)
            p1id.set(names[random_num])

        def random_name2():
            random_num = random.randint(0, len(names) - 1)
            p2id.set(names[random_num])

        b1 = ttk.Button(namewindow, text="Submit", command=submit, style='custom.TButton')
        b2 = ttk.Button(namewindow, text="Cancel", command=cancel)
        b3 = ttk.Button(namewindow, command=random_name1, text="R", width=4)
        b4 = ttk.Button(namewindow, text="R", command=random_name2, width=4)

        b1.grid(row=5, column=1, sticky=tk.E)
        b2.grid(row=5, column=1, sticky=tk.W)
        b3.grid(row=1, column=2, sticky=tk.W)
        b4.grid(row=2, column=2, sticky=tk.W)

    def welcome_page(self):
        win = tk.Toplevel()

        rule1 = Image.open('rule1.png').resize((600,550))
        rule1tk = ImageTk.PhotoImage(rule1)
        rule2 = Image.open('rule2.png').resize((600,550))
        rule2tk = ImageTk.PhotoImage(rule2)

        self.pic_frame = ttk.Frame(win)
        self.pic_frame.grid(row=0, column=0)

        self.button_frame = ttk.Frame(win, padding=3)
        self.button_frame.grid(row=1, column=0)

        win.title("How to Play")
        window_width = 600
        window_height = 600
        screen_width = win.winfo_screenwidth()
        screen_height = win.winfo_screenheight()
        win.resizable(0, 0)
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2) - 30
        win.geometry(f"{window_width}x{window_height}+{x}+{y}")
        win.config(background='lightgray')
        win.resizable(0,0)

        def tab1():
            def tab2():
                def confirm():
                    win.destroy()
                    self.select_difficulty()

                l1.destroy()
                b1_2.config(state='normal')
                b1.config(text='Confirm', command=confirm)  # 修改這行代碼

                l2 = tk.Label(self.pic_frame, image=rule2tk)
                l2.grid(row=0, column=0)

                def back():
                    l2.destroy()
                    b2.destroy()
                    tab1()

                b2 = ttk.Button(self.button_frame, text='Back', command=back)
                b2.grid(row=0, column=0)

            l1 = tk.Label(self.pic_frame, image=rule1tk)
            l1.grid(row=0, column=0)

            b1 = ttk.Button(self.button_frame, text='Next', command=tab2)
            b1_2 = ttk.Button(self.button_frame, text='Back', state='disabled')
            b1.grid(row=0, column=1)
            b1_2.grid(row=0, column=0)
        tab1()

    def select_difficulty(self):
        difficulty_window = tk.Toplevel()
        difficulty_window.title("Select Difficulty")

        window_width = 200
        window_height = 180
        screen_width = difficulty_window.winfo_screenwidth()
        screen_height = difficulty_window.winfo_screenheight()
        difficulty_window.resizable(0, 0)
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2) - 30
        difficulty_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

        difficulty_frame = ttk.Frame(difficulty_window, padding=20)
        difficulty_frame.grid(row=0, column=0)

        easy_button = ttk.Button(difficulty_frame, text="Easy", command=lambda: self.set_difficulty("easy", difficulty_window))
        easy_button.grid(row=0, column=0, padx=10, pady=10)

        medium_button = ttk.Button(difficulty_frame, text="Medium", command=lambda: self.set_difficulty("medium", difficulty_window))
        medium_button.grid(row=1, column=0, padx=10, pady=10)

        hard_button = ttk.Button(difficulty_frame, text="Hard", command=lambda: self.set_difficulty("hard", difficulty_window))
        hard_button.grid(row=2, column=0, padx=10, pady=10)

    def set_difficulty(self, difficulty, window):
        global board_size, hand_size, sec_per_round

        if difficulty == "easy":
            board_size = 11
            hand_size = 9
            sec_per_round = 80
        elif difficulty == "medium":
            board_size = 13
            hand_size = 7
            sec_per_round = 60
        elif difficulty == "hard":
            board_size = 15
            hand_size = 5
            sec_per_round = 45

        self.game.board = Board()  # 創建新的棋盤物件
        self.timer.duration = sec_per_round  # 設置新的回合時間
        self.create_board_labels()  # 重新創建棋盤標籤
        self.create_hand_labels()  # 重新創建手牌標籤
        window.destroy()  # 關閉難易度視窗
        self.Name_Input_Window()  # 進入輸入玩家姓名頁面



    def start_game(self):
        self.button_pressed = True  # 設置按鈕按下標誌位
        self.welcome_page()
        round = 1

        # 在棋盤正中間放置一個隨機字母
        center_row = board_size // 2
        center_col = board_size // 2
        random_letter = random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
        self.game.board.placeCard(Card(random_letter), center_row, center_col)

        # 更新GUI棋盤顯示
        self.update_board()

        self.update_hands()
        self.update_turn_label()
        self.start_button.config(state='disabled')
        self.restart_button.config(state='normal')
        self.pass_button.config(state='normal')
        self.submit_button.config(state='normal')
        self.undo_button.config(state='normal')
        self.swap_button.config(state='normal')
        # 啟動計時器
        self.timer.start()

    def restart_game(self):
        self.button_pressed = True  # 設置按鈕按下標誌位
        confirm = tk.messagebox.askyesno("Confirm Restart", "Are you sure you want to restart the game?")
        if confirm:
            self.game = Scrabble()
            
            player1 = Player('Player 1')
            player2 = Player('Player 2')
            self.game.add_player(player1)
            self.game.add_player(player2)
            self.player_turn = 0
            self.cards_played = 0
            self.tmp_list = [[] for _ in range(hand_size)]
            self.word_list = []
            self.selected_card = None
            self.vocabulary_list = []  # 清空vocabulary_list
            self.round = 1
            self.clear_board()
            self.update_round_label()
            self.update_scores()
            self.update_hands()
            self.update_turn_label()
            self.update_vocabulary()  # 更新vocabulary欄位
            self.start_button.config(state='normal')
            self.restart_button.config(state='disabled')
            self.pass_button.config(state='disabled')
            self.submit_button.config(state='disabled')
            self.undo_button.config(state='disabled')
            self.swap_button.config(state='disabled')
            
            # 暫停計時器
            self.timer.stop()

    def pass_turn(self):
        self.button_pressed = True  # 設置按鈕按下標誌位        
        player = self.game.players[self.player_turn]
        self.cards_played, self.tmp_list = self.game.pass_turn(player, self.cards_played, self.tmp_list)
        self.tip_label.config(text=f'{player.name} has chosen to skip!', foreground='red')
        self.update_board()
        self.update_hands()
        self.timer.reset()  # 重置計時器
        if self.game.consecutive_passes == pass_conti_limit:
            self.game.end_game()  # 連續pass達到4次，遊戲結束
            self.reset_gui()  # 重置GUI
        else:
            self.switch_turn()

    def __del__(self):
        # 停止播放音樂並退出 Pygame 混音器
        pygame.mixer.music.stop()
        pygame.mixer.quit()

    def reset_gui(self):
        self.player_turn = 0
        self.cards_played = 0
        self.round = 1
        self.tmp_list = [[] for _ in range(hand_size)]
        self.word_list = []
        self.selected_card = None
        self.vocabulary_list = []
        self.clear_board()
        self.update_scores()
        self.update_hands()
        self.update_turn_label()
        self.update_vocabulary()

    def create_vocabulary_labels(self):
        vocabulary_frame = ttk.LabelFrame(self.main_frame, text='Vocabulary', padding=5, relief='raised')
        vocabulary_frame.grid(row=1, column=2, rowspan=2, sticky='nsew', padx=2, pady=2)

        # 創建Canvas和Scrollbar
        vocabulary_canvas = tk.Canvas(vocabulary_frame)
        vocabulary_scrollbar = ttk.Scrollbar(vocabulary_frame, orient="vertical", command=vocabulary_canvas.yview)
        vocabulary_canvas.configure(yscrollcommand=vocabulary_scrollbar.set)

        # 創建一個Frame來放置單詞標籤
        self.vocabulary_inner_frame = ttk.Frame(vocabulary_canvas)
        vocabulary_canvas.create_window((0, 0), window=self.vocabulary_inner_frame, anchor='nw')

        # 將Canvas和Scrollbar放置在vocabulary_frame中
        vocabulary_canvas.pack(side="left", fill="both", expand=True)
        vocabulary_scrollbar.pack(side="right", fill="y")

        words_per_column = 15
        num_words = len(self.vocabulary_list)
        num_columns = (num_words + words_per_column - 1) // words_per_column

        self.vocabulary_labels = []  # 清空vocabulary_labels列表

        for i in range(num_columns):
            for j in range(words_per_column):
                index = i + j * num_columns
                if index < num_words:
                    word = self.vocabulary_list[index]
                    label = ttk.Label(self.vocabulary_inner_frame, text=word)
                    label.grid(row=j, column=i, padx=5, pady=2)
                    self.vocabulary_labels.append(label)  # 將新建的標籤添加到vocabulary_labels列表中

        # 更新vocabulary_inner_frame的大小
        self.vocabulary_inner_frame.update_idletasks()
        width = self.vocabulary_inner_frame.winfo_width()
        height = self.vocabulary_inner_frame.winfo_height()
        vocabulary_canvas.config(width=width, height=height)

        # 更新Canvas的滾動區域
        self.vocabulary_inner_frame.bind("<Configure>", lambda e: vocabulary_canvas.configure(
            scrollregion=vocabulary_canvas.bbox("all")))

    def submit_word(self):
        self.button_pressed = True  # 設置按鈕按下標誌位
        player = self.game.players[self.player_turn]
        self.cards_played, self.tmp_list, self.word_list, self.initial_score = self.game.submit_word(player,
                                                                                                     self.tmp_list,
                                                                                                     self.cards_played,
                                                                                                     self.word_list)
        initial_score = self.initial_score

        if self.cards_played == 0:
            # 如果沒有成功放置手牌，歸還手牌並且移除棋盤上出的牌
            for i in range(len(self.tmp_list)):
                if self.tmp_list[i]:
                    row, col = self.tmp_list[i][1], self.tmp_list[i][2]
                    self.game.board.removeCard(row, col)
                    player.hand.add_a_card(self.tmp_list[i][0])
            self.tmp_list = [[] for i in range(hand_size)]
            self.update_board()
            self.update_hands()
            self.update_timer()
        else:
            for word in self.word_list:
                if word not in self.vocabulary_list:
                    self.vocabulary_list.append(word)
            words_played = len(self.word_list)
            score_diff = player.score - initial_score
            if words_played == 1:
                self.tip_label.config(text=f'{player.name} got {score_diff} points for spelling {words_played} word!',
                                      foreground='limegreen')
            else:
                self.tip_label.config(text=f'{player.name} got {score_diff} points for spelling {words_played} words!',
                                      foreground='limegreen')

            self.update_vocabulary()
            self.update_scores()
            self.update_hands()
            self.switch_turn()
            self.vocabulary_inner_frame.update_idletasks()
            width = self.vocabulary_inner_frame.winfo_width()
            if width > self.master.winfo_width():
                self.master.geometry(f"{width + 20}x{self.master.winfo_height()}")

    def update_vocabulary(self):
        # 清空vocabulary_inner_frame中的所有標籤
        for widget in self.vocabulary_inner_frame.winfo_children():
            widget.destroy()

        words_per_column = 15
        num_words = len(self.vocabulary_list)
        num_columns = (num_words + words_per_column - 1) // words_per_column

        self.vocabulary_labels = []  # 清空vocabulary_labels列表

        for i in range(num_columns):
            for j in range(words_per_column):
                index = i + j * num_columns
                if index < num_words:
                    word = self.vocabulary_list[index]
                    label = ttk.Label(self.vocabulary_inner_frame, text=word)
                    label.grid(row=j, column=i, padx=5, pady=2)
                    self.vocabulary_labels.append(label)  # 將新建的標籤添加到vocabulary_labels列表中

        # 更新vocabulary_inner_frame的大小
        self.vocabulary_inner_frame.update_idletasks()
        width = self.vocabulary_inner_frame.winfo_width()
        height = self.vocabulary_inner_frame.winfo_height()
        self.vocabulary_inner_frame.master.config(width=width, height=height)

        # 更新Canvas的滾動區域
        self.vocabulary_inner_frame.bind("<Configure>", lambda e: self.vocabulary_inner_frame.master.configure(
            scrollregion=self.vocabulary_inner_frame.master.bbox("all")))

    def set_layout_weights(self):
        self.master.rowconfigure(0, weight=1)
        self.master.rowconfigure(1, weight=1)
        self.master.columnconfigure(0, weight=1)
        self.master.columnconfigure(1, weight=1)
        self.master.columnconfigure(2, weight=1)

    def start_timer(self):
        self.timer_running = True
        self.update_timer()  # 在這裡立即呼叫 update_timer()

    def draw_timer(self, surface):
        surface.blit(self.timer_text, self.timer_rect)

    def update_timer(self):
        player = self.game.players[self.player_turn]
        if self.button_pressed:
            self.button_pressed = False
            return

        if self.timer.timer_running:
            if self.timer.remaining_time > 0:
                minutes, seconds = divmod(self.timer.remaining_time, 60)
                time_string = f"{minutes:02d}:{seconds:02d}"
                self.timer_label.config(text=time_string)
                if self.timer.remaining_time <= 10:
                    self.timer_label.config(foreground="red")
                else:
                    self.timer_label.config(foreground="black")
                self.master.after(1000, self.update_timer)
            else:
                createmessage(f"Time is up for {player.name}!")
                self.timer.stop()
                self.switch_turn()
                self.update_round_label()

    def switch_turn(self):
        current_player = self.game.players[self.player_turn]
        current_player.refill(self.game.deck)
        self.player_turn = (self.player_turn + 1) % len(self.game.players)
        self.update_hands()
        self.cards_played = 0
        self.tmp_list = [[] for _ in range(hand_size)]
        self.word_list = []
        self.round += 0.5
        self.update_turn_label()
        self.update_round_label()
        self.selected_card = None
        self.timer.reset()  # 重置倒計時
        self.timer.start()  # 啟動計時器
        self.has_swapped = False  # 重置 has_swapped 標誌變數
        self.swap_button.config(state='normal')  # 將 swap_button 重新設置為 normal 狀態

    def clear_board(self):
        for row in range(board_size):
            for col in range(board_size):
                self.board_labels[row][col].config(text='')

    def update_board(self):
        for row in range(board_size):
            for col in range(board_size):
                self.board_labels[row][col].config(text=self.game.board.board[row][col])

    def update_hands(self):
        current_player = self.game.players[self.player_turn]
        for j, label in enumerate(self.hand_labels):
            if j < len(current_player.hand.cards):
                label.config(text=current_player.hand.cards[j].alphabet)
            else:
                label.config(text='')

    def update_scores(self):
        for i, player in enumerate(self.game.players):
            self.score_labels[i].config(text=f'{player.name}: {player.score}')

    def play_card(self, row, col):
        if self.selected_card is None:
            return
        player = self.game.players[self.player_turn]
        alphabet = self.selected_card.alphabet
        if player.play_a_card(alphabet, row, col, self.game.board):
            self.cards_played += 1
            self.tmp_list[self.cards_played - 1].append(alphabet)
            self.tmp_list[self.cards_played - 1].append(row)
            self.tmp_list[self.cards_played - 1].append(col)
            self.update_board()
            self.update_hands()
            self.selected_card = None
            for label in self.hand_labels:
                label.config(relief='raised')
        else:
            self.tip_label.config(text='Invalid move! Please try again.', foreground='red')
    def swap_cards(self):
        player = self.game.players[self.player_turn]
        if self.has_swapped:
            self.tip_label.config(text='You can only swap cards once per turn!', foreground='red')
            return

        if not hasattr(self, 'selected_swap_cards'):
            self.selected_swap_cards = []
            self.swap_button.config(text='Confirm Swap')
            self.tip_label.config(text='Select cards to swap...', foreground='blue')
        else:
            opponent = self.game.players[(self.player_turn + 1) % len(self.game.players)]
            # 隨機選擇對手手牌中等量的卡牌進行交換
            opponent_swap_cards = random.sample(opponent.hand.cards, len(self.selected_swap_cards))
            # 將玩家選擇的卡牌與對手的卡牌進行交換
            for player_card, opponent_card in zip(self.selected_swap_cards, opponent_swap_cards):
                player.hand.cards.remove(player_card)
                opponent.hand.cards.remove(opponent_card)
                player.hand.cards.append(opponent_card)
                opponent.hand.cards.append(player_card)
            self.selected_swap_cards = []
            self.swap_button.config(text='Swap')
            self.tip_label.config(text=f'{player.name} swapped cards with {opponent.name}!', foreground='blue')
            self.update_hands()
            # 取消選中卡牌的反白顯示
            for label in self.hand_labels:
                label.config(relief='raised', background='white')
            # 刪除selected_swap_cards屬性,回到正常選牌模式
            del self.selected_swap_cards
            self.selected_card = None
            self.has_swapped = True  # 設置本輪已經使用過 swap
            self.swap_button.config(state='disabled')  # 將 swap_button 設置為 disabled 狀態

    def select_card(self, index):
        player = self.game.players[self.player_turn]
        if index < len(player.hand.cards):
            if hasattr(self, 'selected_swap_cards'):
                card = player.hand.cards[index]
                if card in self.selected_swap_cards:
                    self.selected_swap_cards.remove(card)
                    self.hand_labels[index].config(relief='raised', background='white')
                else:
                    self.selected_swap_cards.append(card)
                    self.hand_labels[index].config(relief='sunken', background='powderblue')
                # 如果玩家選擇了卡牌,將Swap按鈕的文本更新為'Confirm Swap'
                if len(self.selected_swap_cards) > 0:
                    self.swap_button.config(text='Confirm Swap')
                else:
                    self.swap_button.config(text='Swap')
            else:
                self.selected_card = player.hand.cards[index]
                for label in self.hand_labels:
                    label.config(relief='raised', background='white')
                self.hand_labels[index].config(relief='sunken', background='powderblue')

    def undo_play(self):
        self.button_pressed = True  # 設置按鈕按下標誌位
        Success = 1
        player = self.game.players[self.player_turn]
        self.cards_played, self.tmp_list, Success = self.game.undo_play(player, self.tmp_list, self.cards_played)
        if Success == 1:
            self.tip_label.config(text='')
            self.update_board()
            self.update_hands()
            self.update_timer()
        else:
            self.tip_label.config(text='You have not played a card yet!', foreground='red')
            self.update_timer()

class Timer:
    def __init__(self, master, label, duration, on_timeout):
        self.master = master
        self.label = label
        self.duration = duration
        self.on_timeout = on_timeout
        self.remaining_time = duration
        self.timer_running = False
        self.start_time = 0

    def start(self):
        self.timer_running = True
        self.start_time = time.time()
        self.update_timer()

    def stop(self):
        self.timer_running = False

    def reset(self):
        self.remaining_time = self.duration
        self.update_label()

    def update_timer(self):
        if self.timer_running:
            elapsed_time = int(time.time() - self.start_time)
            self.remaining_time = self.duration - elapsed_time
            if self.remaining_time > 0:
                self.update_label()
                self.master.after(1000, self.update_timer)
            else:
                self.timer_running = False
                self.on_timeout()

    def update_label(self):
        minutes, seconds = divmod(self.remaining_time, 60)
        time_string = f"{minutes:02d}:{seconds:02d}"
        self.label.config(text=time_string)
        if self.remaining_time <= 10:
            self.label.config(foreground="red")
        else:
            self.label.config(foreground="black")


if __name__ == "__main__":
    root = tk.Tk()
    app = ScrabbleGUI(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.__del__(), root.destroy()))  # 在關閉視窗時停止音樂播放
    root.mainloop() 
