import powerfactory as pf
import tkinter as tk
from tkinter import ttk
import sys
from importlib import reload
import find_substation as fs
import radial_feeder_fault_study as radial
import fdr_open_points
reload(radial)
reload(fs)
reload(fdr_open_points)

def main():
    """11kV fault level study

    Version 1.18
    04/11/2025

    By Dan Park
    dan.park@energyq.com.au

    """

    #
    # INITIALISE SCRIPT
    #

    # Get the application object
    app = pf.GetApplication()
    # Enables the user to manually stop the script
    app.SetEnableUserBreak(1)
    app.ClearOutputWindow()
    # Turn the echo off (suppress output window messages)
    echo(app)

    study = study_selection(app)
    if study == "0" or study == "1":
        prjt = app.GetActiveProject()
        if prjt is None:
            app.PrintWarn("No Active Project, Ending Script")
            return

        # Turn on all grids momentarily to load all floating terminals in to line connected elements
        # (used for fdr_open_points algorithm)
        user_selected_study_case = app.GetActiveStudyCase()
        switch_study_case(app, user_selected_study_case, all_grids=True)
        switch_study_case(app, user_selected_study_case, all_grids=False)

    if study == "0":
        radial.main(app)
    elif study == "1":
        fdr_open_points.main(app)
    elif study == "2":
        fs.get_project(app)

    # Restore the echo
    echo(app, off=False)

    # script run successfully.


def study_selection(app):
    """User selects a study to undertake"""

    root = tk.Tk()
    root.title("11kV_fault_level_study")
    root.geometry("+800+200")

    selection = tk.StringVar()
    selection.set('var')
    ttk.Label(root, text="Select study to undertake:", font='Helvetica 14 bold').\
        grid(columnspan=3, sticky="w", padx=5, pady=5)
    tk.Radiobutton(root, text="Find PowerFactory Project", value="0", variable=selection) \
                .grid(row=2, column=0, sticky="w", padx=30, pady=5)
    tk.Radiobutton(root, text="Find Feeder Open Points", value="1", variable=selection) \
        .grid(row=3, column=0, sticky="w", padx=30, pady=5)
    tk.Radiobutton(root, text="Protection Assessment (Legacy)", value="2", variable=selection) \
        .grid(row=4, column=0, sticky="w", padx=30, pady=5)
    tk.Radiobutton(root, text="Protection Assessment (No Relays Configured In Model)", value="2", variable=selection) \
        .grid(row=4, column=0, sticky="w", padx=30, pady=5)
    tk.Radiobutton(root, text="Protection Assessment (All Relays Configured In Model)", value="2", variable=selection) \
        .grid(row=4, column=0, sticky="w", padx=30, pady=5)

    ttk.Button(root, text='Okay', command=lambda: root.destroy()) \
            .grid(row=5, column=0, sticky="w", padx=5, pady=5)
    ttk.Button(root, text='Exit', command=lambda: exit_script(root)) \
            .grid(row=5, column=1, sticky="w", padx=5, pady=5)

    # Run the interface
    root.mainloop()
    # collect results and give error message if input is wrong type
    if selection.get() != 'var':
        study = selection.get()
    else:
        study = no_study_selected(app)
        return study

    return study


def exit_script(root):
    """Exits script"""

    app = pf.GetApplication()
    app.PrintPlain("User terminated script.")
    root.destroy()
    sys.exit(0)


def no_study_selected(app):
    """Ensure the user selects a study before continuing"""

    app.PrintPlain("Please select a study to continue")
    study = study_selection(app)
    return study


def switch_study_case(app, user_selected_study_case, all_grids=False):

    if all_grids:
        int_case = app.GetProjectFolder("study").GetContents("All Active Grids Study Case")[0]
        app.PrintPlain("WARNING: All Active Grids Study Case could not be found.")
        app.PrintPlain("WARNING: Calculated feeder open points may be incomplete.")
        return
    else:
        int_case = user_selected_study_case
    int_case.Activate()


def echo(app, off=True):
    """Supresses the printing of Warning and information messages to the Output.

    Usage: Echo(app) turns the echo off
           Echo(app, off = False) turns the echo back on
    """
    echo = app.GetFromStudyCase('ComEcho')
    if off:
        echo.SetAttribute('iopt_err', False)
        echo.SetAttribute('iopt_wrng', False)
        echo.SetAttribute('iopt_info', False)
        echo.SetAttribute('iopt_oth', True)
        echo.Off()
    else:
        echo.On()


# Python boilerplate
if __name__ == '__main__':
    main()
