import tkinter as tk
from tkinter import ttk
import powerfactory as pf
import sys


def get_project(app):
    """
    Returns the Powerfactory project belonging to a given Energex substation acronym.
    """

    substation = sub_selection(app)
    projects_subs = all_substations(app)
    projects = find_project(app, projects_subs, substation)
    if projects is not None:
        app.PrintPlain(f"Substation {substation} belongs to PowerFactory project {projects}.")
    else:
        app.PrintPlain(f"A matching project for substation {substation} could not be found.")


def sub_selection(app):
    """User inputs a substation acronym"""

    root = tk.Tk()
    root.title("Find Project")
    root.geometry("+800+200")

    name_var = tk.StringVar()
    ttk.Label(root, text="Please enter the Energex substation three letter acronym", font='Helvetica 14 bold').\
        grid(columnspan=3, sticky="w", padx=5, pady=5)
    ttk.Label(root, text="Input must meet the following criteria:", font=('calibre',10,'normal')).\
        grid(row=4, column=0, sticky="w", padx=5, pady=5)
    ttk.Label(root, text="- The substation must have a PowerFactory study case assigned", font=('calibre',10,'normal')).\
        grid(row=5, column=0, sticky="w", padx=5, pady=5)
    ttk.Label(root, text="- Only alphabet"
                         "ical characters are allowed (case insensitive)", font=('calibre',10,'normal')).\
        grid(row=6, column=0, sticky="w", padx=5, pady=5)
    ttk.Label(root, text="- The input must be three characters long", font=('calibre',10,'normal')).\
        grid(row=7, column=0, sticky="w", padx=5, pady=5)
    ttk.Label(root, text="The result will be displayed in the Output Window.", font=('calibre',10,'normal')).\
        grid(row=8, column=0, sticky="w", padx=5, pady=5)
    ttk.Entry(root, textvariable = name_var, font=('calibre',10,'normal')).grid(row=9, columnspan=3, sticky="w", padx=5, pady=5)
    ttk.Button(root, text='Okay', command=lambda: root.destroy()) \
            .grid(row=10, column=0, sticky="w", padx=5, pady=5)
    ttk.Button(root, text='Exit', command=lambda: exit_script(root)) \
            .grid(row=10, column=1, sticky="w", padx=5, pady=5)
    # Run the interface
    root.mainloop()

    # collect results and give error message if input is wrong type
    substation = name_var.get()
    if len(substation) > 3:
        substation = error_message(app, 1)
        return substation
    elif len(substation) < 1:
        substation = error_message(app, 2)
        return substation
    elif not substation.isalpha():
        substation = error_message(app, 3)
        return substation
    else:
        return substation.upper()


def exit_script(root):
    """Exits script"""

    app = pf.GetApplication()
    app.PrintPlain("User terminated script.")
    root.destroy()
    sys.exit(0)


def error_message(app, x):
    """Print an error message if input is wrong format"""

    if x == 1:
        app.PrintPlain("Please input 3 characters or less")
    elif x == 2:
        app.PrintPlain("Please input a substation acronym to proceed")
    else:
        app.PrintPlain("Please input alphabetical characters only")
    study = sub_selection(app)
    return study


def all_substations(app):
    """
    "Abermain": ["ABY", "BDB"]
    :param app:
    :return:
    """
    projects_subs = {}

    user = app.GetCurrentUser()
    database = user.GetAttribute('fold_id')
    seq_models = database.GetContents("Publisher\\MasterProjects\\SEQ Models")[0]
    projects = seq_models.GetContents("*.IntPrj")
    for project in projects:
        study_cases = project.GetContents("Study Cases")
        for study_case in study_cases:
            sub_study_cases = study_case.GetContents("Substation Study Cases")
        for sub_study_case in sub_study_cases:
            intcases = [intcase.GetAttribute('loc_name').split()[0] for intcase in sub_study_case.GetContents("*.IntCase")]
        projects_subs[project.GetAttribute('loc_name')] = intcases
    return projects_subs


def find_project(app, projects_subs, substation):

    substation = substation.upper()
    for project, sub_list in projects_subs.items():
        app.PrintPlain(f"Looking in project {project} for substation {substation}...")
        if substation in sub_list:
            return project
    return None