from tkinter import *
from tkinter import messagebox
import pandas as pd
import os
import random

# Data handling functions (same as your original)
profiles_file = 'profiles.csv'
question_file = 'questions.csv'
questions_df = pd.read_csv(question_file)

class AdaptiveDifficulty:
    def __init__(self, initial_difficulty='medium'):
        self.user_stats = {
            'easy': {'correct': 0, 'total': 0},
            'medium': {'correct': 0, 'total': 0},
            'hard': {'correct': 0, 'total': 0}
        }
        self.current_difficulty = initial_difficulty
        
    def update_user_response(self, is_correct):
        level_stats = self.user_stats[self.current_difficulty]
        level_stats['total'] += 1
        if is_correct:
            level_stats['correct'] += 1
            
    def calculate_success_rate(self, difficulty):
        stats = self.user_stats[difficulty]
        if stats['total'] == 0:
            return 0
        return stats['correct'] / stats['total']
        
    def adjust_difficulty(self):
        success_rate = self.calculate_success_rate(self.current_difficulty)
        
        if self.current_difficulty == 'easy':
            if success_rate > 0.7:
                self.current_difficulty = 'medium'
                
        elif self.current_difficulty == 'medium':
            if success_rate > 0.7:
                self.current_difficulty = 'hard'
            elif success_rate < 0.3:
                self.current_difficulty = 'easy'
                
        elif self.current_difficulty == 'hard':
            if success_rate < 0.3:
                self.current_difficulty = 'medium'
                
        return self.current_difficulty




def Signup(username, password):
    if os.path.exists(profiles_file):
        df = pd.read_csv(profiles_file)
    else:
        df = pd.DataFrame(columns=['username', 'password', 'score', 'question_history'])

    if username in df['username'].tolist():
        return False
    
    new = pd.DataFrame([[username, password, 0, '']],
                       columns=['username', 'password', 'score', 'question_history'])
    df = pd.concat([df, new], ignore_index=True)
    df.to_csv(profiles_file, index=False)
    return True

def Login(username, password):
    if not os.path.exists(profiles_file):
        return False
    
    df = pd.read_csv(profiles_file)
    if (username in df['username'].tolist()) and (df.loc[df['username']==username,'password'].values[0] == password):
        return True
    return False

def get_history(username):
    df = pd.read_csv(profiles_file)
    idx = df.index[df['username']==username][0]
    history = df.at[idx,'question_history']
    if pd.isnull(history) or history == '' or history is None:
        return set()
    return set(history.split('|'))    

def update_history(username, question):
    df = pd.read_csv(profiles_file)
    idx = df.index[df['username']==username][0]
    history = df.at[idx,'question_history']
    if pd.isnull(history) or history == '' or history is None:
        questions = []
    else:
        questions = history.split('|')
    questions.append(question)
    df.at[idx,'question_history'] = "|".join(questions)
    df.to_csv(profiles_file, index=False)

def update_score(username, points):
    df = pd.read_csv(profiles_file)
    idx = df.index[df['username']==username][0]
    df.at[idx,'score'] += points
    df.to_csv(profiles_file, index=False)

def get_score(username):
    df = pd.read_csv(profiles_file)
    idx = df.index[df['username']==username][0]
    return int(df.at[idx,'score'])

#--------------------------------------------------------------------------#
current_user = None
question_pool = []
question = None
options = []
difficulty_adapter = None

def start_quiz(username):
    global current_user, question_pool, difficulty_adapter
    current_user = username
    difficulty_adapter = AdaptiveDifficulty()  # Initialize adapter
    answered = get_history(username)
    
    # Get questions filtered by current difficulty
    update_question_pool()
    
    if not question_pool:
        messagebox.showinfo("Done", "All questions answered at this difficulty level.")
        show_login()
        return
    
    next_question()

def update_question_pool():
    global question_pool, difficulty_adapter
    answered = get_history(current_user)
    current_diff = difficulty_adapter.current_difficulty
    
    # Filter questions by current difficulty and unanswered
    question_pool = questions_df[
        (questions_df['difficulty'] == current_diff) & 
        (~questions_df['question'].isin(answered))
    ]['question'].tolist()
    
    # If none left in current difficulty, try other difficulties
    if not question_pool:
        question_pool = questions_df[
            ~questions_df['question'].isin(answered)
        ]['question'].tolist()



def next_question():
    for widget in root.winfo_children():
        widget.destroy()

    if not question_pool:
        messagebox.showinfo("Done", "You are now Einstein :)")
        show_login()
        return

    global question, options, var
    
    question = random.choice(question_pool)
    row = questions_df.loc[questions_df['question']==question].iloc[0]
    options = [row['option1'], row['option2'], row['option3'], row['option4']]
    correct = row['correct_answer']

    question_lbl = Label(root, text=question, font=('Helvetica', 20, 'bold'), wraplength=400, fg='#3aaba9', bg='white')
    question_lbl.pack(pady=20)

    # Add difficulty display
    difficulty_lbl = Label(root, 
                         text=f"Difficulty: {difficulty_adapter.current_difficulty.capitalize()}",
                         font=('Helvetica', 12, 'bold'),
                         fg='#3aaba9',
                         bg='white')
    difficulty_lbl.pack()

    var = IntVar()
    for i, opt in enumerate(options, start=1):
        r = Radiobutton(root, text=opt, variable=var, value=i, font=('Helvetica', 16), 
                       fg='#3aaba9', bg='white', selectcolor='white')
        r.pack(anchor='w', padx=20, pady=5)

    submit = Button(root, text='Submit', font=('Helvetica', 14), command=check_answer, 
                   bg='#3aaba9', fg='white', width=20)
    submit.pack(pady=20)

    score = get_score(current_user)
    score_lbl = Label(root, text=f"Score: {score}", font=('Helvetica', 14), fg='#3aaba9', bg='white')
    score_lbl.pack()

def check_answer():
    choice = var.get()
    row = questions_df.loc[questions_df['question']==question].iloc[0]
    correct = row['correct_answer']
    is_correct = (options[choice-1] == correct)

    # Update difficulty system
    difficulty_adapter.update_user_response(is_correct)
    difficulty_adapter.adjust_difficulty()
    
    if is_correct:
        update_score(current_user, 1)
        feedback = "Correct!"
    else:
        feedback = f"Incorrect! The correct answer was {correct}"
    messagebox.showinfo("Result", feedback)

    update_history(current_user, question)
    update_question_pool()  # Refresh pool with new difficulty
    next_question()

#login/signup GUI functions
def on_entry_click(event):
    entry = event.widget
    if entry == username_entry and entry.get() == "Username":
        entry.delete(0, END)
        entry.config(fg="black", show="")
    elif entry == password_entry and entry.get() == "Password":
        entry.delete(0, END)
        entry.config(fg="black", show="*")

def on_focus_out(event):
    entry = event.widget
    if entry == username_entry and entry.get() == "":
        entry.insert(0, "Username")
        entry.config(fg="grey", show="")
    elif entry == password_entry and entry.get() == "":
        entry.insert(0, "Password")
        entry.config(fg="grey", show="")

def handle_login():
    username = username_entry.get()
    password = password_entry.get()
    
    if Login(username, password):
        messagebox.showinfo("Success", "Login Successful.")
        start_quiz(username)
    else:
        messagebox.showerror("Error", "Invalid credentials.")

def handle_signup():
    username = username_entry.get()
    password = password_entry.get()
    
    if Signup(username, password):
        messagebox.showinfo("Success", "Signup Successful.")
        start_quiz(username)
    else:
        messagebox.showerror("Error", "Username already exists.")

def show_login():
    for widget in root.winfo_children():
        widget.destroy()

    root.config(bg="white")
    main_container = Frame(root, bg="white")
    main_container.pack(fill=BOTH, expand=True)

    # Left panel (login form)
    left_panel = Frame(main_container, bg="#f5f5f5", width=350)
    left_panel.pack(side=LEFT, fill=BOTH, expand=True)
    left_panel.pack_propagate(False)

    head = Label(left_panel, text="Login to Your Account", font=("Arial", 28, "bold"), 
                fg="black", bg="#f5f5f5")
    head.pack(pady=40)

    global username_entry, password_entry
    username_entry = Entry(left_panel, width=30, font=('Helvetica', 14), fg="grey")
    username_entry.insert(0, "Username")
    username_entry.bind("<FocusIn>", on_entry_click)
    username_entry.bind("<FocusOut>", on_focus_out)
    username_entry.pack(pady=10)

    password_entry = Entry(left_panel, width=30, font=('Helvetica', 14), fg="grey")
    password_entry.insert(0, "Password")
    password_entry.bind("<FocusIn>", on_entry_click)
    password_entry.bind("<FocusOut>", on_focus_out)
    password_entry.pack(pady=10)

    sign_in = Button(left_panel, text="Log In", bg="#3aaba9", fg="white", 
                    font=('Helvetica', 14), command=handle_login)
    sign_in.pack(pady=20, padx=40, fill=X)

    # Right panel (signup portion)
    right_panel = Frame(main_container, bg="#3aaba9", width=200)
    right_panel.pack(side=RIGHT, fill=BOTH, expand=True)
    right_panel.pack_propagate(False)

    right_head = Label(right_panel, text="New Here?", font=("Arial", 28, "bold"), 
                     bg="#3aaba9", fg="white")
    right_head.pack(pady=(170,0))

    right_subhead = Label(right_panel, text="Sign up to learn in a unique way!", 
                         font=("Times new roman", 15), bg="#3aaba9", fg="white")
    right_subhead.pack(pady=10)
    
    sign_up = Button(right_panel, text="Sign Up", width=20, bg="white", 
                    fg="black", font=('Helvetica', 14), command=handle_signup)
    sign_up.pack(pady=20)

    # Footer
    footer = Label(root, text="© 2025 Quiz App By Bunny| Terms of Service", 
                  bg="white", fg="gray")
    footer.pack(side=BOTTOM, pady=20)

# Main window setup
root = Tk()
root.title("Quiz Generator")
root.geometry("700x500")
root.config(bg="#ffffff")

show_login()
root.mainloop()