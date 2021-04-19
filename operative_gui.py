import tkinter as tk  #
from tkinter import font as tkfont
from tkinter import ttk
from pandastable import Table

# fonts
from pipeline.emr_pipeline import EMRPipeline
from pipeline.processing.columns import load_excluded_columns_as_df, load_excluded_columns_as_list, \
    save_excluded_columns
from pipeline.processing.specific_functions import immediate_reconstruction_mentioned
from pipeline.utils.report_type import ReportType

EXTRA_SMALL_FONT = ("Helvetica", 15)
SMALL_FONT = ("Helvetica", 18)
MEDIUM_FONT = ("Helvetica", 24)
LARGE_FONT = ("Helvetica", 28)

# s = ttk.Style()
# bg = s.lookup('TFrame', 'background')  # default background color\
bg = "gray93"  # default background color

# box to put logging info
log_box = None
# app
app = None

print_debug = True
max_edit_distance_missing = 5
max_edit_distance_autocorrect = 5
substitution_cost = 1
resolve_ocr = True


class OperativeEMRApp(tk.Tk):

    def __init__(self, *args, **kwargs):

        # begin initializing GUI
        tk.Tk.__init__(self, *args, **kwargs)
        self.title_font = tkfont.Font(font=MEDIUM_FONT)

        # set color theme
        style = ttk.Style(self)
        # style.theme_use('aqua')

        # the container is where we'll stack a bunch of frames
        # on top of each other, then the one we want visible
        # will be raised above the others
        self.container = container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (StartPage, PageOne):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            frame.configure(background=bg)
            self.frames[page_name] = frame
            # put all of the pages in the same location;
            # the one on the top of the stacking order
            # will be the one that is visible.
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("StartPage")

    def show_frame(self, page_name):
        '''Show a frame for the given page name'''
        if page_name == "PageAutocorrect" and "PageAutocorrect" not in self.frames.keys():
            # initialize the auto-correct if it didn't exist
            frame = PageAutocorrect(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        else:
            frame = self.frames[page_name]
        if page_name == "PageAutocorrect":
            frame.show_table()
        frame.tkraise()


class StartPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = ttk.Label(self, text="Scanned EMR to Excel Converter", font=controller.title_font)
        label.configure(anchor="center")
        label.pack(side="top", fill="x", pady=10)

        self.button_auto = ttk.Button(self, text="Auto-corrected Columns",
                                      command=lambda: controller.show_frame("PageAutocorrect"))

        self.button_rerun = ttk.Button(self, text="Run converter", command=lambda: self.run_converter())
        self.button_rerun.pack(side="bottom", pady=10)
        self.stats_label = None  # result statistics
        self.log_box = None  # terminal logging
        self.log_scroll_bar = None  # scroll bar for log_box
        self.hint_label = None  # a hint label (printed progress is a scrollable box)

    def run_converter(self):
        self.button_rerun.pack_forget()
        if self.hint_label:
            self.hint_label.destroy()
        processing_label = ttk.Label(self, text="Processing data, please wait...", font=MEDIUM_FONT)
        processing_label.configure(anchor="center")
        processing_label.pack(side="bottom", fill="x", pady=10)
        controller = self.controller
        if self.log_box:
            self.log_box.destroy()
        self.log_box = tk.Text(self, height=25, padx=100, pady=5)
        global log_box
        log_box = self.log_box
        self.log_box.config(font=EXTRA_SMALL_FONT)
        self.log_box.pack(side="top", fill='x')

        # remove widgets when pathology_pipeline, we will add them back later
        for widget in (self.stats_label, self.button_auto, self.log_scroll_bar):
            if widget:
                widget.destroy()
        self.update()
        # run converter and get the accuracy statistics and autocorrected columns DataFrame
        operative_pipeline = EMRPipeline(start=1, end=50, report_name="operative", report_ending="OR_Redacted.pdf",
                                         report_type=ReportType.ALPHA)

        controller.stats, controller.auto_correct_df = operative_pipeline.run_pipeline(
            baseline_versions=["operative_VZ.csv"], anchor=r"^\d*\.* *",
            single_line_list=["neoadjuvant treatment", "neoadjuvant treatment?"],
            use_separator_to_capture=True,
            add_anchor=True,
            cols_to_skip=["immediate reconstruction mentioned", "laterality",
                          "reconstruction mentioned"],
            contained_capture_list=["breast incision type", "immediate reconstruction type"],
            no_anchor_list=["neoadjuvant treatment", "immediate reconstruction mentioned",
                            "localization"],
            tools={"immediate_reconstruction_mentioned": immediate_reconstruction_mentioned},
            sep_list=["surgical indication", "immediate reconstruction type"],
            perform_autocorrect=True,
            do_training=False)

        controller.auto_correct_df = controller.auto_correct_df.sort_values(
            ["Edit Distance", "Original Column", "Corrected Column"], ascending=[False, True, True])

        # remove the widgets for processing_msg
        processing_label.pack_forget()
        # self.hint_label = ttk.Label(self, text="(the above progress information is a scrollable box)", font=EXTRA_SMALL_FONT)
        self.hint_label = ttk.Label(self, text="", font=EXTRA_SMALL_FONT)
        self.hint_label.configure(anchor="center")
        self.hint_label.pack(side="top", fill="x", pady=5)

        stats = controller.stats
        # format statistics as string, e.g. (1655, 22, 16, 151, 56) becomes: "1655 same, 22 different, 16 missing..."
        stats_str = "Result: out of {} cells, {} cells are same, {} different, {} missing, {} extra".format(sum(stats),
                                                                                                            stats[0],
                                                                                                            stats[1],
                                                                                                            stats[2],
                                                                                                            stats[3])

        # add back the removed widgets
        self.stats_label = ttk.Label(self, anchor="center", text=stats_str, font=EXTRA_SMALL_FONT)
        self.button_rerun.pack(side="bottom", pady=5)
        self.button_auto = ttk.Button(self, text="Review Auto-corrected Columns",
                                      command=lambda: controller.show_frame("PageAutocorrect"))
        self.stats_label.pack(side="bottom", fill="x", pady=5)
        self.button_auto.pack(side="bottom", pady=5)


class PageOne(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = ttk.Label(self, text="This is page 1", font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)
        button = ttk.Button(self, text="Go to the start page", command=lambda: controller.show_frame("StartPage"))
        button.pack()


class PageTwo(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = ttk.Label(self, text="This is page 2", font=controller.title_font)
        label.pack(side="top", fill="x", pady=10)
        button = ttk.Button(self, text="Go to the start page", command=lambda: controller.show_frame("StartPage"))
        button.pack()


class PageAutocorrect(tk.Frame):

    def show_table(self):
        """
        display the tables
        :return:
        """
        # self.auto_table_holder.place_forget()
        # self.excl_table_holder.place_forget()
        # if self.excl_table:
        #     self.excl_table.destroy()
        # if self.auto_table:
        #     self.auto_table.destroy()
        if self.excl_table:
            self.excl_table.destroy()
            self.excl_table = Table(self.excl_table_holder, dataframe=load_excluded_columns_as_df(), showtoolbar=False,
                                    showstatusbar=True)
        if self.auto_table:
            self.auto_table.destroy()
            self.auto_table = Table(self.auto_table_holder, dataframe=self.controller.auto_correct_df,
                                    showtoolbar=False, showstatusbar=True)

        self.auto_table.show()
        self.excl_table.show()
        self.auto_table_holder.place(anchor=tk.N, relx=0.5, y=50, width=1200)
        self.excl_table_holder.place(anchor=tk.N, relx=0.5, y=380, width=1200)

    def close_table_and_save(self, controller, table_holders):
        """
        closes the table and save excluded columns
        :param controller:
        :param table_holders:
        :return:
        """

        # clear entry fields and msg
        self.original_entry.delete(0, 'end')
        self.corrected_entry.delete(0, 'end')
        self.success_msg.place_forget()

        controller.show_frame("StartPage")

    def add_exclusion(self):
        """
        Read the "original" and "corrected" text boxes and add rule to current list of excluded column pairs
        :return:
        """
        original = self.original_entry.get()
        corrected = self.corrected_entry.get()
        if len(original) and len(corrected):
            cols = load_excluded_columns_as_list()
            cols.append((original, corrected))
            save_excluded_columns(cols)
            df = load_excluded_columns_as_df()
            self.excl_table_holder.place_forget()
            self.excl_table.destroy()
            self.excl_table = Table(self.excl_table_holder, dataframe=df, showtoolbar=False, showstatusbar=True)
            self.excl_table.show()
            self.excl_table_holder.place(anchor=tk.N, relx=0.5, y=380, width=1200)
            self.fail_msg.place_forget()
            self.success_msg.place(anchor=tk.N, x=1120, y=700, width=230)
        else:
            self.success_msg.place_forget()
            self.fail_msg.place(anchor=tk.N, x=1120, y=700, width=230)

    def delete_exclusion(self):
        """
        Read the "original" and "corrected" text boxes and remove rule to current list of excluded column pairs
        :return:
        """
        original = self.original_entry.get()
        corrected = self.corrected_entry.get()
        if len(original) and len(corrected):
            cols = load_excluded_columns_as_list()
            if (original, corrected) in cols:
                cols.remove((original, corrected))
                save_excluded_columns(cols)
                df = load_excluded_columns_as_df()
                self.excl_table_holder.place_forget()
                self.excl_table.destroy()
                self.excl_table = Table(self.excl_table_holder, dataframe=df, showtoolbar=False, showstatusbar=True)
                self.excl_table.show()
                self.excl_table_holder.place(anchor=tk.N, relx=0.5, y=380, width=1200)
                self.fail_msg.place_forget()
                self.success_msg.place(anchor=tk.N, x=1120, y=700, width=230)
                return
        # else
        self.success_msg.place_forget()
        self.fail_msg.place(anchor=tk.N, x=1120, y=700, width=230)

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, background=bg)
        self.controller = controller

        # show auto-corrected columns
        label = ttk.Label(self, text="Auto-corrected Column Pairs", font=MEDIUM_FONT)
        label.place(anchor=tk.N, relx=0.5, y=10)
        label = ttk.Label(self, text="Double-click any column header to sort the table", font=EXTRA_SMALL_FONT)
        label.place(anchor=tk.N, relx=0.5, y=34)

        self.auto_table_holder = tk.Frame(self, width=1200, height=340)
        self.auto_correct_df = controller.auto_correct_df
        self.auto_table = Table(self.auto_table_holder, dataframe=self.auto_correct_df, showtoolbar=False,
                                showstatusbar=True)

        # show excluded columns
        label = ttk.Label(self, text="Excluded Column Pairs from Auto-Correct", font=MEDIUM_FONT)
        label.place(anchor=tk.N, relx=0.5, y=350)
        self.excl_table_holder = tk.Frame(self, width=1200, height=300)
        self.excluded_df = load_excluded_columns_as_df()
        self.excl_table = Table(self.excl_table_holder, dataframe=self.excluded_df, showtoolbar=False,
                                showstatusbar=True)

        # create and show tables
        self.show_table()

        # entry for adding/deleting excluded auto-correct column pairs
        label = ttk.Label(self, text="Edit Excluded Pairs", font=SMALL_FONT)
        label.place(anchor=tk.N, x=130, y=660, width=180)
        label = ttk.Label(self, text="original", font=SMALL_FONT)
        label.place(anchor=tk.N, x=280, y=660, width=120)
        label = ttk.Label(self, text="corrected", font=SMALL_FONT)
        label.place(anchor=tk.N, x=647, y=660, width=120)
        self.success_msg = ttk.Label(self, text="Success.", font=EXTRA_SMALL_FONT)
        self.fail_msg = ttk.Label(self, text="Try Again.", font=EXTRA_SMALL_FONT)
        self.original_entry = original_entry = ttk.Entry(self)
        self.corrected_entry = corrected_entry = ttk.Entry(self)
        add_exclusion = ttk.Button(self, text="Add", command=lambda: self.add_exclusion())
        delete_exclusion = ttk.Button(self, text="Delete", command=lambda: self.delete_exclusion())
        original_entry.place(anchor=tk.N, x=430, y=660, width=300)
        corrected_entry.place(anchor=tk.N, x=820, y=660, width=300)
        add_exclusion.place(anchor=tk.N, x=1055, y=660, width=110)
        delete_exclusion.place(anchor=tk.N, x=1185, y=660, width=110)

        # back button
        button = ttk.Button(self, text="Save and Back",
                            command=lambda: self.close_table_and_save(controller,
                                                                      [self.auto_table_holder, self.excl_table_holder]))
        button.place(anchor=tk.N, relx=0.5, y=700, width=120)
