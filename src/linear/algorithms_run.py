from src.linear.eval import *
from src.linear.algorithms import *
from src.helpers import *


def run(functions):
    for function in functions:
        path: Path = Path("../data").joinpath(function)
        problem_spec = get_problem_spec(function)
        grad_spec = get_grad_spec(function)
        eval_spec = get_eval_spec(function)
        mps_dict, pm_lb_dict, pm_ub_dict, ipdd_dict, gdpa_dict, pga_dict = {}, {}, {}, {}, {}, {}
        var_mps, J_mps, constraint_values_mps, runtime_mps = mps(num_var=problem_spec["num_var"],
                                                                 num_con=problem_spec["num_con"], c=problem_spec["c"],
                                                                 q=problem_spec["q"],
                                                                 ub=problem_spec["ub"], lb=problem_spec["lb"],
                                                                 T=problem_spec["T"])
        save(dict_=mps_dict, J=J_mps, f=constraint_values_mps, runtime=runtime_mps, path=path, name="mps", vars=var_mps)
        J_pm_lb, constraint_values_pm_lb, var_pm_lb, runtime_pm_lb = standard_penalty_alg(
            num_var=problem_spec["num_var"],
            num_con=problem_spec["num_con"],
            c=problem_spec["c"],
            q=problem_spec["q"],
            ub=problem_spec["ub"],
            lb=problem_spec["lb"],
            C=grad_spec["C"],
            initial_vector=grad_spec[
                "initial_vector"],
            delta=grad_spec["delta"],
            patience=grad_spec["patience"],
            grad_iter_max=grad_spec[
                "grad_iter_max"])
        save(dict_=pm_lb_dict, J=J_pm_lb, f=constraint_values_pm_lb, runtime=runtime_pm_lb, path=path,
             name="pm_lb", vars=var_pm_lb)
        J_pm_ub, constraint_values_pm_ub, var_pm_ub, runtime_pm_ub = standard_penalty_alg(
            num_var=problem_spec["num_var"],
            num_con=problem_spec["num_con"],
            c=problem_spec["c"],
            q=problem_spec["q"],
            ub=problem_spec["ub"],
            lb=problem_spec["lb"], C=grad_spec["C_large"],
            initial_vector=grad_spec[
                "initial_vector"],
            delta=grad_spec["delta"],
            patience=grad_spec["patience"],
            grad_iter_max=grad_spec[
                "grad_iter_max"])
        save(dict_=pm_ub_dict, J=J_pm_ub, f=constraint_values_pm_ub, runtime=runtime_pm_ub, path=path,
             name="pm_ub", vars=var_pm_ub)
        J_ipdd, constraint_values_ipdd, var_ipdd, runtime_ipdd = ipdd(
            num_var=problem_spec["num_var"],
            num_con=problem_spec["num_con"],
            c=problem_spec["c"],
            q=problem_spec["q"], ub=problem_spec["ub"],
            lb=problem_spec["lb"], T=problem_spec["T"],
            rho=1,
            initial_vector=grad_spec["initial_vector"],
            initial_lambdas=grad_spec["initial_lambdas"],
            grad_iter_max=grad_spec["grad_iter_max"])
        save(dict_=ipdd_dict, J=J_ipdd, f=constraint_values_ipdd, runtime=runtime_ipdd, path=path, name="ipdd",
             vars=var_ipdd)
        J_gdpa, constraint_values_gdpa, var_gdpa, runtime_gdpa = gdpa(num_var=problem_spec["num_var"],
                                                                      num_con=problem_spec["num_con"],
                                                                      c=problem_spec["c"], q=problem_spec["q"],
                                                                      ub=problem_spec["ub"],
                                                                      lb=problem_spec["lb"],
                                                                      T=problem_spec["T"],
                                                                      initial_vector=grad_spec["initial_vector"],
                                                                      initial_lambdas=grad_spec["initial_lambdas"],
                                                                      step_size_init=grad_spec["step_size"],
                                                                      perturbation_term=grad_spec["perturbation_term"],
                                                                      beta_init=grad_spec["beta"],
                                                                      gamma=grad_spec["gamma"])
        save(dict_=gdpa_dict, J=J_gdpa, f=constraint_values_gdpa, runtime=runtime_gdpa, path=path, name="gdpa",
             vars=var_gdpa)
        J_pga, constraint_values_pga, var_pga, runtime_pga = pga(num_var=problem_spec["num_var"],
                                                                 num_con=problem_spec["num_con"],
                                                                 c=problem_spec["c"],
                                                                 q=problem_spec["q"], ub=problem_spec["ub"],
                                                                 lb=problem_spec["lb"], T=problem_spec["T"],
                                                                 C=grad_spec["C"],
                                                                 initial_vector=grad_spec["initial_vector"],
                                                                 delta=grad_spec["delta"],
                                                                 patience=grad_spec["patience"],
                                                                 grad_iter_max=grad_spec["grad_iter_max"])
        save(dict_=pga_dict, J=J_pga, f=constraint_values_pga, runtime=runtime_pga, path=path, name="pga", vars=var_pga)
        initialization(problem_spec, grad_spec, initial_vectors=eval_spec["initial_vectors"],
                       path=path.joinpath("initialization"))
        parameter_C(problem_spec=problem_spec, grad_spec=grad_spec, Cs=eval_spec["Cs"],
                    path=path.joinpath("parameter_C"))
        evaluate_gdpa(problem_spec=problem_spec, grad_spec=grad_spec, beta_inits=[0.9, 0.75, 0.5, 0.25, 0.1],
                      gammas=[0.99, 0.99, 0.99, 0.99, 0.99], path=path.joinpath("evaluate_gdpa"))


if __name__ == "__main__":
    functions = ["fun_1", "fun_2", "fun_3"]
    run(functions=functions)
