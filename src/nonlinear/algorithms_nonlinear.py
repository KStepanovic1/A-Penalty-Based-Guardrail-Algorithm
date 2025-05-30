from pyscipopt import Model, quicksum, multidict, exp
import tensorflow as tf
import time
from src.helpers import *


def sigmoid(x):
    """Sigmoid activation function."""
    return 1 / (1 + exp(-x))


def tanh(x):
    """Hyperbolic tangent activation function."""
    return (exp(x) - exp(-x)) / (exp(x) + exp(-x))


def relu(m, neuron_input, i, j, M=10000):
    """Rectified Linear Unit (ReLU) activation function."""
    # Create binary variable for activation status
    is_active = m.addVar(name=f"relu_active_{i}_{j}", vtype="B")

    # Create output variable (always non-negative)
    neuron_output = m.addVar(name=f"relu_output_{i}_{j}", lb=0.0)

    # ReLU constraints
    m.addCons(neuron_input <= M * is_active)
    m.addCons(neuron_input >= -M * (1 - is_active))

    m.addCons(neuron_output >= neuron_input)
    m.addCons(neuron_output <= neuron_input + M * (1 - is_active))

    m.addCons(neuron_output >= 0)
    m.addCons(neuron_output <= M * is_active)

    return m, neuron_output


def leaky_relu(m, neuron_input, i, j, alpha=0.01, M=10000):
    """Leaky rectified linear unit (LeakyReLU) activation function."""
    neuron_output = m.addVar(
        name=f"leaky_relu_output_{i}_{j}", lb=float("-inf"), ub=float("+inf")
    )

    # Auxiliary binary variable to handle the piecewise function
    is_active = m.addVar(name=f"leaky_relu_is_positive_{i}_{j}", vtype="BINARY")

    # Constraints to implement LeakyReLU
    m.addCons(neuron_input <= M * is_active)
    m.addCons(neuron_input >= -M * (1 - is_active))

    m.addCons(neuron_output >= neuron_input)
    m.addCons(neuron_output <= neuron_input + M * (1 - is_active))

    m.addCons(neuron_output >= alpha * neuron_input - M * is_active)
    m.addCons(neuron_output <= alpha * neuron_input + M * is_active)

    return m, neuron_output


def elu(m, neuron_input, i, j, alpha=1, M=10000):
    """Exponential linear unit (ELU) activation function."""
    neuron_output = m.addVar(
        name=f"elu_output_{i}_{j}", lb=float("-inf"), ub=float("+inf")
    )

    # Auxiliary binary variable to handle the piecewise function
    is_active = m.addVar(name=f"elu_is_positive_{i}_{j}", vtype="BINARY")

    # Constraints to implement ELU
    m.addCons(neuron_input <= M * is_active)
    m.addCons(neuron_input >= -M * (1 - is_active))

    m.addCons(neuron_output >= neuron_input)
    m.addCons(neuron_output <= neuron_input + M * (1 - is_active))

    m.addCons(neuron_output >= alpha * (exp(neuron_input) - 1) - M * is_active)
    m.addCons(neuron_output <= alpha * (exp(neuron_input) - 1) + M * is_active)

    return m, neuron_output


def selu(m, neuron_input, i, j, alpha=1.67326, lambda_=1.0507, M=10000):
    """Scaled exponential linear unit (ELU) activation function."""
    neuron_output = m.addVar(
        name=f"selu_output_{i}_{j}", lb=float("-inf"), ub=float("+inf")
    )

    # Auxiliary binary variable to handle the piecewise function
    is_active = m.addVar(name=f"selu_is_positive_{i}_{j}", vtype="BINARY")

    # Constraints to implement ELU
    m.addCons(neuron_input <= M * is_active)
    m.addCons(neuron_input >= -M * (1 - is_active))

    m.addCons(neuron_output >= lambda_ * neuron_input)
    m.addCons(neuron_output <= lambda_ * neuron_input + M * (1 - is_active))

    m.addCons(neuron_output >= lambda_ * alpha * (exp(neuron_input) - 1) - M * is_active)
    m.addCons(neuron_output <= lambda_ * alpha * (exp(neuron_input) - 1) + M * is_active)
    return m, neuron_output


def exponential(x):
    """Exponential function."""
    return exp(x)


def compile_nn(
        m,
        order_constraint,
        num_var,
        x,
        num_layers,
        neurons_per_layer,
        weights,
        activations,
        q,
):
    layer_output = []
    # Loop through each layer and initialize an empty list for neurons in each layer
    for i, nn in enumerate(neurons_per_layer):
        # Create list for variables in the current layer
        current_layer = []
        for j in range(nn):
            var_name = f"layer_{i}_neuron_{j}"
            current_layer.append(
                m.addVar(
                    name=var_name,
                    lb=float("-inf"),
                    ub=float("+inf"),
                )
            )
        # Append the current layer's variables to layer_output
        layer_output.append(current_layer)

    # Loop through each layer to define constraints
    for i in range(num_layers):
        activation = activations[i]
        weights_per_layer = weights[i]
        if i == 0:
            # Input layer computation
            for j in range(neurons_per_layer[i]):
                neuron_input = quicksum(
                    weights_per_layer[k][j] * x[k] for k in range(num_var)
                )
                if activation == "linear":
                    neuron_output = neuron_input
                elif activation == "sigmoid":
                    neuron_output = sigmoid(neuron_input)
                elif activation == "tanh":
                    neuron_output = tanh(neuron_input)
                elif activation == "relu":
                    m, neuron_output = relu(m=m, neuron_input=neuron_input, i=i, j=j)
                elif activation == "leaky_relu":
                    m, neuron_output = leaky_relu(
                        m=m, neuron_input=neuron_input, i=i, j=j, alpha=0.01
                    )
                elif activation == "elu":
                    m, neuron_output = elu(
                        m=m, neuron_input=neuron_input, i=i, j=j, alpha=1
                    )
                elif activation == "selu":
                    m, neuron_output = selu(
                        m=m,
                        neuron_input=neuron_input,
                        i=i,
                        j=j,
                        alpha=1.67326,
                        lambda_=1.0507,
                    )
                elif activation == "exponential":
                    neuron_output = exponential(neuron_input)
                else:
                    raise ValueError(f"Unsupported activation function: {activation}")
                constraint_name = f"layer_{i}_neuron_{j}_constraint"
                m.addCons(layer_output[i][j] == neuron_output, name=constraint_name)
        else:
            # Hidden and output layer computation
            for j in range(neurons_per_layer[i]):
                neuron_input = quicksum(
                    weights_per_layer[k][j] * layer_output[i - 1][k]
                    for k in range(neurons_per_layer[i - 1])
                )
                if activation == "linear":
                    neuron_output = neuron_input
                elif activation == "sigmoid":
                    neuron_output = sigmoid(neuron_input)
                elif activation == "tanh":
                    neuron_output = tanh(neuron_input)
                elif activation == "relu":
                    m, neuron_output = relu(m=m, neuron_input=neuron_input, i=i, j=j)
                elif activation == "leaky_relu":
                    m, neuron_output = leaky_relu(
                        m=m, neuron_input=neuron_input, i=i, j=j, alpha=0.01
                    )
                elif activation == "elu":
                    m, neuron_output = elu(
                        m=m, neuron_input=neuron_input, i=i, j=j, alpha=1
                    )
                elif activation == "selu":
                    m, neuron_output = selu(
                        m=m,
                        neuron_input=neuron_input,
                        i=i,
                        j=j,
                        alpha=1.67326,
                        lambda_=1.0507,
                    )
                elif activation == "exponential":
                    neuron_output = exponential(neuron_input)
                else:
                    raise ValueError(f"Unsupported activation function: {activation}")
                constraint_name = f"layer_{i}_neuron_{j}_constraint"
                m.addCons(layer_output[i][j] == neuron_output, name=constraint_name)

    # Add final constraint
    m.addCons(layer_output[-1][0] >= q, name=f"constraint({order_constraint})")
    return m, layer_output


def mps(problem_specs):
    """
    Compiles the problem specification of the neural network into a Mathematical Programming Solver (MPS).
    """
    start = time.time()

    # Unpack problem specifications
    num_var = problem_specs["num_var"]
    num_con = problem_specs["num_con"]
    num_layers = problem_specs["num_layers"]
    neurons_per_layer = problem_specs["num_neuron_per_layer"]
    weights = problem_specs["w"]
    activations = problem_specs["activation_fun"]
    q = problem_specs["q"]
    c_obj = problem_specs["c_obj"]
    lb = problem_specs["lb"]
    ub = problem_specs["ub"]

    # Create Model
    m = Model("MPS")
    m.resetParams()
    # m.setRealParam("numerics/feastol", 1e-03)
    m.setRealParam("limits/time", problem_specs["T"])

    # Decision Variables
    x = {i: m.addVar(lb=lb[i], ub=ub[i], name=f"x({i})") for i in range(num_var)}
    layer_outputs = []
    # Constraint compilation
    for i in range(num_con):
        m, layer_output = compile_nn(
            m=m,
            order_constraint=i,
            num_var=num_var,
            x=x,
            num_layers=num_layers[i],
            neurons_per_layer=neurons_per_layer[i],
            weights=weights[i],
            activations=activations[i],
            q=q[i],
        )
        layer_outputs.append(layer_output)

    # Objective variable
    objvar = m.addVar(name="J", lb=None, ub=None)
    m.setObjective(objvar, "minimize")
    m.addCons(
        objvar >= quicksum(c_obj[j] * x[j] for j in range(num_var)),
        name="objective_function_constraint",
    )

    # Save model
    m.writeProblem("mps.cip")
    # Optimize the model
    m.optimize()

    # Extracting results
    end = time.time()
    var = [m.getVal(x[i]) for i in range(num_var)]
    J = m.getVal(objvar)
    constraint_values = []
    for i in range(num_con):
        constraint_values.append(m.getVal(layer_outputs[i][-1][0]) - q[i])
    return [J], [constraint_values], [var], [end - start]


def get_constraint_values(
        var, w, q, activations, gdpa_coeff_w=1, gdpa_coeff_q=1
) -> np.ndarray:
    var = tf.constant(var, dtype=tf.float32)
    q = tf.constant(q, dtype=tf.float32)

    outputs = []
    for constraint_weights, constraint_activations in zip(w, activations):
        x = var
        for weights, activation in zip(constraint_weights, constraint_activations):
            x = tf.tensordot(x, weights, axes=[[0], [0]])

            if activation == "elu":
                x = tf.nn.elu(x)
            elif activation == "exponential":
                x = tf.math.exp(x)
            elif activation == "relu":
                x = tf.nn.relu(x)
            elif activation == "sigmoid":
                x = tf.nn.sigmoid(x)
            elif activation == "tanh":
                x = tf.nn.tanh(x)
            # Add more activation functions as needed

        outputs.append(x)

    x = tf.stack(outputs)
    x = tf.squeeze(x)  # Ensure x is 1D
    q = tf.squeeze(q)  # Ensure q is 1D

    constraint_values = (
            gdpa_coeff_w * x - gdpa_coeff_q * q
    )  # Positive values indicate satisfied constraints

    return np.atleast_1d(constraint_values.numpy())


@tf.function
def calculate_gradient_penalty_fun(var, c_obj, w, q, activations, C):
    with tf.GradientTape() as tape:
        tape.watch(var)
        # f = tf.math.add_n([c_obj[i] * var[i] for i in range(num_var)])
        f_obj = tf.tensordot(c_obj, var, axes=1)
        outputs = []
        for constraint_weights, constraint_activations in zip(w, activations):
            x = var
            for weights, activation in zip(constraint_weights, constraint_activations):
                # Matrix multiplication
                x = tf.tensordot(x, weights, axes=[[0], [0]])
                # Apply activation function
                if activation == "linear":
                    pass
                elif activation == "elu":
                    x = tf.nn.elu(x)
                elif activation == "exponential":
                    x = tf.math.exp(x)
                elif activation == "relu":
                    x = tf.nn.relu(x)
                elif activation == "sigmoid":
                    x = tf.nn.sigmoid(x)
                elif activation == "tanh":
                    x = tf.nn.tanh(x)
                elif activation == "leaky_relu":
                    x = tf.nn.leaky_relu(x)
                elif activation == "selu":
                    x = tf.nn.selu(x)
                # Add more activation functions as needed
            outputs.append(x)
        x = tf.stack(outputs)
        x = tf.squeeze(x)
        # Constraint violations
        # If penalizing when Ax < q:
        violations = tf.nn.relu(q - x)  # Shape: (num_con,)
        # Penalty term: penalty = C * sum(violations^2)
        penalty = C * tf.reduce_sum(tf.square(violations))  # Scalar value
        f = f_obj + penalty
    grads = tape.gradient(f, var)
    return grads


def standard_penalty_alg(problem_specs, grad_specs, C):
    print("PM")

    var = tf.Variable(grad_specs["initial_vector"], dtype=tf.float32)

    # Convert c_obj, w, q, ub, lb to tensors
    c_obj = tf.constant(
        problem_specs["c_obj"], dtype=tf.float32
    )  # Objective coefficients
    w = [
        [tf.constant(layer, dtype=tf.float32) for layer in constraint]
        for constraint in problem_specs["w"]
    ]
    q = tf.constant(problem_specs["q"], dtype=tf.float32)  # Constraint bounds
    lb = tf.constant(problem_specs["lb"], dtype=tf.float32)
    ub = tf.constant(problem_specs["ub"], dtype=tf.float32)
    activations = problem_specs["activation_fun"]

    C = C

    opt = tf.keras.optimizers.Adam(learning_rate=0.01)
    grad_iter = 0
    grad_iter_max = grad_specs["grad_iter_max"]
    start_time = time.time()
    while grad_iter < grad_iter_max:
        grads = calculate_gradient_penalty_fun(
            var=var, c_obj=c_obj, w=w, q=q, activations=activations, C=C
        )
        opt.apply_gradients([(grads, var)])
        # Apply variable bounds
        var.assign(tf.clip_by_value(var, lb, ub))
        grad_iter += 1
    end_time = time.time()
    var_np = var.numpy()
    J = float(np.sum(c_obj.numpy() * var_np))
    constraint_values = get_constraint_values(
        var=var_np, w=w, q=q, activations=activations
    )
    runtime = end_time - start_time
    return [J], [constraint_values], [var_np.tolist()], [runtime]


@tf.function
def calculate_gradient_lagrangian_fun(var, c_obj, w, activations, q, rho, lambdas):
    with tf.GradientTape() as tape:
        tape.watch(var)
        # f = tf.math.add_n([c_obj[i] * var[i] for i in range(num_var)])
        f_obj = tf.tensordot(c_obj, var, axes=1)
        outputs = []
        for constraint_weights, constraint_activations in zip(w, activations):
            x = var
            for weights, activation in zip(constraint_weights, constraint_activations):
                # Matrix multiplication
                x = tf.tensordot(x, weights, axes=[[0], [0]])
                # Apply activation function
                if activation == "linear":
                    pass
                elif activation == "elu":
                    x = tf.nn.elu(x)
                elif activation == "exponential":
                    x = tf.math.exp(x)
                elif activation == "relu":
                    x = tf.nn.relu(x)
                elif activation == "sigmoid":
                    x = tf.nn.sigmoid(x)
                elif activation == "tanh":
                    x = tf.nn.tanh(x)
                elif activation == "leaky_relu":
                    x = tf.nn.leaky_relu(x)
                elif activation == "selu":
                    x = tf.nn.selu(x)
                # Add more activation functions as needed
            outputs.append(x)
        x = tf.stack(outputs)
        x = tf.squeeze(x)
        # Constraint violations
        # If penalizing when Ax < q:
        violations = x - q  # Shape: (num_con,)
        # Penalty term: penalty = C * sum(violations^2)
        penalty = (1 / rho) * tf.reduce_sum(tf.square(violations))  # Scalar value
        linear_term = tf.tensordot(lambdas, violations, axes=1)
        f = f_obj + penalty + linear_term
    grads = tape.gradient(f, var)
    return grads


def ipdd(
        problem_specs,
        grad_specs,
):
    print("IPDD")
    Js, constraint_values, solutions, runtimes = [], [], [], [0]

    var = tf.Variable(grad_specs["initial_vector"], dtype=tf.float32)
    lambdas = tf.Variable(grad_specs["initial_lambdas"], dtype=tf.float32)

    # Convert c_obj, w, q, ub, lb to tensors
    c_obj = tf.constant(
        problem_specs["c_obj"], dtype=tf.float32
    )  # Objective coefficients
    w = [
        [tf.constant(layer, dtype=tf.float32) for layer in constraint]
        for constraint in problem_specs["w"]
    ]
    q = tf.constant(problem_specs["q"], dtype=tf.float32)  # Constraint bounds
    lb = tf.constant(problem_specs["lb"], dtype=tf.float32)
    ub = tf.constant(problem_specs["ub"], dtype=tf.float32)
    activations = problem_specs["activation_fun"]

    rho = grad_specs["rho"]

    grad_iter_max = grad_specs["grad_iter_max"]
    outer_iter = 0
    # Convert c and q to tensors
    while runtimes[-1] < problem_specs["T"]:
        print("outer_iter ", outer_iter)
        outer_iter += 1
        # at each new iteration of outer loop, reset gradient iterations and patience counter.
        grad_iter = 0
        opt = tf.keras.optimizers.Adam(learning_rate=0.01)
        start_time = time.time()
        while grad_iter < grad_iter_max:
            grads = calculate_gradient_lagrangian_fun(
                var=var,
                c_obj=c_obj,
                w=w,
                activations=activations,
                q=q,
                rho=rho,
                lambdas=lambdas,
            )
            opt.apply_gradients([(grads, var)])
            # Apply variable bounds
            var.assign(tf.clip_by_value(var, lb, ub))
            grad_iter += 1
        var_np = var.numpy()
        J = np.sum(c_obj.numpy() * var_np)
        # Compute constraint violations using TensorFlow
        constraint_value = get_constraint_values(
            var=var_np, w=w, q=q, activations=activations
        )
        constraint_value_tf = tf.constant(constraint_value, dtype=tf.float32)
        constraint_value_tf = tf.reshape(constraint_value_tf, lambdas.shape)
        # Update Lagrange multipliers
        lambdas.assign_add((1 / rho) * constraint_value_tf)
        rho = rho * (1 / (outer_iter ** (1 / 3)))
        end_time = time.time()
        solutions.append(var_np.tolist())
        Js.append(J)
        constraint_values.append(constraint_value)
        runtimes.append(runtimes[-1] + end_time - start_time)
    return Js, constraint_values, solutions, runtimes[1:]


@tf.function
def calculate_gradient_obj_fun(var, c_obj):
    with tf.GradientTape() as tape:
        tape.watch(var)
        f = tf.tensordot(c_obj, var, axes=1)
    grads = tape.gradient(f, var)
    return grads


@tf.function
def calculate_jacobian(var, w, q, activations):
    with tf.GradientTape() as tape:
        tape.watch(var)
        outputs = []
        for constraint_weights, constraint_activations in zip(w, activations):
            x = var
            for weights, activation in zip(constraint_weights, constraint_activations):
                x = tf.tensordot(x, weights, axes=[[0], [0]])
                if activation == "linear":
                    pass
                elif activation == "elu":
                    x = tf.nn.elu(x)
                elif activation == "exponential":
                    x = tf.math.exp(x)
                elif activation == "relu":
                    x = tf.nn.relu(x)
                elif activation == "sigmoid":
                    x = tf.nn.sigmoid(x)
                elif activation == "tanh":
                    x = tf.nn.tanh(x)
                elif activation == "leaky_relu":
                    x = tf.nn.leaky_relu(x)
                elif activation == "selu":
                    x = tf.nn.selu(x)
            outputs.append(-x)
        g = tf.stack(outputs)
        g = tf.squeeze(g) + q
    jacobian = tape.jacobian(g, var)
    return jacobian


def gdpa(problem_specs, grad_specs, step_size_init, perturbation_term, beta_init, gamma):
    print("GDPA")
    Js, constraint_values_, solutions, runtimes = [], [], [], [0]

    solution_prev = tf.Variable(grad_specs["initial_vector"], dtype=tf.float32)
    lambdas_prev = tf.Variable(grad_specs["initial_lambdas"], dtype=tf.float32)

    # Convert c_obj, w, q, ub, lb to tensors
    c_obj = tf.constant(
        problem_specs["c_obj"], dtype=tf.float32
    )  # Objective coefficients
    w = [
        [tf.constant(layer, dtype=tf.float32) for layer in constraint]
        for constraint in problem_specs["w"]
    ]
    q = tf.constant(problem_specs["q"], dtype=tf.float32)  # Constraint bounds
    lb = tf.constant(problem_specs["lb"], dtype=tf.float32)
    ub = tf.constant(problem_specs["ub"], dtype=tf.float32)
    activations = problem_specs["activation_fun"]

    grad_iter_max = grad_specs["grad_iter_max"]
    outer_iter = 0
    while runtimes[-1] < 20:
        outer_iter += 1
        print("outer iteration ", outer_iter)
        start_time = time.time()
        beta = beta_init * outer_iter ** (1 / 3)
        print("beta ", beta)
        step_size = step_size_init * (1 / (outer_iter ** (1 / 3)))
        print("step size ", step_size)
        if tf.reduce_any(tf.math.is_nan(solution_prev)):
            break
        # first equation
        # np.ndarray([dJ/dx_1, dJ/dx_2,...,dJ/dx_n])_1xn
        delta_J = np.array(calculate_gradient_obj_fun(var=solution_prev, c_obj=c_obj))
        # print("delta_J ", delta_J)
        # tf.Tensor([df_1/dx_1,df_1/dx_2,...,df_1/dx_n],...,[df_m/dx_1,df_m/dx_2,...,df_m/dx_n])_mxn
        Jacobian = calculate_jacobian(
            var=solution_prev, w=w, q=q, activations=activations
        )
        print("Jacobian ", Jacobian)
        # np.array([df_1/dx_1,df_2/dx_1,...,df_m/dx_1],...,[df_1/dx_n,df_2/dx_n,...,df_m/dx_n])_nxm
        Jacobian = tf.transpose(Jacobian)
        # print("Jacobian ", Jacobian)
        constraint_values_prev = get_constraint_values(
            var=solution_prev,
            w=w,
            q=q,
            activations=activations,
            gdpa_coeff_w=-1,
            gdpa_coeff_q=-1,
        )
        print("solution prev ", solution_prev)
        print("constraint values prev ", constraint_values_prev)
        constraint_values_prev = tf.constant(constraint_values_prev, dtype=tf.float32)
        # print("constraint values prev ", constraint_values_prev)
        tau_beta = (
                beta * constraint_values_prev + (1 - perturbation_term) * lambdas_prev
        )
        print("tau_beta ", tau_beta)
        # print("tau_beta ", tau_beta)
        tau_beta_nonnegative = tf.maximum(tau_beta, 0)
        print("tau_beta_nonnegative ", tau_beta_nonnegative)
        # print("tau_beta_nonnegative ", tau_beta_nonnegative)
        solution = solution_prev - step_size * (
                delta_J + tf.tensordot(Jacobian, tau_beta_nonnegative, axes=1)
        )
        print("solution ", solution)
        # print("solution ", solution)
        solution = tf.clip_by_value(solution, lb, ub)
        print("solution clipped", solution)
        # print("solution ", solution)
        # second equationS_r = [i for i in range(num_con) if tau_beta[i] > 0]
        indices_range = tf.cast(tf.range(problem_specs["num_con"]), tf.int32)
        print("indices range ", indices_range)
        # print("indices range ", indices_range)
        S_r = tf.where(tau_beta > 0)[:, 0]
        S_r = tf.cast(S_r, tf.int32)
        print("S_r ", S_r)
        # print("S_r ", S_r)
        lambdas = tf.zeros(problem_specs["num_con"], dtype=tf.float32)
        # print("lambdas ", lambdas)
        mask = tf.reduce_any(
            tf.equal(tf.expand_dims(indices_range, 1), tf.expand_dims(S_r, 0)), axis=1
        )
        # print("mask ", mask)
        # calculate new constraint values
        constraint_values = get_constraint_values(
            var=solution,
            w=w,
            q=q,
            activations=activations,
            gdpa_coeff_w=-1,
            gdpa_coeff_q=-1,
        )
        constraint_values = tf.constant(constraint_values, dtype=tf.float32)
        print("constraint values ", constraint_values)
        # print("constraint values ", constraint_values)
        # Calculate new lambda values
        new_lambda_values = tf.maximum(
            0.0, (1 - perturbation_term) * lambdas_prev + beta * constraint_values
        )
        print("new lambda values ", new_lambda_values)
        # print("new lambda values ", new_lambda_values)
        # Update lambdas using the mask
        # where the mask is true, update the lambda values with the new lambda values (i \in S_r)
        # otherwise, keep the old lambda values (i \notin S_r)
        lambdas = tf.where(mask, new_lambda_values, lambdas)
        print("lambdas ", lambdas)
        # print("lambdas ", lambdas)
        solution_prev = solution
        lambdas_prev = lambdas
        end_time = time.time()
        solution_np = solution.numpy()
        J = np.sum(c_obj.numpy() * solution_np)
        Js.append(J)
        solutions.append(solution_np.tolist())
        constraint_value_temp = get_constraint_values(
            var=solution, w=w, q=q, activations=activations
        ).tolist()
        constraint_values_.append(constraint_value_temp)
        runtimes.append(end_time - start_time + runtimes[-1])
    return Js, constraint_values_, solutions, runtimes[1:]


def pga(problem_specs, grad_specs, C):
    print("PGA")
    Js, constraint_values, variables, runtimes = [], [], [], [0]
    epsilon = [0] * problem_specs["num_con"]

    c_obj = tf.constant(
        problem_specs["c_obj"], dtype=tf.float32
    )  # Objective coefficients
    w = [
        [tf.constant(layer, dtype=tf.float32) for layer in constraint]
        for constraint in problem_specs["w"]
    ]
    q = tf.constant(problem_specs["q"], dtype=tf.float32)  # Constraint bounds
    lb = tf.constant(problem_specs["lb"], dtype=tf.float32)
    ub = tf.constant(problem_specs["ub"], dtype=tf.float32)
    activations = problem_specs["activation_fun"]

    C = C

    grad_iter_max = grad_specs["grad_iter_max"]
    outer_iter = 0
    while runtimes[-1] < problem_specs["T"]:
        outer_iter += 1
        # at each new iteration of outer loop, reset gradient iterations and patience counter.
        grad_iter = 0
        var = tf.Variable(grad_specs["initial_vector"], dtype=tf.float32)
        opt = tf.keras.optimizers.Adam(learning_rate=0.01)
        start_time = time.time()
        q_pga = tf.constant(
            [np.float32(epsilon[i] + x) for i, x in enumerate(q)], dtype=tf.float32
        )
        while grad_iter < grad_iter_max:
            grads = calculate_gradient_penalty_fun(
                var=var, c_obj=c_obj, w=w, q=q_pga, activations=activations, C=C
            )
            opt.apply_gradients([(grads, var)])
            # Apply variable bounds
            var.assign(tf.clip_by_value(var, lb, ub))
            grad_iter += 1
        end_time = time.time()
        # extract outer iteration results
        var_np = var.numpy()
        J = np.sum(c_obj.numpy() * var_np)
        constraint_value = get_constraint_values(
            var=var_np, w=w, q=q, activations=activations
        )
        # update epsilon
        epsilon = [
            np.float32(
                eps - (1 / (outer_iter ** (1 / 3))) * min(0, constraint_value[i])
            )
            for i, eps in enumerate(epsilon)
        ]
        # append outer iteration results
        variables.append(var_np.tolist())
        Js.append(J)
        constraint_values.append(constraint_value)
        runtimes.append(runtimes[-1] + end_time - start_time)
    return Js, constraint_values, variables, runtimes[1:]
