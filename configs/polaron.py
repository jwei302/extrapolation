POLY = {
    'degrees': [4],
    'alphas': [0.01],
}

RFF = {
    'ls_T_factors': [32.0],
    'ls_m_factors': [0.5],
    'n_features_list': [4000],
    'alphas': [1e-08],
    'n_rff_seeds': 3,
}

GP = {
    'alphas': [1e-08],
    'n_restarts_optimizer': 3,
    'constant_value_bounds': (0.001, 1000.0),
    'length_scale_bounds': (0.01, 100.0),
    'kernel': '(RBF)+MAT',
}

MLP = {
    'n_layers_list': [4],
    'widths': [128],
    'activations': ['gelu'],
    'lrs': [0.01],
    'weight_decays': [0.0001],
    'max_epochs': 20000,
    'patience': 500,
    'n_seeds': 1,
}

NUMERICS = {
    "jitter_poly": 1e-06,
    "jitter_rff": 2e-15,
}


DISTANCES = [0.1000, 0.1191, 0.1420, 0.1691, 0.2015, 0.2401, 0.2861, 0.3409, 0.4061, 0.4839]
