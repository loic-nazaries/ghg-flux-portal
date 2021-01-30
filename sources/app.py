#!/usr/bin/env python
# coding: utf-8

# # LaPiscine - Projet pro

# ## Dashboard Web for GHG_fluxes Analysis

# Filename: ghg_flux_data_dashboard.py
# Previous version: ghg_flux_data_dashboard_v3 (less bugs)

"""Create a Web app to analyse greenhouse gas (GHG) emmissions at EucFACE.

TODO make a list of known issues and give context
TODO if there are magic numbers (i.e. constants like a default file path),
    capitalise the variable name
TODO set up buttons with code for saving generated figures, e.g. with the
    'st.button(label="Save Figure")' command, i.e. save new figures using
    Matplotlib command 'plt.savefig()' ?  NOT working for now
    Also, automate file naming (e.g. 'FILE_PATH_FIGURE + plot_name + ".png"')
    and ask user for name with "st.text_input"
TODO store EucFACE data file(s) on GitHub and create a link to load data
    and start analysis on Streamlit
TODO to upload a file, add choice to use default (EucFACE) file with a checkbox
    or load the user's file
TODO create an attachment list to compress and send by e-mail
    Idea: create empty list and append new files to it
TODO for dummy generation, if number of levels is more than 2, apply
    label encoding, e.g. use "0, 1, 2, 3" for the "Season" variable
BUG fix problem w/ dummies as variable dummified even if 2+ levels are present
TODO set-up user login: add an "assert" code to force user to add his/her user
    name as well as a valid email address, i.e. check that the address
    contains a '@' (use a regular expression)
BUG can only choose independent/numerical variables as grouping factor for
    the bi- and uni-variate analyses
TODO prepare histogram/box plots to check the distribution of the dependent
    variables selected
TODO select a pickle file to load data
TODO if no pickling, assign type (category, dummy, numerical) to variables
    like "Ring" and "Year"
TODO add multiple attachments when sending emails
TODO when graphing functions will be defined, add the cache method:
    @st.cache(
        persist=True,
        suppress_st_warning=False,
        allow_output_mutation=True,
    )
BUG not possible to log users in from existing users in 'usertable' SQL table
TODO allow admin to delete user's details from the data base
    Idea: use checkbox next to users' table with "st.sidebar.beta_columns(2)")
TODO in new_user and in admin section, check if a user/password already exists
    when entering new user's details
TODO replace the "sign up" and "log in" menus by two buttons on the same line
    (use "st.beta_columns()" method - already set up; now implement it)
TODO add "beta_columns" for "image_1" & "image_2"
TODO hide secrets (admin & password keys) in Windows "user variables" of
    "environmental variables" (streamlit_admin; streamlit_password)
        import os
        os.environ.get("ADMIN", "admin")
    OR, better
    use .env file: manage them simply with a "dotenv" file in project folder
        pip install python-dotenv  # package
    LIKE
    explicitly providing path to '.env'
        from pathlib import Path
        env_path = Path('.') / '.env'
        load_dotenv(dotenv_path=env_path)
    # settings.py
        import os
        USER = os.getenv("admin")
        PASSWORD = os.getenv("password")
TODO change colours of the "save" buttons (use CSS)
"""

import datetime
import hashlib
import smtplib
import sqlite3
import time
import warnings
from email.message import EmailMessage

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import seaborn as sns
import streamlit as st
from IPython.core.interactiveshell import InteractiveShell
from PIL import Image

warnings.filterwarnings("ignore")

# from pandas_profiling import ProfileReport
# import jupyterlab

# # try below to handle passwords and secret keys using a ".env" file
# import os
# USER = os.environ.get("user")
# PASSWORD = os.environ.get("password")
# print(USER, PASSWORD)
# # or
# # pip install python-dotenv
# from dotenv import load_dotenv
# from pathlib import Path
# env_path = Path('.') / '.env'
# load_dotenv(dotenv_path=env_path)

# # if using a Jupyter notebook, include:
# %matplotlib inline
# %config InlineBackend.figure_formats = ["pdf", "png"]


InteractiveShell.ast_node_interactivity = "all"


# DO NOT delete as it contains streamlit conditions
def start_config():
    """Initialise the configuration for pandas features display mode.

    The display is set to:
        - print all columns (0 maximum columns) in the terminal
        - the maximum width of columns is set to 1000 pixels
        - a maximum of 200 rows will be displayed in the terminal
        - the default precision of floats will be 3 decimal points

    Also, how to insert the default file paths ?
    """
    options = {
        "display": {
            "max_columns": None,  # Max number of columns
            "max_colwidth": None,  # Max width of columns
            "max_seq_item": None,  # display all items in list
            # "max_rows": None,  # Max number of rows
            # "min_rows": 20,  # 20 rows minimum
            "precision": 3,  # Float number precision (3 decimal places)
            "encoding": "UTF-8",
        },
    }
    for display, option_vals in options.items():
        for setting, user_val in option_vals.items():
            pd.set_option(f"{display}.{setting}", user_val)
            # sns.set(f"{display}={setting}", user_val)
            sns.set(
                context="notebook",  # or "poster"
                style="whitegrid",
                palette="colorblind",
                color_codes=True,
            )
            # sns.color_palette("muted", 6)  # or 12 ?
            sns.despine(left=True, trim=True)
            st.set_option("deprecation.showfileUploaderEncoding", False)
            st.set_option("deprecation.showPyplotGlobalUse", False)
            # plt.figure(figsize=(12, 10)
    # print(display, setting)
    return options


start_config()


def make_hashes(user_password):
    """[summary].

    Args:
        user_password ([type]): [description]

    Returns:
        [type]: [description]
    """
    return hashlib.sha256(str.encode(user_password)).hexdigest()


def check_hashes(user_password, hashed_password):
    """[summary].

    Args:
        user_password ([type]): [description]
        hashed_password (bool): [description]

    Returns:
        [type]: [description]
    """
    if make_hashes(user_password) == hashed_password:
        return hashed_password
    return False  # use "else:" at beginning ?


# user database management
# conn = sqlite3.connect(db)  # "db" is the file path to local SQLite database
db_connection = sqlite3.connect("user_management.db")
connection = db_connection.cursor()  # what is it ?

# # instead of using "def create_usertable()" below, hard-code default
# # "usertable" including admin credentials first, e.g.:
# user_details = {"user_name": ["admin"], "user_password": ["password"]}
# user_table = pd.DataFrame.from_dict(user_details)
# # save dataframe to SQL database
# # it's equivalent to using "INSERT INTO" (see "add_user_data" function below)
# user_table.to_sql(
#     "User Management",  # or just usertable ?
#     con=db_connection,
#     if_exists="append",  # if the table already exists
#     index=False
# )
# # use "db_connection.execute()" or "db_connection.execute()" ?
# conn.execute("SELECT * FROM usertable").fetchall()
# db_connection.close()  # use here or after calling the objects/variables ?


def create_usertable():
    """[summary]

    Use "db_connection.execute()" or "db_connection.execute()" ?

    Note: the database name MUST be in ONE word, i.e. no '_' nor '-' allowed
    """
    # connection.execute(
    #     "CREATE TABLE IF NOT EXISTS usertable(user_name TEXT, user_password TEXT)"
    # )
    # alternative to above
    user_table = """
        CREATE TABLE IF NOT EXISTS usertable(
            user_name TEXT,
            user_password TEXT
        )
        """
    connection.execute(user_table)
    db_connection.commit()  # added as a test => OK ?


def add_user_data(user_name, user_password):
    """[summary].

    Protecting against SQL injections

    Args:
        user_name ([type]): [description]
        user_password ([type]): [description]
    """
    # connection.execute(
    #     "INSERT INTO usertable(user_name, user_password) VALUES (?,?)",
    #     (user_name, user_password),
    # )
    # alternative to above
    user_data = """
        INSERT INTO usertable(user_name, user_password) VALUES (?,?)
        """
    connection.execute(user_data, (user_name, user_password))
    db_connection.commit()
    data = connection.fetchall()  # added as a test => OK
    return data  # added as a test => OK


def login_user(user_name, user_password):
    """[summary].

    Protecting against SQL injections

    Args:
        user_name ([type]): [description]
        user_password ([type]): [description]

    Returns:
        [type]: [description]
    """
    # connection.execute(
    #     "SELECT * FROM usertable WHERE user_name = ? AND user_password = ?",
    #     (user_name, user_password),
    # )
    # alternative to above
    user_log = (
        "SELECT * FROM usertable WHERE user_name = ? AND user_password = ?"
    )
    connection.execute(user_log, (user_name, user_password))
    data = connection.fetchall()
    return data


def view_all_users():
    """[summary].

    Returns:
        [type]: [description]
    """
    # connection.execute("SELECT * FROM usertable")
    # alternative to above
    user_view = "SELECT * FROM usertable"
    connection.execute(user_view)
    data = connection.fetchall()
    return data


# try to refactor by moving outside the function the .st methods, when possible
def select_page():
    """Include the various pages of the Web app."""
    menu = (
        "Portal Homepage",
        "Admin",
    )
    page = st.sidebar.selectbox(label="Choose a page", options=menu)

    if page == "Portal Homepage":
        st.title("The Greenhouse Gas Estimation Portal")
        st.info(
            """
            The dashboard performs an automatic analysis of greenhouse gas
            (GHG) emission data. The user can customise the selection and
            visualisation of the output data.
            The GHG list includes the following gases:\n
                - methane (CH4)\n
                - carbon dioxide (CO2)\n
                - nitrous oxide (N2O)
            """
        )
        st.warning(
            """
            Please log in before entering the portal.\n
            If you need to register, please choose the "Sign Up" section
            from the left-side panel and provide your e-mail address.
            """
        )

        # # display buttons to sign up/log in
        # # plus, use placeholder st.empty() ?
        # login_button, signup_button = st.sidebar.beta_columns(2)
        # login = login_button.button("Log In")
        # signup = signup_button.button("Sign Up")

        # connect_portal = (login_button, signup_button)  # NOT working
        connect_portal = ("Log In", "Sign Up")
        connect = st.sidebar.selectbox(
            label="Choose to Log In or Sign Up", options=connect_portal
        )
        # if signup:  # NOT working
        if connect == "Sign Up":
            st.sidebar.title("Create a New Account")
            new_user_name = st.sidebar.text_input(label="Choose User Name")
            new_user_password = st.sidebar.text_input(
                label="Enter e-mail Address as Password", type="password"
            )
            submit_button = st.sidebar.button(label="Submit")
            if submit_button:
                create_usertable()
                add_user_data(
                    new_user_name, make_hashes(new_user_password),
                )
                # display loading message
                with st.spinner("Registering..."):
                    time.sleep(1)
                    st.success(
                        f"{new_user_name.title()}, "
                        f"you have successfully created an account. "
                    )
                st.info("You can now log in from the left-side panel.")

        # BUG not possible to log users in from existing users in 'usertable'
        # SQL table
        # elif login:  # NOT working
        elif connect == "Log In":
            st.sidebar.title("Log In to the Portal")
            user_name = st.sidebar.text_input(label="User Name.")
            user_password = st.sidebar.text_input(
                label="""
                    Enter e-mail Address as Password \n
                    (BUG - temporally use 'password' as default)
                    """,
                type="password",
            )
            log_checkbox = st.sidebar.checkbox(
                label="Log In/Log Out", value=False
            )
            if log_checkbox:
                create_usertable()
                hashed_password = make_hashes(user_password)
                log_info = login_user(
                    user_name, check_hashes(user_password, hashed_password),
                )
                # use below password as user login above NOT working
                if user_password == "password":
                    # if above 'user_password == "password"' commented out,
                    # remove one indent from here all the way down to
                    # 'else:
                    #     st.warning("Incorrect User name and/or Password")'

                    # display loading message
                    with st.spinner("Loging in..."):
                        time.sleep(1)
                        # if log_info:
                        st.success(
                            f"{user_name.title()}, "
                            f"Welcome to Greenhouse Gas Estimation Portal!"
                        )
                        st.sidebar.date_input(
                            label="Today is: ", value=datetime.datetime.now(),
                        )

                        st.header("About the Portal")
                        about = st.beta_expander("Show/Hide Details")
                        about.info(
                            """
                            In the "Data Exploration" page, the user can
                            customise the analysis through the options
                            available in the "User Input Parameters" to the
                            left-side panel:\n
                                - selection of categorical & dependent
                                variables\n
                                - choice of experimental settings (treatment
                                factors) to include to the statistical
                                analysis\n
                                - grouping variables to fine-tune the data
                                output visualisation and statistical results
                            Also, the user can explore data analysis outputs by
                            inspecting the interactive plots and tables.

                            Finally, the "Statistical Analysis" page allows the
                            user to test various treatment effects on the data.

                            Note: only preprocessed files can be analysed.
                            In other words, the data must be already cleaned
                            and transformed to optimise the quality of the
                            statistical analysis.
                            Soon, the user will be able to select a range of
                            imputation and transformation techniques.
                            Finally, a machine learning module will also be
                            implemented.

                            As an exemple, the user can use the data from the
                            EucFACE experiment. A quick overview is available
                            from the "EucFACE Site Presentation" page.
                            """
                        )
                        analysis_select = st.selectbox(
                            "Choose a Data Analysis",
                            [
                                "Data Exploration (EucFACE experiment)",
                                "Statistics",
                                "EucFACE Site Presentation",
                            ],
                        )
                        if (
                            analysis_select
                            == "Data Exploration (EucFACE experiment)"
                        ):
                            st.title("Exploratory Data Analysis (EDA)")
                            st.warning(
                                """
                                **Disclaimer**: It is assumed that the user has
                                prior experience in **data analysis**, and is
                                familiar with the basic concepts of
                                **dataframe**, **data manipulation**, including
                                its associated "jargon" such as knowing the
                                difference between *independent* and
                                *dependent* variables, the meaning of *dummy*
                                variables or the concept of *data
                                transformation*.\n
                                However, a lexicon will be prepared in the
                                near future.
                                """
                            )
                            st.info(
                                """
                                The dashboard will visualise the effect of
                                elevated atmospheric CO2 concentration on
                                greenhouse gas (GHG) emissions.
                                """
                            )
                            st.sidebar.title("User Input Parameters")

                            def user_input_features():
                                """Select the various options & variables for
                                processing analyses.

                                Returns:
                                    tuple: selection variables from user choices
                                """
                                st.header("Procedure")
                                procedure = st.beta_expander(
                                    "Show/Hide Details"
                                )
                                procedure.info(
                                    """
                                        For a good user experience, please 
                                        read (and follow) these instructions.\n
                                        #### Notes:\n
                                        * The left-side panel is used to 
                                        select the user's parameters to be 
                                        included in the analysis
                                        * It is not possible to skip the 
                                        preparatory steps 1 to 6

                                        1. Upload the **input** file
                                        2. Select the **categorical** variables
                                        3. Select the categorical variables 
                                        to dummify (a.k.a. "**dummies**")\n
                                        To activate this option, tick the 
                                        label box
                                        > "***Convert categorical variables
                                        to dummy variables***"

                                        4. Select the **dependent** variables
                                        (a.k.a. "target variables")
                                        5. Select the dataframe **index** to 
                                        concatenate the features selected
                                        above\n
                                        > **The purpose is to create a new
                                        dataframe based on the user's
                                        choices**\n

                                        6. Select the variables that will be 
                                        used to group samples by **category** 
                                        (or **treatment**) and calculate the 
                                        **group means**
                                        7. Bivariate Analysis\n
                                        To activate this option, tick the 
                                        sidebar label box
                                        > "***Perform Bivariate Analysis***"

                                        Select the GHG variable for the 
                                        *univariate* and *time-series* analyses

                                        8. Univariate Analysis\n
                                        To activate this option, tick the 
                                        sidebar label box
                                        > "***Perform Univariate Analysis***"

                                        9. Time-Series Analysis\n
                                        To activate this option, tick the 
                                        sidebar label box
                                        > "***Perform Time-Series Analysis***"

                                        10. Save Data\n
                                        Choose the files to compress and send 
                                        by e-mail
                                        """
                                )
                                st.error(
                                    """
                                    **Warning**: If moving to another page,
                                    the data generated within this page
                                    will be lost !!
                                    """
                                )
                                st.header("1. Load Dataset")
                                st.sidebar.subheader("1. Upload an input file")
                                # TODO add choice to use default (EucFACE)
                                # file  or user's file
                                upload_file = st.sidebar.file_uploader(
                                    label="Choose a .csv or .pkl file format.",
                                    type=["csv", "pkl"],
                                    accept_multiple_files=False,
                                )
                                if upload_file is not None:

                                    @st.cache(
                                        persist=True,
                                        suppress_st_warning=False,
                                        allow_output_mutation=True,
                                    )
                                    def load_data():
                                        """Load data file.

                                        Upload file only works with the
                                        "pd.read_csv()" method but not with
                                        the "pd.read_pickle" method.

                                        Returns:
                                            object: transformed without
                                                outliers dataframe from EDA
                                        """
                                        # # BUG reading ".pkl" file NOT working
                                        # dataframe = pd.read_pickle(upload_file)
                                        dataframe = pd.read_csv(
                                            upload_file,
                                            sep="[;,]",
                                            encoding="utf-8",
                                            engine="python",
                                            header=0,
                                            skipinitialspace=True,
                                            skip_blank_lines=True,
                                            na_values="nan",
                                            warn_bad_lines=True,
                                        )
                                        return dataframe

                                    ghg_flux_data = load_data()
                                    # display loading message
                                    with st.spinner("Loading Data..."):
                                        # display progress bar
                                        bar = st.progress(0)
                                        for i in range(100):
                                            bar.progress(i + 1)
                                            time.sleep(0.01)
                                        st.success(
                                            "The file has been uploaded."
                                        )

                                else:
                                    st.warning(
                                        "Awaiting data file to be uploaded."
                                    )

                                st.subheader("Output table (preview).")
                                st.table(ghg_flux_data.head(10))
                                st.text(
                                    f"{ghg_flux_data.shape[0]} rows and "
                                    f"{ghg_flux_data.shape[1]} columns"
                                )
                                st.write("\n")

                                st.subheader("Dataset Information")
                                dataframe_info = ghg_flux_data.info()
                                st.table(
                                    dataframe_info
                                )  # gives empty column !!
                                # date_format =

                                # display results on same row but on two columns
                                (
                                    number_treatments,
                                    number_rings,
                                ) = st.beta_columns(2)
                                with number_treatments:
                                    st.write(
                                        f"Number of Samples for each "
                                        f"CO2 treatment"
                                    )
                                    st.table(
                                        ghg_flux_data["co2_treatment"]
                                        .value_counts()
                                        .sort_values(ascending=False)
                                    )
                                with number_rings:
                                    st.write("Number of Samples for each Ring")
                                    st.table(
                                        ghg_flux_data["Ring"]
                                        .value_counts()
                                        .sort_values(ascending=False)
                                    )

                                st.sidebar.subheader(
                                    "2. Categorical Variables"
                                )
                                cat_vars_select = st.sidebar.multiselect(
                                    label=f"Select one or more categorical "
                                    f"variables.",
                                    options=ghg_flux_data.columns,
                                )
                                st.sidebar.write(
                                    "You selected",
                                    len(cat_vars_select),
                                    "categorical variables.",
                                )

                                st.sidebar.subheader("3. Dummy Variables")
                                dummy_vars_select = st.sidebar.multiselect(
                                    label=f"Select one or more categorical "
                                    f"variables to be dummified.",
                                    options=cat_vars_select,
                                )
                                st.sidebar.write(
                                    "You selected",
                                    len(dummy_vars_select),
                                    "dummy variables.",
                                )
                                st.sidebar.subheader("4. Dependent Variables")
                                dep_vars_select = st.sidebar.multiselect(
                                    label=f"Select one or more dependent "
                                    f"(numerical) variables.",
                                    options=ghg_flux_data.columns,
                                )
                                st.sidebar.write(
                                    "You selected",
                                    len(dep_vars_select),
                                    "dependent variables.",
                                )
                                st.sidebar.subheader(
                                    f"5. Dataframe Index to Concatenate the "
                                    f"Variable Types"
                                )
                                index_select = st.sidebar.multiselect(
                                    label=f"Select the index ID of the "
                                    f"concatenated dataframe.",
                                    # # options from "cat_vars" disabled for now
                                    # options=cat_vars_select,
                                    options=("SampleTrackerNo", ""),
                                )
                                return (
                                    ghg_flux_data,
                                    cat_vars_select,
                                    dummy_vars_select,
                                    dep_vars_select,
                                    index_select,
                                )

                            (
                                ghg_flux_data,
                                cat_vars_select,
                                dummy_vars_select,
                                dep_vars_select,
                                index_select,
                            ) = user_input_features()

                            st.header("Variable Selection")
                            st.info(
                                """
                                The variables must be chosen from the
                                various options on the left-side panel.
                                """
                            )
                            st.subheader(
                                "2. Categorical Variables (preview) \n"
                            )
                            cat_vars = ghg_flux_data[cat_vars_select]
                            st.table(cat_vars.head(10))

                            st.write("#### Categorical variable types: \n")
                            st.dataframe(cat_vars.dtypes)
                            # BUG cannot change the data type for "Year" to a
                            # "category" otherwise
                            # there are issues with concatenation in section #5
                            # hence, change to "object" instead
                            st.write(
                                """
                                Changing variables type from 'integer' to
                                'object'
                                """
                            )
                            # # other BUG, below list comprehension not
                            # changing anything
                            # cat_vars_list = [
                            #     cat_vars[var].astype("object")
                            #     for var in cat_vars
                            #     if type(cat_vars[var]) == ["int"]
                            # ]
                            # st.write("#### Categorical variable types after
                            # conversion: \n")
                            # st.dataframe(cat_vars_list.dtypes)

                            # # alternative code to above, but still with no
                            # # effect
                            # labelencoder = LabelEncoder()
                            # for var in cat_vars:
                            #     if cat_vars.dtypes[var] == "int":
                            #         cat_vars[
                            #             cat_vars.columns[var]
                            #         ] = labelencoder.fit_transform(
                            #             cat_vars.dtypes[var] == "object"
                            #         )
                            # st.dataframe(cat_vars.dtypes)

                            # other alternative code to above but HARD-CODED
                            # for "Year", "Ring"
                            # and "SampleTrackerNo" only
                            cat_vars["Year"] = cat_vars["Year"].astype(
                                "object"
                            )
                            st.write(
                                f"For example, the variable 'Year' data type "
                                f"is now: **{cat_vars.Year.dtypes}**"
                            )
                            cat_vars["Ring"] = cat_vars["Ring"].astype(
                                "object"
                            )
                            cat_vars["SampleTrackerNo"] = cat_vars[
                                "SampleTrackerNo"
                            ].astype("object")
                            st.write(
                                """
                                Categorical variable types AFTER conversion: \n
                                """
                            )
                            st.dataframe(cat_vars.dtypes)

                            st.subheader("3. Dummy Variables (preview) \n")
                            st.info(
                                """
                                #### Important Note: \n
                                If the "Convert categorical variables to dummy
                                variables" box is checked (see below), then the
                                dummy variables must be selected from
                                the sidebar.
                                """
                            )
                            convert_cat_vars_check = st.checkbox(
                                label="""
                                    Convert categorical variables to dummy
                                    variables
                                    """,
                                value=False,
                            )
                            if convert_cat_vars_check:
                                for var in cat_vars:
                                    # BUG not working properly as vars selected
                                    # even if uniq vals > 2
                                    if len(cat_vars[var].unique()) <= 2:
                                        dummy_vars = pd.get_dummies(
                                            data=ghg_flux_data[
                                                dummy_vars_select
                                            ],
                                            prefix_sep="_",
                                            dummy_na=False,
                                            # if drop_first=False, it avoids
                                            # having collinearity with machine
                                            # learning algorithms
                                            drop_first=True,
                                            dtype="int",
                                        )
                                    # # BUG below code seems to do nothing
                                    # elif len(cat_vars[var].unique()) > 2:
                                    #     # creating instance of labelencoder
                                    #     labelencoder = LabelEncoder()
                                    #     # assigning numerical values & storing
                                    #     # in another column
                                    #     ghg_flux_data[
                                    #         "season_label"
                                    #     ] = labelencoder.fit_transform(
                                    #         ghg_flux_data["Season"]
                                    #     )
                                    #     # labelencoder.fit(ghg_flux_data["Season"])
                                    #     labelencoder_name_mapping = dict(
                                    #         zip(
                                    #             labelencoder.classes_,
                                    #             labelencoder.transform(
                                    #                 labelencoder.classes_
                                    #             ),
                                    #         )
                                    #     )
                                    # # try w/ list comprehension but NOT working
                                    # dummy_vars_long = [
                                    #     labelencoder.fit_transform(
                                    #         ghg_flux_data[dummy_vars_select]
                                    #     )
                                    #     for var in cat_vars
                                    # ]
                                    # else:
                                    #     pass
                                ########## how is "season_label" working
                                # although not defined ?!!
                                # dummy_vars = dummy_vars.join(
                                #     ghg_flux_data["season_label"], how="left"
                                # )
                                st.write(dummy_vars.head(10))
                                # st.write(
                                # """
                                # Print encoded values for 'Season' using
                                # 'season_label': \n
                                # """
                                # )
                                # st.markdown(labelencoder_name_mapping)
                                # st.write(ghg_flux_data[
                                #     "season_label"
                                # ].unique())

                            st.subheader("4. Dependant Variables (preview) \n")
                            dep_vars = ghg_flux_data[dep_vars_select]
                            st.write(dep_vars.head(10))
                            st.write(
                                "### Dependent variables statistics summary"
                            )
                            st.table(dep_vars.describe())

                            st.subheader(
                                f"5. Concatenation of Selected Variables "
                                f"(preview)"
                            )
                            # st.info(
                            #     """
                            #     In oder to create a new dataframe, a dataframe
                            #     index MUST be selected from the left-side
                            #     panel.
                            #     """
                            # )
                            if index_select is None:
                                st.warning(
                                    """
                                    A dataframe index MUST be selected from
                                    the sidebar menu.
                                    """
                                )
                            else:
                                with st.spinner("Applying new index..."):
                                    time.sleep(1)
                                    st.success(
                                        f"The dataframe index selected is: "
                                        f"{str(index_select)}"
                                    )

                            # concatenate the categorical, dummy and dependent
                            # variables
                            # Note: there is an option to NOT include dummies
                            # to the new dataset using the st.checkbox() method
                            include_dummy_check = st.checkbox(
                                label="Include dummy variables", value=False,
                            )
                            if not include_dummy_check:
                                variables_concat = [cat_vars, dep_vars]
                            else:
                                variables_concat = [
                                    cat_vars,
                                    dummy_vars,
                                    dep_vars,
                                ]
                            concat_dataset = pd.concat(
                                variables_concat, sort=False, axis=1
                            ).set_index(index_select)
                            st.table(concat_dataset.head(10))
                            st.text(
                                f"{concat_dataset.shape[0]} rows and "
                                f"{concat_dataset.shape[1]} columns"
                            )

                            st.subheader(
                                f"6. Table of Aggregated Ring Means "
                                f"(from pseudo-replicates)(preview)"
                            )
                            st.info(
                                """
                                    #### Important note:
                                        In order to choose a grouping factor,
                                        it first needs to be part of the
                                        categorical variables list.
                                    For EucFACE, the variable "Ring" **MUST**
                                    be selected as a grouping factor in order
                                    to average the pseudo-replicates
                                    represented by the seven gas sampling
                                    collars (labelled as "Collar_Unique_ID"
                                    within the dataset).
                                """
                            )
                            st.sidebar.subheader(
                                "6. Aggregation of Grouping Variables"
                            )
                            group_select = st.sidebar.multiselect(
                                label=f"Select the categorical variables "
                                f"(or treatments) for the aggregation "
                                f"table.",
                                options=cat_vars.columns,
                            )
                            st.sidebar.write(
                                "You selected",
                                len(group_select),
                                "grouping variables.",
                            )
                            # calculate aggregates with means and stdev
                            # (for display only)
                            # use "group_select" as grouping factors
                            pseudo_rep_aggregate_mean_std = concat_dataset.groupby(
                                by=group_select
                            ).aggregate(
                                ["mean", "std"]
                            )
                            st.table(pseudo_rep_aggregate_mean_std.head(10))
                            # calculate aggregates with means only
                            # (save to file)
                            # use "group_select" as grouping factors
                            pseudo_rep_aggregate_mean = concat_dataset.groupby(
                                by=group_select
                            ).mean()
                            # display table shape of the
                            # "pseudo_rep_aggregate_mean" variable only
                            st.text(
                                f"{pseudo_rep_aggregate_mean.shape[0]} "
                                f"rows and "
                                f"{pseudo_rep_aggregate_mean.shape[1]} columns"
                            )
                            save_data_button = st.button(
                                label="Save Aggregated Data"
                            )
                            if save_data_button:
                                pseudo_rep_aggregate_mean.to_csv(
                                    f"C:/python_projects/exam_piscine_heroku_redone/"
                                    f"data/ghg_flux_data_stats.csv",
                                    sep=",",
                                    encoding="utf-8",
                                    na_rep="nan",
                                    header=True,
                                    index=True,
                                )
                                with st.spinner("Data Aggregation..."):
                                    time.sleep(1)
                                    st.success(
                                        """
                                        The aggregated file was saved
                                        successfully.
                                        """
                                    )

                            # code below cannot be used within the
                            # "user_input_features" function
                            # as the below section deals with the aggregation
                            # table using the
                            # "pseudo_rep_aggregate_mean" dataframe which is
                            # instanciated AFTER the function, thus not using
                            # the "ghg_flux_data" dataframe which is the
                            # main dataframe
                            st.header("Description of GHG emissions")
                            st.info(
                                """
                                Select the variables from the left-side panel.
                                """
                            )

                            st.subheader(
                                "7. Bivariate Analysis (Scatter Plot)"
                            )
                            st.info(
                                """
                                Use a scatter plot to visualise the
                                relationships beetween GHG fluxes.\n
                                Select the variables from the left-side panel.
                                """
                            )
                            st.error(
                                """
                                BUG !! Can only choose independent/numerical
                                variables as grouping factor.
                                No categorical variables available.
                                """
                            )
                            st.sidebar.subheader("7. Bivariate Analysis")
                            perform_analysis_check = st.sidebar.checkbox(
                                label="Perform Bivariate Analysis",
                                value=False,
                            )
                            if perform_analysis_check:
                                x_axis = st.sidebar.selectbox(
                                    label="Select a GHG flux for x-axis",
                                    options=dep_vars.columns,
                                )
                                # format the "x_axis" variable for a prettier
                                # display on graphs
                                # remove everything from "_" onwards, then
                                # transform as all caps
                                x_name = x_axis[: x_axis.find("_")].upper()

                                y_axis = st.sidebar.selectbox(
                                    label="Select a GHG flux for y-axis",
                                    options=dep_vars.columns,
                                )
                                # same as above but with the "y_axis" variable
                                y_name = y_axis[: x_axis.find("_")].upper()

                                group_scatter = st.sidebar.selectbox(
                                    label="Select a group/colour for graphing",
                                    options=pseudo_rep_aggregate_mean.columns,
                                    key=1,
                                )
                                st.sidebar.error(
                                    "BUG !! See main panel for details."
                                )
                                scatter_plot_check = st.checkbox(
                                    label="Show/Hide Graph",
                                    value=False,
                                    key=1,
                                )
                                if not scatter_plot_check:
                                    scatter_plot = px.scatter(
                                        pseudo_rep_aggregate_mean,
                                        x=x_axis,
                                        y=y_axis,
                                        color=group_scatter,
                                        # error_x="e",
                                        # error_y="e",
                                        marginal_y="violin",
                                        marginal_x="box",
                                        trendline="ols",
                                        # hover_data=[
                                        #     "Ring", "Block", x_axis, y_axis
                                        # ],
                                        title="""
                                            Relationship between dependent
                                            variables
                                            """,
                                    )
                                    scatter_plot.update_xaxes(
                                        title=x_name + " Flux"
                                    )
                                    scatter_plot.update_yaxes(
                                        title=y_name + " Flux"
                                    )
                                    st.plotly_chart(scatter_plot)

                                save_figure_button = st.button(
                                    label="Save Figure", key=1
                                )
                                if save_figure_button:
                                    st.error(
                                        "NOT working - saving a blank figure"
                                    )
                                    plt.savefig(
                                        f"C:/python_projects/exam_piscine_heroku_redone/"
                                        f"figures/bivariate.png",
                                        # + plot_name +
                                        # ".png",
                                        dpi=100,
                                        bbox_inches="tight",
                                    )
                                    with st.spinner("Saving Figure..."):
                                        time.sleep(1)
                                        st.success(
                                            """
                                            The image file was saved
                                            successfully.
                                            """
                                        )
                                        st.write("\n")  # leave a blank space

                            st.sidebar.subheader("Greenhouse Gas Selection")
                            st.sidebar.info(
                                "For Univariate and Time-Series Analyses only"
                            )
                            ghg_select = st.sidebar.radio(
                                label="Select one gas at the time",
                                options=dep_vars_select,
                            )
                            ghg_name = ghg_select[
                                : ghg_select.find("_")
                            ].upper()

                            st.subheader("8. Univariate Analysis (Bar Plot)")
                            st.info(
                                """
                                Choose a categorical variable to visualise
                                its effect on the dependent variables.\n
                                Select the options from the left-side panel.
                                """
                            )
                            st.error(
                                """
                                BUG !! Can only choose independent/numerical
                                variables as grouping factor.\n
                                Only numerical variables available as
                                categories for the x-axis.
                                """
                            )
                            st.sidebar.subheader("8. Univariate Analysis")
                            perform_analysis_check = st.sidebar.checkbox(
                                label="Perform Univariate Analysis",
                                value=False,
                            )
                            if perform_analysis_check:
                                univariate_analysis_select = st.sidebar.selectbox(
                                    label="""
                                            Select a categorical variable
                                            (as x-axis) for the univariate
                                            analysis of GHG fluxes
                                        """,
                                    options=(
                                        pseudo_rep_aggregate_mean.columns,
                                    ),
                                )
                                group_univariate = st.sidebar.selectbox(
                                    label="Select a group/colour for graphing",
                                    options=pseudo_rep_aggregate_mean.columns,
                                    key=2,
                                )
                                st.sidebar.error(
                                    "BUG !! See main panel for details"
                                )
                                # below, option to comment out between a bar
                                # graph or an histogram
                                bar_plot_check = st.checkbox(
                                    label="Show/Hide Graph",
                                    value=False,
                                    key=2,
                                )
                                if not bar_plot_check:
                                    ghg_emissions_univariate_graph = px.bar(
                                        pseudo_rep_aggregate_mean,
                                        x=univariate_analysis_select,
                                        y=ghg_select,
                                        color=group_univariate,
                                        barmode="group",
                                        title=f"Effect of "
                                        f"{univariate_analysis_select} "
                                        f"on {ghg_name} Fluxes",
                                    )
                                    ghg_emissions_univariate_graph.update_yaxes(
                                        title=ghg_name + " Flux"
                                    )
                                    st.plotly_chart(
                                        ghg_emissions_univariate_graph
                                    )

                                save_figure_button = st.button(
                                    label="Save Figure", key=2
                                )
                                if save_figure_button:
                                    st.error(
                                        "NOT working - saving a blank figure"
                                    )
                                    plt.savefig(
                                        f"C:/python_projects/exam_piscine_heroku_redone/"
                                        f"figures/univariate.png",
                                        # + plot_name +
                                        # ".png",
                                        dpi=100,
                                        bbox_inches="tight",
                                    )
                                    with st.spinner("Saving Figure..."):
                                        time.sleep(1)
                                        st.success(
                                            """
                                            The image file was saved
                                            successfully.
                                            """
                                        )
                                        st.write("\n")  # leave a blank space

                            st.subheader("9. Time-Series Analysis (Line Plot)")
                            st.info(
                                """
                                Use a line plot to visualise the changes in
                                GHG emissions across time.\n
                                Select the options from the left-side panel.
                                """
                            )
                            st.error(
                                """
                                BUG !! Cannot choose grouping factor.\n
                                Only numerical variables available for x-axis
                                as for Univariate Analysis.
                                """
                            )
                            st.sidebar.subheader("9. Time-Series Analysis")
                            perform_analysis_check = st.sidebar.checkbox(
                                label="Perform Time-Series Analysis",
                                value=False,
                            )
                            if perform_analysis_check:
                                group_time_series = st.sidebar.selectbox(
                                    label="Select a group/colour for graphing",
                                    options=pseudo_rep_aggregate_mean.columns,
                                    key=3,
                                )
                                st.sidebar.error(
                                    "BUG !! See main panel for details."
                                )

                                st.subheader(
                                    f"Table of Treatment Effect Means "
                                    f"(all CO2 treatments)"
                                )
                                # calculate aggregates with means AND stdev
                                # (for display only)
                                # use BOTH "Sampling_Date" AND "co2_treament"
                                # as grouping factors
                                st.write(
                                    """
                                    With 'Sampling_Date' AND all
                                    'co2_treatment'
                                    """
                                )
                                treatment_effect_aggregate_date_co2_mean_std = (
                                    pseudo_rep_aggregate_mean.groupby(
                                        # by=[group_time_series],
                                        by=["Sampling_Date", "co2_treatment",],
                                    )
                                    .aggregate(["mean", "std"])
                                    .reset_index()
                                )
                                st.table(
                                    treatment_effect_aggregate_date_co2_mean_std.head(
                                        10
                                    )
                                )

                                # calculate aggregates with means ONLY
                                # (save to file)
                                # use BOTH "Sampling_Date" AND "co2_treament"
                                # as grouping factors
                                treatment_effect_aggregate_date_co2_mean = (
                                    pseudo_rep_aggregate_mean.groupby(
                                        # by=[group_time_series],
                                        by=["Sampling_Date", "co2_treatment",],
                                    )
                                    .mean()
                                    .reset_index()
                                )
                                st.text(
                                    f"{treatment_effect_aggregate_date_co2_mean.shape[0]} rows and "
                                    f"{treatment_effect_aggregate_date_co2_mean.shape[1]} columns"
                                )
                                save_data_button = st.button(
                                    label="Save Mean Data"
                                )
                                if save_data_button:
                                    treatment_effect_aggregate_date_co2_mean.to_csv(
                                        f"C:/python_projects/exam_piscine_heroku_redone/"
                                        f"data/ghg_flux_data_stats_means.csv",
                                        sep=",",
                                        encoding="utf-8",
                                        na_rep="nan",
                                        header=True,
                                        index=True,
                                    )
                                    with st.spinner("Saving Data..."):
                                        time.sleep(1)
                                        st.success(
                                            """
                                            The aggregated means file was
                                            saved successfully.
                                            """
                                        )
                                        st.write("\n")

                                # calculate aggregates with means ONLY
                                # (save to file)
                                # use ONLY "Sampling_Date" as grouping factors
                                st.write(
                                    """
                                    With 'Sampling_Date' ONLY, i.e. CO2
                                    treatments averaged
                                    """
                                )
                                treatment_effect_aggregate_date_mean = (
                                    pseudo_rep_aggregate_mean.groupby(
                                        # by=[group_time_series],
                                        by=[
                                            "Sampling_Date",
                                            # "co2_treatment",
                                        ],
                                    )
                                    .mean()
                                    .reset_index()
                                )
                                st.table(
                                    treatment_effect_aggregate_date_mean.head(
                                        10
                                    )
                                )
                                st.text(
                                    f"{treatment_effect_aggregate_date_mean.shape[0]} rows and "
                                    f"{treatment_effect_aggregate_date_mean.shape[1]} columns"
                                )

                                # prepare a list of the dates for the x-axis
                                date_list = ghg_flux_data[
                                    "Sampling_Date"
                                ].unique()
                                st.write("List of sampling dates: \n")
                                st.write(date_list)

                                line_plot_check = st.checkbox(
                                    label="Show/Hide Graph",
                                    value=False,
                                    key=3,
                                )
                                if not line_plot_check:
                                    time_series_graph = px.line(
                                        treatment_effect_aggregate_date_mean,
                                        x=date_list,
                                        y=ghg_select,
                                        # hover_data={
                                        #     date_list.columns: "%Y, |%B, %d"
                                        # },
                                        title=f"{ghg_name} "
                                        f"Emissions Across Time",
                                    )
                                    time_series_graph.update_xaxes(
                                        title="Date",
                                        dtick="M1",
                                        tickformat="%b\n%Y",
                                        ticklabelmode="period",  # month NOT showin in center of period
                                        rangeslider_visible=True,
                                    )
                                    time_series_graph.update_yaxes(
                                        title=ghg_name + " Flux"
                                    )
                                    st.plotly_chart(time_series_graph)

                                # alternative figure (prettier)
                                fig, ax = plt.subplots(figsize=(28, 14))
                                time_series_chart = sns.lineplot(
                                    x=date_list,
                                    y=treatment_effect_aggregate_date_mean[
                                        ghg_select
                                    ],
                                    ax=ax,
                                )
                                time_series_chart.set_xlabel(
                                    xlabel="\nDate",
                                    weight="bold",
                                    fontsize=30,
                                )
                                time_series_chart.set_ylabel(
                                    ylabel=ghg_name + " Flux\n",
                                    weight="bold",
                                    fontsize=30,
                                )
                                time_series_chart.set_xticklabels(
                                    labels=treatment_effect_aggregate_date_mean[
                                        "Sampling_Date"
                                    ],
                                    rotation=45,
                                    horizontalalignment="right",
                                    fontsize=24,
                                )
                                # chart.set_yticklabels(
                                #     labels=ghg_flux_data["ch4_flux"],
                                #     fontsize=24
                                # )
                                time_series_chart.set_title(
                                    f"{ghg_name} Emissions Across Time\n",
                                    weight="bold",
                                    fontsize=36,
                                )
                                st.pyplot()

                                save_figure_button = st.button(
                                    label="Save Figure", key=3
                                )
                                if save_figure_button:
                                    st.error(
                                        "NOT working - saving a blank figure"
                                    )
                                    plt.savefig(
                                        f"C:/python_projects/exam_piscine_heroku_redone/"
                                        f"figures/time_series.png",
                                        # + plot_name +
                                        # ".png",
                                        dpi=100,
                                        bbox_inches="tight",
                                    )
                                    with st.spinner("Saving Figure..."):
                                        time.sleep(1)
                                        st.success(
                                            """
                                            The image file was saved
                                            successfully.
                                            """
                                        )
                                        st.write("\n")  # leave a blank space

                                # calculate aggregates for each
                                # "co2_treatment" only
                                st.subheader(
                                    "**Treatment** **Effect** **Grouping**"
                                )
                                treatment_groups = [
                                    group
                                    for group in ghg_flux_data[
                                        "co2_treatment"
                                    ].unique()
                                ]
                                treatment_groups = sorted(treatment_groups)
                                st.write(
                                    f"#### List of CO2 Treatment Groups: "
                                    f"\n{treatment_groups}\n"
                                )
                                st.write("\n")

                                st.write(
                                    f"#### GHG Fluxes under Ambient "
                                    f"Atmospheric CO2 (aCO2)"
                                )
                                st.write(
                                    f"Table of Treatment Effect Means "
                                    f"(aCO2 treatment only)"
                                )
                                ghg_flux_data_aco2 = (
                                    treatment_effect_aggregate_date_co2_mean_std[
                                        treatment_effect_aggregate_date_co2_mean_std[
                                            "co2_treatment"
                                        ]
                                        == "Ambient"
                                    ]
                                    .reset_index()
                                    .drop("index", axis=1)
                                )
                                st.table(ghg_flux_data_aco2.head(10))

                                # # NOT working
                                # # try refactor above code with ".query()"
                                # ghg_flux_data_aco2_query = (
                                #     treatment_effect_aggregate_date_co2_mean_std.query(
                                #     "co2_treatment == 'Ambient'", inplace=True
                                #     )
                                # )
                                # st.table(ghg_flux_data_aco2_query.head(10))

                                st.text(
                                    f"{ghg_flux_data_aco2.shape[0]} rows and "
                                    f"{ghg_flux_data_aco2.shape[1]} columns"
                                )
                                st.write("\n")
                                st.write(
                                    f"#### GHG Fluxes under Elevated "
                                    f"Atmospheric CO2 (eCO2)"
                                )
                                st.write(
                                    f"Table of Treatment Effect Means "
                                    f"(eCO2 treatment only)"
                                )
                                ghg_flux_data_eco2 = (
                                    treatment_effect_aggregate_date_co2_mean_std[
                                        treatment_effect_aggregate_date_co2_mean_std[
                                            "co2_treatment"
                                        ]
                                        == "Elevated"
                                    ]
                                    .reset_index()
                                    .drop("index", axis=1)
                                )
                                st.table(ghg_flux_data_eco2.head(10))
                                st.text(
                                    f"{ghg_flux_data_eco2.shape[0]} rows and "
                                    f"{ghg_flux_data_eco2.shape[1]} columns"
                                )
                                st.write("\n")  # leave a blank space

                                # # BUG NOT working !!
                                # # gives the following error message
                                # # "ValueError: The truth value of a DataFrame
                                # # is ambiguous. Use a.empty, a.bool(),
                                # # a.item(), a.any() or a.all()."
                                # st.write("#### eCO2 Analysis")
                                # st.write("\n")
                                # line_plot_check = st.checkbox(
                                #     label="Show/Hide Graph",
                                #     value=False,
                                #     key=3
                                # )
                                # if not line_plot_check:
                                #     time_series_graph = px.line(
                                #         ghg_flux_data_eco2,
                                #         x=date_list,
                                #         y=ghg_select,
                                #         title=
                                #             f"{ghg_name} Emissions "
                                #             f"Across Time",
                                #     )
                                #     time_series_graph.update_xaxes(
                                #         title="Date",
                                #         dtick="M1",
                                #         tickformat="%b\n%Y",
                                #         ticklabelmode="period",
                                #         rangeslider_visible=True,
                                #     )
                                #     time_series_graph.update_yaxes(
                                #         title=ghg_name + " Flux"
                                #     )
                                #     st.plotly_chart(time_series_graph)

                                # # alternative figure (prettier)
                                # # BUG NOT working !!
                                # # gives the following error message
                                # # "ValueError: could not broadcast input array
                                # # from shape (2) into shape (38)
                                # fig, ax = plt.subplots(figsize=(28, 14))
                                # time_series_chart = sns.lineplot(
                                #     x=date_list,
                                #     y=ghg_flux_data_eco2[ghg_select],
                                #     ax=ax,
                                # )
                                # time_series_chart.set_xlabel(
                                #     xlabel="\nDate",
                                #     weight="bold",
                                #     fontsize=30
                                # )
                                # time_series_chart.set_ylabel(
                                #     ylabel=ghg_name + " Flux\n",
                                #     weight="bold",
                                #     fontsize=30
                                # )
                                # time_series_chart.set_xticklabels(
                                #     labels=ghg_flux_data_eco2["Sampling_Date"],
                                #     rotation=45,
                                #     horizontalalignment="right",
                                #     fontsize=24,
                                # )
                                # # chart.set_yticklabels(
                                # #     labels=ghg_flux_data["ch4_flux"],
                                # #     fontsize=24
                                # # )
                                # time_series_chart.set_title(
                                #     f"{ghg_name} Emissions Across Time\n",
                                #     weight="bold",
                                #     fontsize=36,
                                # )
                                # st.pyplot()

                            st.subheader("10. Send results by e-mail")
                            st.info(
                                """
                                Select the files to compress and send by e-mail
                                from the left-side panel - INACTIVE
                                """
                            )
                            st.error(
                                """
                                BUG !! Cannot access "attachment_list" content
                                """
                            )
                            # to be done
                            st.sidebar.subheader("10. Finalise Results")
                            concat_files = ["test"]
                            select_file_check = st.sidebar.checkbox(
                                label="Select the files to e-mail - INACTIVE",
                                value=False,
                            )
                            if select_file_check:
                                attachment_select = st.sidebar.multiselect(
                                    label="Select the files to e-mail",
                                    options=concat_files,
                                    key=3,
                                )
                                st.sidebar.error(
                                    "BUG !! See main panel for details."
                                )

                                # # BUG cannot access "attachment_list" content
                                # attachment_list = [
                                #     # pseudo_rep_aggregate_mean,
                                #     # treatment_effect_aggregate_mean,
                                #     treatment_effect_aggregate_mean_std,
                                # ]
                                # # alternative to above code
                                # attachment_list = [
                                #     f"C:/python_projects/exam_piscine_heroku_redone/"
                                #     f"data/ghg_flux_data_stats.csv",
                                #     f"C:/python_projects/exam_piscine_heroku_redone/"
                                #     f"data/ghg_flux_data_stats_mean.csv",
                                # ]
                                # # or, using the .multiselect() method
                                # attachment_select = st.multiselect(
                                #     label=
                                #         f"Select the files to be e-mailed - "
                                #         f"INACTIVE !!",
                                #     options=attachment_list,
                                # )
                            attachment_select = (
                                f"C:/python_projects/exam_piscine_heroku_redone/"
                                f"data/ghg_flux_data_stats.csv"
                            )
                            send_email_button = st.button(label="Send e-mail")
                            if send_email_button:
                                EMAIL_ADDRESS = "loicnazaries@googlemail.com"
                                # if "EMAIL_PASSWORD" lost, generate a new one
                                EMAIL_PASSWORD = "tfuwdfzrcspruqbs"

                                message = EmailMessage()
                                message[
                                    "Subject"
                                ] = "GHG Estimation Portal - EDA report"
                                message["From"] = EMAIL_ADDRESS
                                message["To"] = ["loicnazaries@yahoo.fr"]
                                message.set_content(
                                    """
                                        <!DOCTYPE html>
                                        <html>
                                            <body>
                                                <div style="background-color:#eee;padding:10px 20px;">
                                                    <h2 style="font-family:Georgia, 'Times New Roman',
                                                    Times, serif;color#454349;">My newsletter</h2>
                                                </div>
                                                <div style="padding:20px 0px">
                                                    <div style="height: 500px;width:400px">
                                                        <img src=
                                                        "https://dummyimage.com/500x300/000/fff&text=Dummy+image"
                                                        style="height: 300px;">
                                                        <div style="text-align:center;">
                                                            <h3>Article 1</h3>
                                                            <p>Lorem ipsum dolor sit amet consectetur,
                                                            adipisicing elit. A ducimus deleniti nemo
                                                            quibusdam iste sint!</p>
                                                            <a href="#">Read more</a>
                                                        </div>
                                                    </div>
                                                </div>
                                            </body>
                                        </html>
                                        """,
                                    subtype="html",
                                )
                                # cannot send attachmentS from a list
                                with open(attachment_select, "rb",) as csv:
                                    message.add_attachment(
                                        csv.read(),
                                        maintype="application",
                                        # subtype="octet-stream",
                                        subtype="csv",
                                    )
                                with smtplib.SMTP_SSL(
                                    "smtp.gmail.com", 465
                                ) as smtp:
                                    smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                                    smtp.send_message(message)
                                with st.spinner("Sending e-mail..."):
                                    time.sleep(1)
                                    st.success(
                                        """
                                        An e-mail was successfully sent to
                                        your mail box.\n
                                        (Only sent to 'loicnazaries@yahoo.fr'
                                        for now).
                                        """
                                    )
                                    st.balloons()

                            st.subheader("11. App Deployment")
                            # heroku

                        elif analysis_select == "Statistics":
                            st.title("Statistical analysis")
                            st.error("Page under construction.")

                        elif analysis_select == "EucFACE Site Presentation":
                            st.title(
                                f"Analysis of greenhouse gas (GHG) emissions "
                                f"under elevated atmospheric CO2 concentrations"
                            )
                            st.header("Presentation of the EucFACE Experiment")
                            st.subheader("Background")
                            background = st.beta_expander("Show/Hide Details")
                            background.markdown(
                                """
                                Greenhouse gas (GHG) emissions associated
                                with human activities are well known to be
                                the major contributors to climate change
                                worldwide ([IPCC, 2013]
                                (http://www.climatechange2013.org/images/report/WG1AR5_ALL_FINAL.pdf)).
                                >> These include:
                                > - carbon dioxide (CO<sub>2</sub>)  # BUG
                                > - methane (CH4)
                                > - nitrous oxide (N2O).

                                While the concentration of these gases continue
                                to rise, forest ecosystems have been recently
                                proposed as a natural solution to climate
                                change (Griscom *et* *al*., 2017 [1];
                                Fargione *et* *al*., 2018 [2]) because of their
                                significant capacity to sequestrate atmospheric
                                carbon (C) within the soil profile and
                                aboveground vegetation (Le Quéré *et* *al*.,
                                2018 [3]).\n
                                Past research has also revealed that current
                                atmospheric CO2 levels could increase by about
                                150 ppm before the year 2100 (Stocker *et*
                                *al*., 2013 [4]). The increase of CO2 level in
                                the atmosphere is largely expected to promote
                                a greening effect (*i.e.* plant growth)
                                in forests globally, however, given the
                                concomitant expected global increase in
                                droughts and aridity levels, such CO2
                                fertilisation effect is under debate due to
                                increased water limitation feedback effects
                                (Brodribb *et* *al*., 2020 [5]).
                                """
                            )
                            st.subheader("The EucFACE Experiment")
                            eucface = st.beta_expander("Show/Hide Details")
                            eucface.markdown(
                                """
                                The *Eucalyptus* Free-Air CO2 Enrichment
                                (EucFACE) experiment at Western Sydney
                                University, near Richmond, New South Wales,
                                Australia (33°37’S, 150°44’E, 23 m altitude)
                                represents a unique facility for studying the
                                effect of elevated atmospheric CO2
                                concentration on a remnant Cumberland Plain
                                Woodland. A detailed description of the site,
                                including vegetation and soil characteristics,
                                can be found elsewhere (Crous *et* *al*., 2015
                                [6]; Drake *et* *al*., 2016 [7]; Gimeno *et*
                                *al*., 2016 [8]).\n
                                The EucFACE is composed of six circular plots
                                (henceforth called “rings”), 25 m in diameter
                                and 28 m high. Mature old-growth
                                (> 75-year-old) *Eucalyptus tereticornis* is
                                the dominant species; however, the understorey
                                vegetation varies significantly between rings
                                (Hasegawa *et* *al*., 2018 [9]).
                                Three rings are used as control and are
                                fumigated with ambient air (aCO2) while the
                                other three rings are fumigated with elevated
                                CO2 concentrations (eCO2). Fumigation with CO2
                                is set to 150 ppm above that of the control
                                rings (ambient + 150 ppm) in order to simulate
                                the climate prediction for the year 2100
                                (Stocker *et* *al*., 2013 [4]). Fumigation
                                started in September 2012 with +30 ppm CO2
                                and was ramped periodically for six months
                                (+30 ppm every 4-5 weeks) until February 2013
                                (540 ppm).
                                """
                            )
                            st.write("\n")  # leave a blank space
                            st.video(
                                "https://www.youtube.com/watch?v=K8RTVdijc0o",
                                start_time=0,
                            )
                            # note: fit images on 2x2 quadrant
                            image_0 = Image.open(
                                f"C:/Users/loicn/Google Drive "
                                f"(loic.nazaries@lapiscine.pro)/"
                                f"Projet pro/Présentation/EucFACE.jpg"
                            )
                            st.image(
                                image_0,
                                caption="Bird view of the 6 rings at EucFACE",
                                use_column_width=True,
                            )
                            st.subheader("Aims & Hypotheses")
                            aims = st.beta_expander("Show/Hide Details")
                            aims.markdown(
                                """
                                Here, we conducted monthly measurements of
                                (*in situ*) net CH4, N2O and CO2 fluxes from
                                May 2013 to June 2016 to investigate the
                                effects of elevated atmospheric CO2 (ambient
                                *vs*. +150 ppm) concentrations on soil net
                                CH4, N2O and CO2 fluxes from a mature
                                Eucalypt woodland in New South Wales,
                                Australia. The *Eucalyptus* Free-Air CO2
                                Enrichment (EucFACE) experiment is a unique
                                research station established in 2012 in an
                                Australian endangered woodland ecosystem (the
                                Cumberland Plain).\n
                                The main aims of the present study were to:\n
                                1. Quantify the net CH4, N2O and CO2 fluxes
                                under predicted elevated CO2 (eCO2)
                                concentrations\n
                                2. Identify which climo-edaphic factors could
                                best predict soil GHG emissions\n
                                We considered three different alternative
                                hypotheses:\n
                                1. In mature forest, the feedback response of
                                GHG fluxes to eCO2 will be minimal. The reason
                                is that in old forests, trees are not expected
                                to absorb large amount of CO2 (*vs*. plant
                                growing phase), leading to reduced responses
                                for ecosystem processes such as gas emissions\n
                                2. The response (sink or production) of each
                                GHG investigated to eCO2 treatment will differ,
                                with an expected increase of CO2 and
                                N2O emissions while CH4 flux rates will be
                                reduced\n
                                3. The magnitude of the GHG emissions will be
                                strongly linked to climo-edaphic properties,
                                such as rainfall events and soil water
                                availability as it is responsible for
                                regulating soil biological processes,
                                particularly in water-limited environments.
                                """
                            )
                            st.subheader("Experimental Setup")
                            st.write("### Greenhouse gas measurements")
                            experiment = st.beta_expander("Show/Hide Details")
                            experiment.markdown(
                                """
                                The collection of air samples for GHG analysis
                                was conducted monthly, from seven collars
                                permanently inserted into the ground,
                                within each ring. The GHG sampling campaigns
                                occurred over three years, between May 2013 to
                                June 2016 (no sampling took place in May 2015),
                                in a total of 37 monthly collections. More
                                details related to the sampling strategy can
                                be found in the supporting information
                                section.\n
                                The measurement of the net GHG fluxes between
                                soil and atmosphere was estimated using a
                                “static chamber method”, or non-flow-through
                                non-steady-state (Rochette & Eriksen-Hamel,
                                2008 [10]). Throughout the course of the
                                experiment (chamber design, sample collection
                                and analysis, data processing), guidelines from
                                de Klein *et* *al*. (2012) [11] were followed.
                                Briefly, a 25 ml air sample was collected from
                                the chamber headspace (chamber characteristics:
                                diameter ≈ 20 cm; height above ground ≈ 11 cm;
                                headspace volume ≈ 5 L; soil insertion
                                depth ≈ 7 cm) during a 45-minute deployment
                                time and at four time points (tamb, t15, t30
                                and t45), see supporting information section
                                for further details. The concentrations of
                                CH4, N2O and CO2 were detected on a gas
                                chromatography system against a seven-point
                                serial dilution of a GHG standard mixture
                                (5 ppm CH4, 600 ppm CO2 and 1 ppm N2O).
                                Detailed gas chromatography system
                                characteristics and chamber design are in
                                supporting information.\n
                                The GHG concentrations were converted from
                                ppm values to mass-based concentrations using
                                a conversion factor derived from the ideal gas
                                law (PV = nRT), where an air pressure P of 1
                                atm was assumed and an universal gas constant
                                R of 0.082057 L atm/K/mol. After including
                                the chamber dimensions (headspace volume V,
                                chamber’s base area A) and the corresponding
                                molecular masses, the final flux units were
                                μg-C(N) m-2 h-1 for CH4 and N2O, and
                                mg-C m-2 h-1 for CO2. Greenhouse gas fluxes
                                reported as negative represent net sinks
                                (flux from atmosphere to soil).
                                """
                            )
                            st.markdown(
                                f"#### Illustration of the headspace volume "
                                f"sampling method"
                            )
                            # add "beta_columns" for "image_1" & "image_2"
                            st.write("\n")  # leave a blank space
                            image_1 = Image.open(
                                f"C:/Users/loicn/Google Drive "
                                f"(loic.nazaries@lapiscine.pro)/"
                                f"Projet pro/Présentation/DSC00926.jpg"
                            )
                            st.image(
                                image_1,
                                caption="Air Sampling Chamber",
                                use_column_width=True,
                            )
                            image_2 = Image.open(
                                f"C:/Users/loicn/Google Drive "
                                f"(loic.nazaries@lapiscine.pro)/"
                                f"Projet pro/Présentation/DSC01216.jpg"
                            )
                            st.image(
                                image_2,
                                caption="""
                                    Sampling Headspace Volume using a Siringe
                                    and a Sampling Port
                                    """,
                                use_column_width=True,
                            )
                            st.write("### References")
                            references = st.beta_expander("Show/Hide Details")
                            references.markdown(
                                """
                                [1]: Griscom, B.W., Adams, J., Ellis, P.W., Houghton, R.A., Lomax, G., Miteva, D.A., Schlesinger, W.H., Shoch, D., Siikamäki, J. V, Smith, P., Woodbury, P., Zganjar, C., Blackman, A., Campari, J., Conant, R.T., Delgado, C., Elias, P., Gopalakrishna, T., Hamsik, M.R., Herrero, M., Kiesecker, J., Landis, E., Laestadius, L., Leavitt, S.M., Minnemeyer, S., Polasky, S., Potapov, P., Putz, F.E., Sanderman, J., Silvius, M., Wollenberg, E., Fargione, J., 2017. Natural climate solutions. Proceedings of the National Academy of Sciences 114, 11645 LP – 11650. doi:10.1073/pnas.1710465114\n
                                [2]: Fargione, J.E., Bassett, S., Boucher, T., Bridgham, S.D., Conant, R.T., Cook-Patton, S.C., Ellis, P.W., Falcucci, A., Fourqurean, J.W., Gopalakrishna, T., Gu, H., Henderson, B., Hurteau, M.D., Kroeger, K.D., Kroeger, T., Lark, T.J., Leavitt, S.M., Lomax, G., McDonald, R.I., Megonigal, J.P., Miteva, D.A., Richardson, C.J., Sanderman, J., Shoch, D., Spawn, S.A., Veldman, J.W., Williams, C.A., Woodbury, P.B., Zganjar, C., Baranski, M., Elias, P., Houghton, R.A., Landis, E., McGlynn, E., Schlesinger, W.H., Siikamaki, J. V, Sutton-Grier, A.E., Griscom, B.W., 2018. Natural climate solutions for the United States. Science Advances 4, eaat1869. doi:10.1126/sciadv.aat1869\n
                                [3]: Le Quéré, C., Moriarty, R., Andrew, R.M., Peters, G.P., Ciais, P., Friedlingstein, P., Jones, S.D., Sitch, S., Tans, P., Arneth, A., 2015. Global carbon budget 2014. Earth System Science Data 7, 47–85\n
                                [4]: Stocker, T., Qin, D., Plattner, G., Tignor, M., Allen, S., Boschung, J., Nauels, A., Xia, Y., Bex, B., Midgley, B., 2013. IPCC 2013: Climate Change 2013, The Physical Science Basis. Contribution of Working Group I to the Fifth Assessment Report to the Intergovernmental Panel on Climate Change. Cambridge University Press, Cambridge, United Kingdom and New York, NY, USA\n
                                [5]: Brodribb, T.J., Powers, J., Cochard, H., Choat, B., 2020. Hanging by a thread? Forests and drought. Science 368, 261–266\n
                                [6]: Crous, K.Y., Ósvaldsson, A., Ellsworth, D.S., 2015. Is phosphorus limiting in a mature Eucalyptus woodland? Phosphorus fertilisation stimulates stem growth. Plant and Soil 391, 293–305. doi:10.1007/s11104-015-2426-4\n
                                [7]: Drake, J.E., Macdonald, C.A., Tjoelker, M.G., Crous, K.Y., Gimeno, T.E., Singh, B.K., Reich, P.B., Anderson, I.C., Ellsworth, D.S., 2016. Short-term carbon cycling responses of a mature eucalypt woodland to gradual stepwise enrichment of atmospheric CO2 concentration. Global Change Biology 22, 380–390. doi:10.1111/gcb.13109\n
                                [8]: Gimeno, T.E., Crous, K.Y., Cooke, J., O’Grady, A.P., Ósvaldsson, A., Medlyn, B.E., Ellsworth, D.S., 2016. Conserved stomatal behaviour under elevated CO2 and varying water availability in a mature woodland. Functional Ecology 30, 700–709. doi:10.1111/1365-2435.12532\n
                                [9]: Hasegawa, S., Piñeiro, J., Ochoa‐Hueso, R., Haigh, A.M., Rymer, P.D., Barnett, K.L., Power, S.A., 2018. Elevated CO2 concentrations reduce C4 cover and decrease diversity of understorey plant community in a Eucalyptus woodland. Journal of Ecology 106, 1483–1494\n
                                [10]: Rochette, P., Eriksen-Hamel, N.S., 2008. Chamber Measurements of Soil Nitrous Oxide Flux: Are Absolute Values Reliable? Soil Science Society of America Journal 72, 331–342. doi:10.2136/sssaj2007.0215\n
                                [11]: De Klein, C.A.M., Harvey, M., 2012. Nitrous oxide chamber methodology guidelines. Global Research Alliance on Agricultural Greenhouse Gases, Ministry for Primary Industries: Wellington, New Zealand\n
                                """
                            )

                else:
                    st.warning("Incorrect User name and/or Password")

            elif not log_checkbox:
                st.info("You are now logged out.")

    elif page == "Admin":
        st.title("Admin's Corner")
        st.sidebar.write("### Admin Login")
        admin_name = st.sidebar.text_input(label="Admin Name")
        admin_password = st.sidebar.text_input(
            label="Enter Admin Password", type="password"
        )
        admin_log_checkbox = st.sidebar.checkbox(
            label="Log In/Log Out", value=False
        )
        if admin_log_checkbox:
            # refactor command below to handle admin's secret keys & password
            if (admin_name == "admin") & (admin_password == "password"):
                st.success("Welcome Administrator!")
                st.info(
                    """
                    Here the administrator can add user's details
                    (name and password) manually.
                    """
                )
                # add user's details
                add_new_user_name = st.text_input(label="Add New User Name")
                add_new_user_password = st.text_input(
                    label="Add New User Password (e-mail address)"
                )
                submit_button = st.button(label="Save User's Details")
                if submit_button:
                    add_user_data(
                        add_new_user_name, make_hashes(add_new_user_password)
                    )
                    with st.spinner("Saving User Details..."):
                        time.sleep(1)
                        st.success("A New User Was Added")
                st.header("User Profiles")
                user_profile = view_all_users()
                clean_db = pd.DataFrame(
                    user_profile, columns=["User Name", "User Password"],
                )
                st.dataframe(clean_db)

            else:
                st.warning("Incorrect User name and/or Password")
        elif not admin_log_checkbox:
            st.info("You are now logged out.")


select_page()


# if __name__ == "__main__":
#     main()
