"""RBF surrogate model for fast score prediction.

Fits a Radial Basis Function interpolator on evaluated samples and uses it
to predict scores for proposed candidates during adaptive resampling.

The surrogate is intentionally simple — its role is to guide local search,
not replace the actual FEM solver.
"""

from __future__ import annotations

import numpy as np

try:
    from scipy.interpolate import RBFInterpolator
    _HAS_RBF = True
except ImportError:
    _HAS_RBF = False


class ScoreSurrogate:
    """Wraps SciPy RBFInterpolator for scalar score prediction.

    Usage
    -----
        surrogate = ScoreSurrogate()
        surrogate.fit(X_norm, scores)          # X_norm: (N, D) in [0,1]
        y_pred = surrogate.predict(X_query)    # (M,)
    """

    def __init__(self, kernel: str = "thin_plate_spline", smoothing: float = 0.1) -> None:
        self._kernel = kernel
        self._smoothing = smoothing
        self._rbf = None
        self._fallback_mean: float = 0.0

    @property
    def is_fitted(self) -> bool:
        return self._rbf is not None

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        """Fit on normalised parameter matrix X and scalar scores y.

        Requires at least 2 training points. Falls back to mean prediction
        if scipy RBF is unavailable or training fails.
        """
        self._fallback_mean = float(np.mean(y))

        if not _HAS_RBF or len(X) < 3:
            return

        # Clip extreme scores before fitting to avoid numerical issues
        y_clipped = np.clip(y, np.percentile(y, 5), np.percentile(y, 95))

        try:
            self._rbf = RBFInterpolator(
                X,
                y_clipped,
                kernel=self._kernel,
                smoothing=self._smoothing * len(X),  # scale smoothing with n
            )
        except Exception:
            self._rbf = None

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict scores for a batch of normalised candidate rows."""
        if self._rbf is None:
            return np.full(len(X), self._fallback_mean)
        try:
            return np.clip(self._rbf(X), 0.0, None)
        except Exception:
            return np.full(len(X), self._fallback_mean)

    def predict_min_region(
        self, n_candidates: int, rng: np.random.Generator, n_dim: int
    ) -> np.ndarray:
        """Sample candidates from predicted low-score regions.

        Proposes a large pool of random points, predicts their scores,
        and returns the n_candidates with the lowest predicted scores.
        """
        pool_size = max(n_candidates * 50, 500)
        pool = rng.random((pool_size, n_dim))
        scores = self.predict(pool)
        idx = np.argsort(scores)[:n_candidates]
        return pool[idx]
