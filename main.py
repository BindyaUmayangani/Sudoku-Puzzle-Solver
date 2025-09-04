import tkinter as tk
from tkinter import messagebox
import random
import time
import json
import threading

# -------------------------
# Sudoku Board Logic
# -------------------------
class SudokuBoard:
    def __init__(self):
        self.board = [[0]*9 for _ in range(9)]
        self.solution = None

    def find_empty(self):
        for i in range(9):
            for j in range(9):
                if self.board[i][j] == 0:
                    return (i, j)
        return None

    def valid(self, num, pos):
        row, col = pos
        if num in self.board[row]:
            return False
        if num in [self.board[i][col] for i in range(9)]:
            return False
        box_x = col // 3
        box_y = row // 3
        for i in range(box_y*3, box_y*3 + 3):
            for j in range(box_x*3, box_x*3 + 3):
                if self.board[i][j] == num:
                    return False
        return True

    def solve(self):
        empty = self.find_empty()
        if not empty:
            return True
        row, col = empty
        for num in range(1, 10):
            if self.valid(num, (row, col)):
                self.board[row][col] = num
                if self.solve():
                    return True
                self.board[row][col] = 0
        return False

    def generate(self, clues=30):
        self.board = [[0]*9 for _ in range(9)]
        self.solve()
        self.solution = [row[:] for row in self.board]
        puzzle = [[0]*9 for _ in range(9)]
        positions = [(i,j) for i in range(9) for j in range(9)]
        random.shuffle(positions)
        for i,j in positions[:clues]:
            puzzle[i][j] = self.board[i][j]
        self.board = puzzle

# -------------------------
# Sudoku GUI
# -------------------------
class SudokuGUI:
    def __init__(self, master):
        self.master = master
        master.title("🧩 Sudoku Pro")
        master.config(padx=20, pady=20, bg="#f0f0f0")

        self.board = SudokuBoard()
        self.cells = []
        self.start_time = None
        self.timer_running = False
        self.hints_used = 0
        self.MAX_HINTS = 3
        self.difficulty = 'medium'
        self.best_times_file = "best_times.json"
        self.load_best_times()

        # Timer Label
        self.timer_label = tk.Label(master, text="Time: 00:00", font=("Arial", 14, "bold"), bg="#f0f0f0")
        self.timer_label.grid(row=0, column=0, columnspan=9, pady=(0,10))

        # Create 3x3 frames for the big boxes
        self.frames = [[None]*3 for _ in range(3)]
        for i in range(3):
            for j in range(3):
                f = tk.Frame(master, highlightbackground="black", highlightthickness=2, bd=0)
                f.grid(row=i*3+1, column=j*3, rowspan=3, columnspan=3, sticky="nsew")
                self.frames[i][j] = f

        # Fill each frame with Entry widgets with light borders
        for i in range(9):
            row = []
            for j in range(9):
                frame = self.frames[i//3][j//3]
                e = tk.Entry(frame, width=2, font=("Arial", 20), justify='center', relief="solid", bd=1, highlightthickness=0)
                e.grid(row=i%3, column=j%3, padx=1, pady=1, ipadx=5, ipady=5)
                e.bind("<KeyRelease>", lambda event, x=i, y=j: self.check_entry(x, y))
                row.append(e)
            self.cells.append(row)

        # Buttons
        self.solve_btn = tk.Button(master, text="Solve Sudoku", bg="#4CAF50", fg="white", font=("Arial", 14, "bold"), command=self.solve_animation_thread)
        self.solve_btn.grid(row=10, column=0, columnspan=3, pady=20, sticky="nsew")

        self.hint_btn = tk.Button(master, text="Hint", bg="#FFA500", fg="white", font=("Arial", 14, "bold"), command=self.give_hint)
        self.hint_btn.grid(row=10, column=3, columnspan=3, pady=20, sticky="nsew")

        self.new_btn = tk.Button(master, text="New Puzzle", bg="#2196F3", fg="white", font=("Arial", 14, "bold"), command=self.generate_puzzle)
        self.new_btn.grid(row=10, column=6, columnspan=3, pady=20, sticky="nsew")

        # Difficulty Selector
        tk.Label(master, text="Difficulty:").grid(row=11, column=0, columnspan=2)
        self.diff_var = tk.StringVar(value=self.difficulty)
        tk.OptionMenu(master, self.diff_var, "easy", "medium", "hard").grid(row=11, column=2, columnspan=2)

        # Initial puzzle
        self.generate_puzzle()

    # -------------------------
    # Puzzle Handling
    # -------------------------
    def generate_puzzle(self):
        self.hints_used = 0
        self.start_time = time.time()
        self.timer_running = True
        self.difficulty = self.diff_var.get()
        clues = {'easy':40, 'medium':30, 'hard':20}[self.difficulty]
        self.board.generate(clues=clues)
        for i in range(9):
            for j in range(9):
                self.cells[i][j].delete(0, tk.END)
                if self.board.board[i][j] != 0:
                    self.cells[i][j].insert(0, str(self.board.board[i][j]))
                    self.cells[i][j].config(state="readonly", disabledforeground="black", bg="#ddd")
                else:
                    self.cells[i][j].config(state="normal", bg="white", fg="black")
        self.update_timer()

    def get_current_board(self):
        b = []
        for i in range(9):
            row = []
            for j in range(9):
                val = self.cells[i][j].get()
                row.append(int(val) if val.isdigit() else 0)
            b.append(row)
        return b

    # -------------------------
    # Hint System
    # -------------------------
    def give_hint(self):
        if self.hints_used >= self.MAX_HINTS:
            messagebox.showwarning("No Hints Left", f"Maximum {self.MAX_HINTS} hints per puzzle!")
            return
        board = self.get_current_board()
        empty_cells = [(i,j) for i in range(9) for j in range(9) if board[i][j]==0]
        if not empty_cells:
            messagebox.showinfo("No Empty Cells", "Puzzle already complete!")
            return
        i,j = random.choice(empty_cells)
        board[i][j] = self.board.solution[i][j]
        self.cells[i][j].insert(0, str(self.board.solution[i][j]))
        self.cells[i][j].config(fg="blue")
        self.hints_used += 1

    # -------------------------
    # Real-time Error Check
    # -------------------------
    def check_entry(self, i, j):
        val = self.cells[i][j].get()
        if not val.isdigit():
            return
        val = int(val)
        if self.board.solution:
            if val != self.board.solution[i][j]:
                self.cells[i][j].config(fg="red")
            else:
                self.cells[i][j].config(fg="#888888")  # user input light gray

        # Check if puzzle is complete
        if all(self.cells[r][c].get().isdigit() and int(self.cells[r][c].get()) == self.board.solution[r][c]
               for r in range(9) for c in range(9)):
            if self.timer_running:
                self.timer_running = False
                messagebox.showinfo("Congratulations!", f"Puzzle completed in {self.format_time(time.time() - self.start_time)}!")
                self.update_best_time(self.difficulty, time.time() - self.start_time)

    # -------------------------
    # Solve Animation
    # -------------------------
    def solve_animation_thread(self):
        threading.Thread(target=self.solve_animation).start()

    def solve_animation(self):
        def backtrack():
            empty = self.board.find_empty()
            if not empty:
                return True
            row, col = empty
            for num in range(1, 10):
                if self.board.valid(num, (row, col)):
                    self.board.board[row][col] = num
                    self.cells[row][col].delete(0, tk.END)
                    self.cells[row][col].insert(0, str(num))
                    self.cells[row][col].config(fg="orange")
                    self.master.update()
                    time.sleep(0.05)
                    if backtrack():
                        return True
                    self.board.board[row][col] = 0
                    self.cells[row][col].delete(0, tk.END)
                    self.master.update()
                    time.sleep(0.05)
            return False

        board = self.get_current_board()
        self.board.board = board
        if backtrack():
            if self.timer_running:
                self.timer_running = False
                end_time = time.time()
                messagebox.showinfo("Solved!", f"Sudoku solved in {self.format_time(end_time - self.start_time)}!")
                self.update_best_time(self.difficulty, end_time - self.start_time)
        else:
            messagebox.showerror("Error", "No solution exists!")

    # -------------------------
    # Timer
    # -------------------------
    def update_timer(self):
        if not self.start_time or not self.timer_running:
            return
        elapsed = time.time() - self.start_time
        self.timer_label.config(text=f"Time: {self.format_time(elapsed)}")
        self.master.after(1000, self.update_timer)

    def format_time(self, seconds):
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

    # -------------------------
    # Best Time Tracking
    # -------------------------
    def load_best_times(self):
        try:
            with open(self.best_times_file, "r") as f:
                self.best_times = json.load(f)
        except:
            self.best_times = {"easy": None, "medium": None, "hard": None}

    def update_best_time(self, difficulty, time_sec):
        best = self.best_times.get(difficulty)
        if not best or time_sec < best:
            self.best_times[difficulty] = time_sec
            with open(self.best_times_file, "w") as f:
                json.dump(self.best_times, f)
            messagebox.showinfo("New Best Time!", f"New best time for {difficulty.capitalize()}: {self.format_time(time_sec)}")

# -------------------------
# Run App
# -------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = SudokuGUI(root)
    root.mainloop()
