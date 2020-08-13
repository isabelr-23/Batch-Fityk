# Be sure to have Fityk closed before running!
# Imports - use pip install {pywinauto, numpy, scipy, pandas} in the Terminal to gain access
from pywinauto import Application
import numpy as np
import pandas as pa
from scipy import sparse
from scipy.sparse.linalg import spsolve


# Baseline Removal Algorithm - P. Eilers 2005, returns baseline (z).
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

# Format File
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
fityk = input("Enter exact path to Fityk: ")

# Path to no baseline save folder:
save_csv = input("Enter exact path to save location for baseline-corrected CSV: ")

#Path to test file:
test_csv = input("Enter exact path to test CSV file, including file name and .csv: ")
test_csv_data = pa.read_csv(test_csv, header=None)
clean_test_csv_data = clean(test_csv_data)
data = clean_test_csv_data['%T']
wvnmbr = clean_test_csv_data['cm-1']

# Open Fityk
app = Application(backend='uia').start(fityk)

#config checker
config = 0

while config==0:
    # Config baseline correction
    lm = float(input("Enter lambda value (smoothness parameter) for baseline correction: "))
    p = float(input("Enter p value (asymmetry parameter) for baseline correction: "))

    # calculate baseline
    base = baseline_als(data, lm, p)

    # subtract baseline
    new_data = data - base

    # arrange processed CSV
    new_file_name = save_csv.replace('.csv','') + "\\" + r'_NOBSLINE_TEST.csv'
    new_file = pa.DataFrame()
    new_file.insert(0, "cm-1", wvnmbr, True)
    new_file.insert(1, "%T", new_data, True)
    new_file.to_csv(new_file_name, index=False)

    importFile(new_file_name)

    #check w/ User:
    print('lambda: ' + str(lm) + ' p: ' + str(p))
    is_config = input("Are these parameters final? (type True or False): ")

    if(is_config == 'True'):
        config=1
    else:
        # Replace Data
        app.Dialog.menu_select(r'Session -> Reset')
        config=0
