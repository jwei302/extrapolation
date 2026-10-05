# ARPES data

Antinodal energy-distribution curves of Pb-doped Bi-2212, from

- Y. He, S.-D. Chen, Z.-X. Li, et al., Superconducting fluctuations in overdoped
  Bi2Sr2CaCu2O8+δ, *Phys. Rev. X* **11**, 031068 (2021),
  https://doi.org/10.1103/PhysRevX.11.031068
- X. Chen, Y. Sun, E. Hruska, V. Dixit, J. Yang, Y. He, Y. Wang, and F. Liu, Detecting
  thermodynamic phase transition via explainable machine learning of photoemission
  spectroscopy, *Newton* **1**, 100066 (2025), https://doi.org/10.1016/j.newton.2025.100066

The ARPES data released with the Newton paper are public on Figshare:
X. Chen, ARPES-data (2025), https://doi.org/10.6084/m9.figshare.25439632.v1.

## Files

The measurements are in their original format:

    T_list.txt                 100 temperatures in K
    Tdep_EDC_AN_3momenta.txt   3 blocks, 511 separated energy rows x 100 T columns

The three blocks are the momentum-integration windows, named in their headers:

    combEDC169to179norm        window 0
    combEDC217to227norm        window 1 
    combEDC265to275norm        window 2

## Axes

The temperature axis is `T_list.txt`, 100 non-uniformly spaced points from
13.5 to 290 K, in the same order as the intensity columns.

The energy axis is the fixed grid:

    E_j = -0.371173 + 0.001 j  eV,     j = 0 ... 510

one entry per intensity row, matching `E_J0`, `E_STEP` and `N_E` in
`convert.py`. 

## Building the array

    python -m data.arpes.convert          # -> data/arpes/edc.npz

## License

The ARPES datasets are published under
[CC-BY 4.0](https://creativecommons.org/licenses/by/4.0/) with copyright retained
by the authors of the PRX paper, and are redistributed here under that license
with attribution. 