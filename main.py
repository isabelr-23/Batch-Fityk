# Be sure to have Fityk closed before running!
# Imports - use pip install {pywinauto, numpy, scipy, pandas} in the Terminal to gain access
from pywinauto import Application
import numpy as np
import pandas as pd
from scipy import sparse
from scipy.sparse.linalg import spsolve
import os, time


# Baseline Removal Algorithm - P. Eilers 2005, returns baseline (z). Could update to use sparse matrices (sparse.diags)
# if encountering memory issues
def baseline_als(y, lam, p, niter=10):
    length = len(y)
    diag = sparse.csc_matrix(np.diff(np.eye(length), 2))
    one_mat = np.ones(length)
    for i in range(niter):
        w = sparse.spdiags(one_mat, 0, length, length)
        t = w + lam * diag.dot(diag.transpose())
        z = spsolve(t, one_mat*y)
        one_mat = p * (y > z) + (1-p) * (y < z)
    return z


# Import File into Fityk
def importFile(new):
    app.Dialog['Load file (custom)'].click()
    app.Dialog.Edit.type_keys(new, with_spaces=True)
    app.Dialog['Replace @0'].click()
    app.Dialog['Close'].click()

# type in script dialogue (sub out hello for script lines)
#app.Dialog.Edit.type_keys(r'hello')

# run pre-existing script (sub out hello for script address)
#app.Dialog.menu_select(r'Session -> Execute Script')
#app.Dialog.ComboBox.Edit.type_keys(r'hello')

# Add peaks
#app.Dialog['auto-add'].click()

# Auto fit
#app.Dialog['Start fitting'].click()


# Save session
def saveSession(save):
    time.sleep(1)
    app.Dialog.menu_select(r'Session -> Save Session')
    app.Dialog.ComboBox.type_keys(save, with_spaces=True)
    app.Dialog['Save'].click()


def clean(df):
    if len(df.columns) == 3:
        col = [2]
        df = df.drop(df.columns[col], axis=1)
    df = df.drop([0, 1])
    df.columns = ['cm-1', '%T']
    df = df.astype(float)
    df['%T'] = -1*df['%T']
    df = df.reset_index(drop=True)
    return df

# Ask user for Fityk path
fityk = input("Enter exact path to Fityk:")

# Ask user for Data folder path
primary = input(r"Enter exact data folder path (Ex: C:\Users\...):")

# Ask user for folder name
folder = "\\" + input("Which folder do I sort through?:")

# Path to no baseline save folder:
save_csv = input("Enter exact path to save folder for baseline-corrected CSVs")

# Path to fityk save folder:
save_fityk = input("Enter exact path to save folder for fityk sessions")

# Ask user for file version
version = input("Enter an underscore (_) followed by the file version (Ex: V1, V2, etc.):")

# Open Fityk
app = Application(backend='uia').start(fityk)

# Path to folder where raw CSV files are held:
directory = primary + folder


for filename in os.listdir(directory):
    if filename.endswith('.csv'):
        # read in and clean raw CSV
        file = filename.replace('.csv', '')
        original_file = directory + "\\" + filename
        original_data = pd.read_csv(original_file, header=None)
        clean_data = clean(original_data)
        data = clean_data['%T']

        # calculate baseline
        base = baseline_als(data, 7500000, 0.00003)

        # subtract baseline
        new_data = data - base

        # arrange processed CSV
        wvnmbr = clean_data['cm-1']
        new_file_name = save_csv + "\\" + file + '_NOBSLINE.csv'
        new_file = pd.DataFrame()
        new_file.insert(0, "cm-1", wvnmbr, True)
        new_file.insert(1, "%T", new_data, True)
        new_file.to_csv(new_file_name, index=False)

        importFile(new_file_name)

        save_session_name = save_fityk + "\\" + file + version + '.fit'
        saveSession(save_session_name)

        # Replace Data
        app.Dialog.menu_select(r'Session -> Reset')

    else:
        continue