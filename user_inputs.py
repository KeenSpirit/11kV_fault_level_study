import math
import tkinter as tk
from tkinter import ttk
import sys
from typing import Dict, List, Tuple, Any

def get_input(app):
    study = FaultLevelStudy(app)
    return study.main()

class FaultLevelStudy:
    def __init__(self, app):
        self.app = app

    def main(self) -> Tuple[List[str], Dict[str, List[float]]]:
        radial_list = self.mesh_feeder_check()
        feeder_list, external_grid = self.feeders_external_grid(radial_list)
        return feeder_list, external_grid

    def center_window(self, root, width, height):
        """Center the window on the user's screen"""
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        root.geometry(f"{width}x{height}+{x}+{y}")

    def mesh_feeder_check(self) -> List[str]:
        self.app.PrintPlain("Checking for radial feeders...")
        all_grids = self.app.GetCalcRelevantObjects('*.ElmXnet')
        grids = [grid for grid in all_grids if grid.GetAttribute('outserv') == 0]
        all_feeders = [fdr for fdr in self.app.GetCalcRelevantObjects('*.ElmFeeder') if fdr.IsEnergized()]
        radial_list = []
        for feeder in all_feeders:
            cubicle = feeder.GetAttribute('obj_id')
            down_devices = cubicle.GetAll(1, 0)
            up_devices = cubicle.GetAll(0, 0)
            if any(item in grids for item in down_devices) and any(item in grids for item in up_devices):
                continue
            elif any(item in grids for item in down_devices) or any(item in grids for item in up_devices):
                radial_list.append(feeder.GetAttribute('loc_name'))
        if radial_list:
            self.app.PrintPlain("Radial feeders detected.")
        else:
            self.show_no_radial_feeders_message()
        return sorted(radial_list)

    def show_no_radial_feeders_message(self):
        root = tk.Tk()
        root.title("Distribution fault study")
        # Calculate window size and center it
        window_width = 400
        window_height = 150
        self.center_window(root, window_width, window_height)
        ttk.Label(root, text="No radial feeders were found at the substation").grid(padx=5, pady=5)
        ttk.Label(root, text="To run this script, please radialise one or more feeders").grid(padx=5, pady=5)
        ttk.Button(root, text='Exit', command=lambda: self.exit_script(root)).grid(sticky="s", padx=5, pady=5)
        root.mainloop()

    def exit_script(self, root):
        self.app.PrintPlain("User terminated script.")
        root.destroy()
        sys.exit(0)

    def feeders_external_grid(self, radial_list: List[str]) -> Tuple[List[str], Dict[str, List[float]]]:
        root = tk.Tk()

        def _window_dim(radial_list):
            grids = [grid for grid in self.app.GetCalcRelevantObjects('*.ElmXnet') if grid.outserv == 0]
            grid_cols = len(grids)
            column_width = 360
            feeder_col = 285
            window_width = max((grid_cols * column_width + feeder_col), 700)
            if window_width > 1300:
                window_width = 1500
            # Height will be recomputed after widgets are built.
            window_height = 600  # provisional
            return window_width, window_height

        window_width, window_height = _window_dim(radial_list)
        self.center_window(root, window_width, window_height)
        root.title("Distribution Fault Study")

        # Main container
        main_frame = tk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Scrollable area (canvas + inner frame)
        canvas = tk.Canvas(main_frame, borderwidth=0)
        inner_frame = tk.Frame(canvas)
        vsb = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        hsb = tk.Scrollbar(main_frame, orient="horizontal", command=canvas.xview)
        canvas.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        canvas.pack(fill="both", expand=True)
        canvas.create_window((4, 4), window=inner_frame, anchor="nw")

        # Bind events to update scrollbars if ever needed
        inner_frame.bind("<Configure>", lambda event: self.onFrameConfigure(canvas, vsb, hsb))
        canvas.bind("<Configure>", lambda event: self.onCanvasConfigure(canvas, vsb, hsb))

        # Buttons at bottom (outside scroll area)
        button_frame = tk.Frame(root)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

        # Build the UI inside inner_frame
        list_length, var, grid_entries, grids = self.populate_feeders(root, inner_frame, radial_list, button_frame)

        # After widgets exist, compute required height and resize window to avoid vertical scrollbar
        root.update_idletasks()
        content_h = inner_frame.winfo_reqheight() + 20          # requested content height
        buttons_h = button_frame.winfo_reqheight() + 12         # bottom buttons
        chrome_h = 24                                           # title/labels margin
        desired_h = content_h + buttons_h + chrome_h

        screen_h = root.winfo_screenheight()
        final_h = min(desired_h, int(screen_h * 0.90))          # cap at 90% of screen height
        self.center_window(root, window_width, final_h)

        root.mainloop()

        feeder_list = [radial_list[i] for i in range(list_length) if var[i].get() == 1]
        if not feeder_list:
            return self.window_error(radial_list, 3)

        new_grid_data = self.collect_grid_data(grid_entries, radial_list)
        if not self.validate_grid_data(new_grid_data):
            return self.window_error(radial_list, 1)
        self.update_grid_data(grids, new_grid_data)

        return feeder_list, new_grid_data

    def populate_feeders(self, root, frame, radial_list, button_frame):
        """
        Adds the heading, the feeder selection area, and the external grid input area
        (which includes the three frames per grid). Returns (list_length, var, load, grids).
        """
        ttk.Label(frame, text="Select all feeders to study:", font='Helvetica 14 bold').grid(
            columnspan=3, padx=5, pady=5
        )
        ttk.Label(frame, text="(mesh feeders excluded)", font='Helvetica 10 bold').grid(
            columnspan=3, padx=5, pady=5
        )

        grids = [grid for grid in self.app.GetCalcRelevantObjects('*.ElmXnet') if grid.outserv == 0]
        grid_data = self.get_grid_data(grids)

        # Feeder checkboxes in their own frame
        feeder_frame = tk.Frame(frame)
        feeder_frame.grid(row=2, column=0, columnspan=4, sticky="nw", padx=5, pady=5)
        var = self.create_feeder_checkboxes(feeder_frame, radial_list)

        # Spacer column before the grid frames
        frame.columnconfigure(4, minsize=100)

        self.app.PrintPlain("Please enter the requested inputs.")

        # Create the 3 frames per grid (Max, Min, Sys Norm Min) and entries within
        grid_entries = self.create_external_grid_interface(frame, grids, grid_data)

        # Buttons in the fixed bottom bar
        ttk.Button(button_frame, text='Okay', command=root.destroy).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text='Exit', command=lambda: self.exit_script(root)).pack(side=tk.LEFT, padx=5)

        return len(radial_list), var, grid_entries, grids
    # ------------------------------------------------

    def get_master_grid(self, grid_loc_name):

        project = self.app.GetActiveProject()
        derived_proj = project.GetAttribute('der_baseproject')
        if derived_proj is None:
            return False
        net_dat = derived_proj.GetContents("Network Model\\Network Data")
        for network in net_dat:
            elm_nets = network.GetContents("*.ElmNet")
            for elm_net in elm_nets:
                elm_substats = elm_net.GetContents("*.ElmSubstat")
                for elm_substat in elm_substats:
                    if elm_substat.GetContents(f'{grid_loc_name}.ElmXnet', 1):
                        master_proj_grids = elm_substat.GetContents(f'{grid_loc_name}.ElmXnet', 1)[0]
                        self.app.PrintPlain(f'Gathered master grid data for {grid_loc_name}.')
                        return master_proj_grids
        self.app.PrintPlain(f'Could not find master grid data for {grid_loc_name}.')
        return False

    def get_grid_data(self, grids):
        grid_data = {}
        attributes = ['ikss', 'rntxn', 'z2tz1', 'x0tx1', 'r0tx0', 'ikssmin', 'rntxnmin', 'z2tz1min', 'x0tx1min',
                      'r0tx0min']
        for grid in grids:
            grid_data[grid] = [grid.GetAttribute(attr) for attr in attributes]
            self.app.PrintPlain(f'Finding System normal source impedance for {grid}...')
            grid_loc_name = grid.GetAttribute('loc_name')
            master_grid = self.get_master_grid(grid_loc_name)
            if master_grid:
                grid_prw = master_grid.GetAttribute('snssmin')
                ikssmin = grid_prw / (11 * math.sqrt(3))
                master_grid_attr = ['rntxnmin', 'z2tz1min', 'x0tx1min', 'r0tx0min']
                master_grid_imp = [master_grid.GetAttribute(attr) for attr in master_grid_attr]
                grid_data[grid].append(ikssmin)
                grid_data[grid].extend(master_grid_imp)
            if len(grid_data[grid]) == 10:
                self.app.PrintPlain(f'Could not fine system normal source impedance for {grid}...')
                grid_data[grid].extend([0, 0, 0, 0, 0])
        return grid_data

    def create_feeder_checkboxes(self, feeder_frame, radial_list):
        var = []
        for i, feeder in enumerate(radial_list):
            var.append(tk.IntVar())
            ttk.Checkbutton(feeder_frame, text=feeder, variable=var[-1]).grid(
                row=i, column=0, sticky="w", padx=25, pady=5
            )
        return var

    def create_external_grid_interface(self, frame, grids, grid_data):
        ttk.Label(frame, text="Enter external grid data:", font='Helvetica 14 bold').grid(
            column=5, columnspan=3, sticky="w", row=0, padx=5, pady=5
        )

        # Dedicated container for grid entries
        grid_entries_frame = tk.Frame(frame)
        grid_entries_frame.grid(row=2, column=5, columnspan=10, sticky="nw", padx=5, pady=5)

        grid_entries = {}
        for i, grid in enumerate(grids):
            grid_entries[grid] = self.create_grid_entries(grid_entries_frame, grid, grid_data[grid], i * 3)
        return grid_entries

    def create_grid_entries(self, grid_frame, grid, data, column):
        """
        Create three bordered frames per grid: Maximum, Minimum, and Sys Norm Minimum.
        """
        grid_entries = []
        labels = [
            "P-P-P fault max.", "R/X max.", "Z2/Z1 max.", "X0/X1 max.", "R0/X0 max.",
            "P-P-P fault min.", "R/X min.", "Z2/Z1 min.", "X0/X1 min.", "R0/X0 min."
        ]
        # Max values
        max_frame = tk.LabelFrame(
            grid_frame, text=f"{grid.loc_name} Maximum Values", relief="solid", bd=1, padx=5, pady=5
        )
        max_frame.grid(row=0, column=column, columnspan=3, padx=5, pady=5, sticky="ew")

        # Min values
        min_frame = tk.LabelFrame(
            grid_frame, text=f"{grid.loc_name} Minimum Values", relief="solid", bd=1, padx=5, pady=5
        )
        min_frame.grid(row=1, column=column, columnspan=3, padx=5, pady=5, sticky="ew")

        # Maximum entries (first 5)
        for i in range(5):
            label, value = labels[i], data[i]
            value = round(value, 6)
            tk.Label(max_frame, text=label).grid(row=i, column=0, pady=2, sticky="w")
            var = tk.DoubleVar(value=value)
            tk.Entry(max_frame, textvariable=var).grid(row=i, column=1, pady=2, padx=(5, 0))
            if i == 0:
                tk.Label(max_frame, text='kA').grid(row=i, column=2, ipadx=5, pady=2)
            grid_entries.append(var)

        # Minimum entries (last 5)
        for i in range(5, 10):
            label, value = labels[i], data[i]
            value = round(value, 6)
            tk.Label(min_frame, text=label).grid(row=i - 5, column=0, pady=2, sticky="w")
            var = tk.DoubleVar(value=value)
            tk.Entry(min_frame, textvariable=var).grid(row=i - 5, column=1, pady=2, padx=(5, 0))
            if i == 5:
                tk.Label(min_frame, text='kA').grid(row=i - 5, column=2, ipadx=5, pady=2)
            grid_entries.append(var)

        # Sys Norm Minimum
        sys_norm_min_frame = tk.LabelFrame(
            grid_frame, text=f"{grid.loc_name} Sys Norm Minimum Values", relief="solid", bd=1, padx=5, pady=5
        )
        sys_norm_min_frame.grid(row=2, column=column, columnspan=3, padx=5, pady=5, sticky="ew")

        for i in range(10, 15):
            label, value = labels[i-5], data[i]
            value = round(value, 6)
            tk.Label(sys_norm_min_frame, text=label).grid(row=i-10, column=0, pady=2, sticky="w")
            var = tk.DoubleVar(value=value)
            tk.Entry(sys_norm_min_frame, textvariable=var).grid(row=i-10, column=1, pady=2, padx=(5, 0))
            if i == 10:
                tk.Label(sys_norm_min_frame, text='kA').grid(row=i-10, column=2, ipadx=5, pady=2)
            grid_entries.append(var)

        if data[10] != 0:
            tk.Label(
                sys_norm_min_frame, text="Default Values Copied From Master Project"
            ).grid(row=6, columnspan=3, pady=2)

        return grid_entries

    def collect_grid_data(self, grid_entries, radial_list):
        new_grid_data = {}
        for grid in grid_entries:
            try:
                new_grid_data[grid] = [item.get() for item in grid_entries[grid]]
            except Exception:
                return self.window_error(radial_list, 2)
        return new_grid_data

    def validate_grid_data(self, new_grid_data):
        return all(new_grid_data[grid][0] <= 100
                   and new_grid_data[grid][5] <= 100
                   and new_grid_data[grid][10] <= 100 for grid in new_grid_data)

    def update_grid_data(self, grids, new_grid_data):
        for grid in grids:
            for attr, value in zip(
                ['ikss', 'rntxn', 'z2tz1', 'x0tx1', 'r0tx0', 'ikssmin', 'rntxnmin', 'z2tz1min', 'x0tx1min', 'r0tx0min'],
                new_grid_data[grid]
            ):
                setattr(grid, attr, value)
            grid.cmax = 1.1
            grid.cmin = 1
            # name = grid.loc_name
            # new_grid_data[name] = new_grid_data[grid]
            # del new_grid_data[grid]

    def window_error(self, radial_list, error_code):
        error_messages = {
            1: "Please enter fault level values in kA, not A",
            2: "Please enter numerical values only",
            3: "Please select at least one feeder to continue"
        }
        self.app.PrintPlain(error_messages[error_code])
        return self.feeders_external_grid(radial_list)

    @staticmethod
    def onFrameConfigure(canvas, vsb, hsb):
        """Update scroll region and show/hide scrollbars as needed"""
        canvas.configure(scrollregion=canvas.bbox("all"))
        FaultLevelStudy.update_scrollbars(canvas, vsb, hsb)

    @staticmethod
    def onCanvasConfigure(canvas, vsb, hsb):
        """Handle canvas resize events"""
        FaultLevelStudy.update_scrollbars(canvas, vsb, hsb)

    @staticmethod
    def update_scrollbars(canvas, vsb, hsb):
        """Show or hide scrollbars based on content size vs canvas size"""
        scrollregion = canvas.cget("scrollregion")
        if not scrollregion:
            return
        x1, y1, x2, y2 = map(float, scrollregion.split())
        content_width = x2 - x1
        content_height = y2 - y1
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        if content_height > canvas_height:
            vsb.pack(side="right", fill="y", before=canvas)
        else:
            vsb.pack_forget()
        if content_width > canvas_width:
            hsb.pack(side="bottom", fill="x", before=canvas)
        else:
            hsb.pack_forget()
        canvas.pack(fill="both", expand=True)

def get_grid_data(app) -> Dict[Any, Any]:
    """
    PowerFactory model external grid data read to put in a pd.DataFrame
    """
    all_grids = app.GetCalcRelevantObjects('*.ElmXnet')
    grids = [grid for grid in all_grids if grid.outserv == 0]
    grid_data = {}
    for grid in grids:
        grid_data['Parameter'] = ['3-P fault level (A):', 'R/X:', 'Z2/Z1:', 'X0/X1:', 'R0/X0:']
        grid_data[f'{grid.loc_name} Maximum'] = [
            round(grid.GetAttribute('ikss'), 3),
            round(grid.GetAttribute('rntxn'), 8),
            round(grid.GetAttribute('z2tz1'), 8),
            round(grid.GetAttribute('x0tx1'), 8),
            round(grid.GetAttribute('r0tx0'), 8)
        ]
        grid_data[f'{grid.loc_name} Minimum'] = [
            round(grid.GetAttribute('ikssmin'), 3),
            round(grid.GetAttribute('rntxnmin'), 8),
            round(grid.GetAttribute('z2tz1min'), 8),
            round(grid.GetAttribute('x0tx1min'), 8),
            round(grid.GetAttribute('r0tx0min'), 8)
        ]
    return grid_data

