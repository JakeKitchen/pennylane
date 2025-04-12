:orphan:

# Release 0.42.0-dev (development release)

<h3>New features since last release</h3>

<h3>Improvements 🛠</h3>

* Optimized the vibrational quantum chemistry modules (VSCF and Christiansen utilities) for better performance with larger molecular systems. Functions improved include `_find_active_terms`, `_rotate_three_body`, and `_fock_energy`.
  [(#7273)](https://github.com/PennyLaneAI/pennylane/pull/7273)

<h3>Breaking changes 💔</h3>

<h3>Deprecations 👋</h3>

<h3>Internal changes ⚙️</h3>

<h3>Documentation 📝</h3>

<h3>Bug fixes 🐛</h3>

* Fixes a bug where the global phase was not being added in the ``QubitUnitary`` decomposition.  
  [(#7244)](https://github.com/PennyLaneAI/pennylane/pull/7244)

<h3>Contributors ✍️</h3>

This release contains contributions from (in alphabetical order):

Guillermo Alonso-Linaje Jacob Kitchen
