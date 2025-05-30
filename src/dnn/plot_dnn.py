import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path

from collections import OrderedDict

linestyles = OrderedDict(
    [('solid', (0, ())),
     ('loosely dotted', (0, (1, 10))),
     ('dotted', (0, (1, 5))),
     ('densely dotted', (0, (1, 1))),

     ('loosely dashed', (0, (5, 10))),
     ('dashed', (0, (5, 5))),
     ('densely dashed', (0, (5, 1))),

     ('loosely dashdotted', (0, (3, 10, 1, 10))),
     ('dashdotted', (0, (3, 5, 1, 5))),
     ('densely dashdotted', (0, (3, 1, 1, 1))),

     ('loosely dashdotdotted', (0, (3, 10, 1, 10, 1, 10))),
     ('dashdotdotted', (0, (3, 5, 1, 5, 1, 5))),
     ('densely dashdotdotted', (0, (3, 1, 1, 1, 1, 1)))])

visualization_spec = {
    "mps": {"color": "#36FF33", "marker": "s", "linestyle": "dotted", "label": "MPS", "markersize": 12},
    "pm_lb": {"color": "#B6C800", "marker": "^", "linestyle": "dashed", "label": "$PA_{C\searrow}$", "markersize": 12},
    "pm_ub": {"color": "#f119c3", "marker": "v", "linestyle": "dotted", "label": r"$PA_{C\nearrow}$", "markersize": 12},
    "ipdd": {"color": "#0d5915", "marker": "2", "linestyle": linestyles['densely dashed'],
             "label": "IPDD",
             "markersize": 15},
    "gdpa": {"color": "#E31D1D", "marker": "o", "linestyle": "dashdot", "label": "GDPA", "markersize": 7},
    "pga": {"color": "#1c24dc", "marker": "*", "linestyle": "solid", "label": "PGA", "markersize": 10}}

visualization_spec_init = {
    "mps": {"color": "#36FF33", "marker": "s", "linestyle": "solid", "label": r"$MPS(\mathbf{x}^0_{max})$",
            "markersize": 12},
    "pm_lb_init_25_25_25_25_25": {"color": "#B6C800", "marker": "^", "linestyle": "solid",
                                  "label": r"$PM_{C\searrow}(\mathbf{x}^0_{max})$", "markersize": 12},
    "pm_ub_init_25_25_25_25_25": {"color": "#f119c3", "marker": "v", "linestyle": "solid",
                                  "label": r"$PM_{C\nearrow}(\mathbf{x}^0_{max})$", "markersize": 12},
    "ipdd_init_25_25_25_25_25": {"color": "#0d5915", "marker": "2", "linestyle": "solid",
                                 "label": r"$IPDD(\mathbf{x}^0_{max})$",
                                 "markersize": 15},
    "gdpa_init_25_25_25_25_25": {"color": "#E31D1D", "marker": "o", "linestyle": "solid",
                                 "label": r"$GDPA(\mathbf{x}^0_{max})$",
                                 "markersize": 10},
    "gdpa_init_20_20_20_20_20": {"color": "#df6f67", "marker": "o", "linestyle": linestyles["loosely dotted"],
                                 "label": r"$GDPA(\mathbf{x}^0_1)$", "markersize": 6},
    "gdpa_init_10_10_10_10_10": {"color": "#dea39f", "marker": "o", "linestyle": linestyles["loosely dashed"],
                                 "label": r"$GDPA(\mathbf{x}^0_2)$", "markersize": 6},
    "pga_init_25_25_25_25_25": {"color": "#1c24dc", "marker": "*", "linestyle": "solid",
                                "label": r"$PGA(\mathbf{x}^0_{max})$",
                                "markersize": 10},
    "pga_init_20_20_20_20_20": {"color": "#595fdc", "marker": "*", "linestyle": linestyles["loosely dotted"],
                                "label": r"$PGA(\mathbf{x}^0_1)$", "markersize": 6},
    "pga_init_10_10_10_10_10": {"color": "#9598dc", "marker": "*", "linestyle": linestyles["loosely dashed"],
                                "label": r"$PGA(\mathbf{x}^0_2)$", "markersize": 6}}


def objective_value_dnn(num_con, T, opt_name, path, path_w, function_name, freq_s):
    plt.figure(figsize=(8, 6))
    opts = {}
    for opt in opt_name:
        data = pd.read_json(path.joinpath(opt + ".json"))
        freq_elem = int(len(data) / (T / freq_s))
        if freq_elem > 0:
            data = data.iloc[::freq_elem, :]
        opts[opt] = data
    # objective function
    # plt.figure(figsize=(10, 5))
    for opt in opt_name:
        plt.plot(
            opts[opt]["runtime"],
            opts[opt]["J"],
            color=visualization_spec[opt]["color"],
            marker=visualization_spec[opt]["marker"],
            linestyle=visualization_spec[opt]["linestyle"],
            label=visualization_spec[opt]["label"],
            markersize=visualization_spec[opt]["markersize"],
        )
        if opt in ["pm_lb", "pm_ub"]:
            plt.axhline(
                y=opts[opt]["J"][0],
                xmin=opts[opt]["runtime"][0] / (T),
                xmax=1,
                color=visualization_spec[opt]["color"],
                linestyle=visualization_spec[opt]["linestyle"], )
        elif opt == "mps":
            plt.axhline(
                y=opts[opt]["J"][0],
                xmin=0,
                xmax=1,
                color=visualization_spec[opt]["color"],
                linestyle=visualization_spec[opt]["linestyle"], )
    plt.xlim([0, T])
    plt.ylim([1800, 2450])
    # plt.ylim([lower_bound, upper_bound])
    # plt.yscale("log")
    plt.legend(loc="upper right")
    plt.xlabel("Computational time [s]", fontsize=15)
    plt.ylabel(r"Objective value [€]", fontsize=15)
    plt.grid()
    plt.savefig(path_w.joinpath("objective_value_" + function_name + ".svg"), format='svg')
    plt.savefig(path_w.joinpath("objective_value_" + function_name + ".eps"), format='eps')
    plt.show()


def constraint_violation_dnn(num_con, T, q, opt_name, path, path_w, function_name, freq_s):
    plt.figure(figsize=(8, 6))
    opts = {}
    for opt in opt_name:
        data = pd.read_json(path.joinpath(f"{opt}.json"))[["f", "runtime"]]
        freq_elem = int(len(data) / (T / freq_s))
        if freq_elem > 0:
            data = data.iloc[::freq_elem, :]
        opts[opt] = {"runtime": data["runtime"].tolist(), "f": []}
        f = data["f"].tolist()
        for i in range(len(f)):
            opts[opt]["f"].append(abs(min(0, min(f[i]))))
        # opts[opt]["f"] = calculate_max_percent_f_and_q(f, q)
    # objective function
    # plt.figure(figsize=(10, 5))
    for opt in opt_name:
        plt.plot(
            opts[opt]["runtime"],
            opts[opt]["f"],
            color=visualization_spec[opt]["color"],
            marker=visualization_spec[opt]["marker"],
            linestyle=visualization_spec[opt]["linestyle"],
            label=visualization_spec[opt]["label"],
            markersize=visualization_spec[opt]["markersize"],
        )
        if opt in ["pm_lb", "pm_ub"]:
            plt.axhline(
                y=opts[opt]["f"][0],
                xmin=opts[opt]["runtime"][0] / (T),
                xmax=1,
                color=visualization_spec[opt]["color"],
                linestyle=visualization_spec[opt]["linestyle"], )
        elif opt == "mps":
            plt.axhline(
                y=opts[opt]["f"][0],
                xmin=0,
                xmax=1,
                color=visualization_spec[opt]["color"],
                linestyle=visualization_spec[opt]["linestyle"], )
    plt.xlim([0, T])
    # plt.yscale("log")
    # plt.ylim([lower_bound, upper_bound])
    plt.legend(loc="upper right")
    plt.xlabel("Computational time [s]", fontsize=15)
    plt.ylabel("Constraint violation [MW]", fontsize=15)
    plt.grid()
    plt.savefig(path_w.joinpath("constraint_violations_" + function_name + ".svg"), format='svg')
    plt.savefig(path_w.joinpath("constraint_violations_" + function_name + ".eps"), format='eps')
    plt.show()


def parameter_C(opt_names, T, Cs, path_r, path_w):
    # Define colors and styles
    opts = ["#36FF33", "#B6C800", "#f119c3", "#0d5915", "#E31D1D", "#1c24dc"]
    if len(opts) < len(Cs):
        raise ValueError("The number of parameters C must be at least equal to the number of C values.")
    colors = {}
    for i, C in enumerate(Cs):
        colors[str(C)] = opts[i]
    styles = {
        'pm': {'linestyle': '--', 'marker': 'o', "markersize": 7},
        'pga': {'linestyle': '-', 'marker': '*', "markersize": 10}
    }

    plt.figure(figsize=(12, 6))

    # First set of lines for C values
    for C in Cs:
        for opt_name in opt_names:
            filename = f"{opt_name}_{C}.json"
            filepath = path_r.joinpath(filename)

            data = pd.read_json(filepath)

            plt.plot(data["runtime"], data["J"],
                     color=colors[str(C)],
                     **styles[opt_name])
            if opt_name == "pm":
                plt.axhline(
                    y=data["J"][0],
                    xmin=data["runtime"][0] / (T),
                    xmax=1,
                    color=colors[str(C)],
                    linestyle=styles[opt_name]["linestyle"])

    # Create legend for C values
    C_legend = [plt.Line2D([0], [0], color=colors[str(C)], lw=2, label=f'C={C}') for C in Cs]

    # Create legend for optimizers
    opt_legend = [plt.Line2D([0], [0], **styles[opt], color='black', label=visualization_spec[opt]["label"]) for opt in
                  opt_names]

    # Add C values legend
    first_legend = plt.legend(handles=C_legend, title='C values', loc='upper left')
    plt.gca().add_artist(first_legend)

    # Add Optimizers legend
    plt.legend(handles=opt_legend, title='Optimizers', loc='upper right')

    plt.xlabel("Computational time [s]", fontsize=15)
    plt.ylabel("Objective value", fontsize=15)
    plt.xlim([0, T])
    plt.grid()
    plt.savefig(path_w.joinpath("objective_value_parameter_C_" + ".svg"), format='svg')
    plt.show()

    plt.figure(figsize=(12, 6))

    # First set of lines for C values
    for C in Cs:
        for opt_name in opt_names:
            filename = f"{opt_name}_{C}.json"
            filepath = path_r.joinpath(filename)

            data = pd.read_json(filepath)
            constraint_violations = []
            f = data["f"].tolist()
            for i in range(len(f)):
                constraint_violations.append(abs(min(0, min(f[i]))))

            plt.plot(data["runtime"], constraint_violations,
                     color=colors[str(C)],
                     **styles[opt_name])
            if opt_name == "pm":
                plt.axhline(
                    y=constraint_violations[0],
                    xmin=data["runtime"][0] / (T),
                    xmax=1,
                    color=colors[str(C)],
                    linestyle=styles[opt_name]["linestyle"])

    # Create legend for C values
    C_legend = [plt.Line2D([0], [0], color=colors[str(C)], lw=2, label=f'C={C}') for C in Cs]

    # Create legend for optimizers
    opt_legend = [plt.Line2D([0], [0], **styles[opt], color='black', label=visualization_spec[opt]["label"]) for opt in
                  opt_names]

    # Add C values legend
    first_legend = plt.legend(handles=C_legend, title='C values', loc='upper left')
    plt.gca().add_artist(first_legend)

    # Add Optimizers legend
    plt.legend(handles=opt_legend, title='Optimizers', loc='upper right')

    plt.xlabel("Computational time [s]", fontsize=15)
    plt.ylabel("Constraint violation", fontsize=15)
    plt.xlim([0, T])
    plt.grid()
    plt.savefig(path_w.joinpath("constraint_violations_parameter_C_" + ".svg"), format='svg')
    plt.show()


def plot():
    objective_value_dnn(num_con=1, T=500, opt_name=["mps", "pm_lb", "pm_ub", "ipdd", "gdpa", "pga"],
                        path=Path("../data/dnn").joinpath(""),
                        path_w=Path("../plots/dnn").joinpath(""), function_name="dnn",
                        freq_s=10)

    constraint_violation_dnn(num_con=1, T=500, q=[0], opt_name=["mps", "pm_lb", "pm_ub", "ipdd", "gdpa", "pga"],
                             path=Path("../data/dnn").joinpath(""),
                             path_w=Path("../plots/dnn").joinpath(""), function_name="dnn",
                             freq_s=10)
    # parameter_C(opt_names=["pm", "pga"], T=500, Cs=[1, 0.75, 0.5, 0.25, 0.1],
    #            path_r=Path("../../data/dnn").joinpath("parameter_C"),
    #            path_w=Path("../../plots/dnn"))


if __name__ == "__main__":
    plot()
