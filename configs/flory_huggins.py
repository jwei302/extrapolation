POLY = {
    'degrees': [8],
    'alphas': [0.0001],
}

RFF = {
    'n_features_list': [8000],
    'alphas': [1e-08],
    'n_rff_seeds': 3,
    'ls_T_factors': [4.0],
    'ls_m_factors': [0.25],
}

GP = {
    'alphas': [1e-08],
    'n_restarts_optimizer': 1,
    'constant_value_bounds': (0.001, 1000.0),
    'length_scale_bounds': (0.01, 100.0),
    'kernel': 'RBF',
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
    "jitter_poly": 1e-07,
    "jitter_rff": 1e-12,
}


DISTANCES = [0.5000, 0.6101, 0.7445, 0.9086, 1.1087, 1.3529, 1.6510, 2.0146, 2.4584, 3.0000]
