POLY = {
    'axis_degrees': [(2, 12)],
    'degrees': [10],
    'alphas': [1e-10],
}

RFF = {
    'n_features_list': [8000],
    'ls_T_factors': [1.0],
    'ls_m_factors': [0.25],
    'alphas': [1e-08],
    'n_rff_seeds': 3,
}

GP = {
    'alphas': [1e-08],
    'n_restarts_optimizer': 1,
    'constant_value_bounds': (0.001, 1000.0),
    'length_scale_bounds': (0.01, 100.0),
    'length_scale_bounds_per_axis': [(10.0, 10000.0), (0.01, 100.0)],
    'kernel': '(MAT)*MAT',
}

MLP = {
    'n_layers_list': [8],
    'widths': [128],
    'activations': ['tanh'],
    'lrs': [0.01],
    'weight_decays': [0.0001],
    'max_epochs': 40000,
    'patience': 1500,
    'n_seeds': 1,
}

NUMERICS = {
    "jitter_poly": 1e-12,
    "jitter_rff": 1e-12,
}


DISTANCES = [0.2861, 0.3245, 0.3680, 0.4174, 0.4734, 0.5369, 0.6089, 0.6905, 0.7831, 0.8882]
