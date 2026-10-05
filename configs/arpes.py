POLY = {
    'degrees': [10],
    'alphas': [1e-05],
}

RFF = {
    'n_features_list': [2000],
    'ls_T_factors': [2.0],
    'ls_m_factors': [0.25],
    'alphas': [0.0001],
    'n_rff_seeds': 3,
}

GP = {
    'alphas': [1e-08],
    'n_restarts_optimizer': 3,
    'constant_value_bounds': (0.001, 1000.0),
    'length_scale_bounds': (0.01, 100.0),
    'kernel': '(MAT)+RBF',
}

MLP = {
    'n_layers_list': [4],
    'widths': [512],
    'activations': ['gelu'],
    'lrs': [0.003],
    'weight_decays': [0.0001],
    'max_epochs': 500000,
    'patience': 500,
    'n_seeds': 1,
}

FF_MLP = {
    'm_ff_list': [256],
    'sigmas': [0.05],
    'n_layers_list': [6],
    'widths': [256],
    'activation': 'gelu',
    'lrs': [0.001],
    'weight_decays': [0.0001],
    'max_epochs': 500000,
    'patience': 500,
    'n_seeds': 1,
}

SIREN = {
    'n_layers_list': [4],
    'widths': [256],
    'omega_0_first_list': [10.0],
    'omega_0_hidden': 5.0,
    'lrs': [0.0001],
    'weight_decays': [0.0],
    'max_epochs': 500000,
    'patience': 500,
    'n_seeds': 1,
}

PINN = {
    'constraints': ['nonneg', 'sumrule'],
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
    'structure': 'peak',
    'n_layers_list': [2],
    'widths': [64],
    'lrs': [0.001],
    'weight_decays': [0.0001],
    'max_epochs': 500000,
    'patience': 500,
    'n_seeds': 1,
}

NUMERICS = {
    "jitter_poly": 1e-09,
    "jitter_rff": 1e-09,
}


DISTANCES = [5.0000, 7.1811, 10.3136, 14.8125, 21.2739, 30.5539, 43.8819, 63.0238, 90.5157, 130.0000]
