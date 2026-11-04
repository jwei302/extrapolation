POLY = {
    'degrees': [8],
    'alphas': [1e-06],
}

RFF = {
    'n_features_list': [8000],
    'alphas': [1e-08],
    'n_rff_seeds': 3,
    'ls_T_factors': [2.0],
    'ls_m_factors': [0.25],
}

GP = {
    'alphas': [1e-08],
    'n_restarts_optimizer': 3,
    'constant_value_bounds': (0.001, 1000.0),
    'length_scale_bounds': (0.01, 100.0),
    'kernel': '(((RBF)*LIN)*LIN)*LIN',
}

MLP = {
    'n_layers_list': [2],
    'widths': [256],
    'activations': ['gelu'],
    'lrs': [0.003],
    'weight_decays': [1e-05],
    'max_epochs': 500000,
    'patience': 500,
    'n_seeds': 1,
}

FF_MLP = {
    'm_ff_list': [128],
    'sigmas': [0.1],
    'n_layers_list': [4],
    'widths': [256],
    'activation': 'gelu',
    'lrs': [0.003],
    'weight_decays': [0.0001],
    'max_epochs': 500000,
    'patience': 500,
    'n_seeds': 1,
}

SIREN = {
    'n_layers_list': [4],
    'widths': [256],
    'omega_0_first_list': [2.0],
    'omega_0_hidden': 1.0,
    'lrs': [0.0001],
    'weight_decays': [0.0],
    'max_epochs': 500000,
    'patience': 500,
    'n_seeds': 1,
}

PINN = {
    'constraints': ['even_x2'],
    'lambdas': [1.0],
    'n_colloc': 4096,
    'grid_shape': [64, 64],
    'n_layers_list': [4],
    'widths': [128],
    'activations': ['gelu'],
    'lrs': [0.003],
    'weight_decays': [0.0001],
    'max_epochs': 500000,
    'patience': 500,
    'n_seeds': 1,
}

GRAYBOX = {
    'structure': 'coeff_poly',
    'orders': [0, 2, 4],
    'n_layers_list': [2],
    'widths': [64],
    'lrs': [0.003],
    'weight_decays': [0.0001],
    'max_epochs': 500000,
    'patience': 500,
    'n_seeds': 1,
}

NUMERICS = {
    "jitter_poly": 1.5e-14,
    "jitter_rff": 2e-15,
}


DISTANCES = [0.5000, 0.6101, 0.7445, 0.9086, 1.1087, 1.3529, 1.6510, 2.0146, 2.4584, 3.0000]
