import numpy as np
from models.data_models import MeasurePoint, FittedCircle


def fit_least_squares(points):
    """
    Kasa algebraic least-squares circle fit.
    Minimizes Σ((x²+y²) - A·x - B·y + C)².
    Fast but biased toward smaller radii for small arcs.
    """
    pts = np.array([[p.x, p.y] for p in points], dtype=np.float64)
    if len(pts) < 3:
        return None
    x, y = pts[:, 0], pts[:, 1]
    z = x * x + y * y
    A = np.column_stack([x, y, np.ones_like(x)])
    coeffs, _, _, _ = np.linalg.lstsq(A, z, rcond=None)
    a, b, c = coeffs
    cx = a / 2.0
    cy = b / 2.0
    radius = np.sqrt(cx * cx + cy * cy + c)
    distances = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
    rmse = float(np.sqrt(np.mean((distances - radius) ** 2)))
    return FittedCircle(cx=float(cx), cy=float(cy), radius=float(radius), rmse=rmse)


def fit_taubin(points):
    """
    Taubin algebraic circle fit — gradient-weighted normalization.

    Minimises Σ(a·z_i + b·x_i + c·y_i + d)² / Σ(‖∇f(x_i,y_i)‖²)
    where z_i = x_i² + y_i² and ∇f = (2a·x_i + b, 2a·y_i + c).

    More robust than Kasa for data covering small arcs and for noisy
    measurements.  Uses mean-centering → 3×3 generalised eigenproblem
    → back-substitution for numerical stability.

    Reference:
      G. Taubin, "Estimation of Planar Curves, Surfaces and Nonplanar
      Space Curves Defined by Implicit Equations …", IEEE PAMI, 1991.
    """
    pts = np.array([[p.x, p.y] for p in points], dtype=np.float64)
    if len(pts) < 3:
        return None

    n = len(pts)
    x_orig = pts[:, 0]
    y_orig = pts[:, 1]

    # ── mean-centre for stability ──────────────────────────────────────────
    mx = np.mean(x_orig)
    my = np.mean(y_orig)
    x = x_orig - mx
    y = y_orig - my
    z = x * x + y * y                     # z_i in centred coords
    z_bar = np.mean(z)

    # ── 3×3 moment matrix M ────────────────────────────────────────────────
    # After eliminating D, we minimise Σ(A·(z_i − z̄) + B·x_i + C·y_i)².
    # Hence M_ij uses z_i − z̄ rather than raw z_i.
    M = np.zeros((3, 3))
    M[0, 0] = np.mean(z * z) - z_bar ** 2   # var(z) — was missing −z̄² before
    M[0, 1] = M[1, 0] = np.mean(x * z)      # mean(x)=0 ⇒ cross-term unchanged
    M[0, 2] = M[2, 0] = np.mean(y * z)
    M[1, 1] = np.mean(x * x)
    M[1, 2] = M[2, 1] = np.mean(x * y)
    M[2, 2] = np.mean(y * y)

    # ── 3×3 constraint matrix N (diagonal because x̄ = ȳ = 0) ──────────────
    N = np.diag([4.0 * z_bar, 1.0, 1.0])

    # ── generalised eigenproblem  M·v = λ·N·v ─────────────────────────────
    # Cholesky of N (diagonal → trivial), then standard eigenvalue problem
    try:
        # N = L·Lᵀ  with L = diag(2√(z_bar), 1, 1)
        L_diag = np.array([2.0 * np.sqrt(max(z_bar, 1e-15)), 1.0, 1.0])
        L_inv_diag = 1.0 / L_diag
        # A = L⁻¹ · M · L⁻ᵀ   (standard symmetric eigenvalue problem)
        A = M * np.outer(L_inv_diag, L_inv_diag)
        eigenvalues, eigenvectors = np.linalg.eigh(A)
        v = L_inv_diag * eigenvectors[:, 0]     # back-transform eigenvector
    except np.linalg.LinAlgError:
        # degenerate case – fall back to smallest eigenvector of M alone
        eigenvalues, eigenvectors = np.linalg.eigh(M)
        v = eigenvectors[:, 0]

    # Ensure a consistent sign (A > 0 so centre formula works predictably)
    if v[0] < 0:
        v = -v

    A_coeff, B_coeff, C_coeff = v[0], v[1], v[2]

    # ── transform back to original coordinates ─────────────────────────────
    # Centred equation:  A·z' + B·x' + C·y' + D = 0
    # With centred data (x̄' = ȳ' = 0), taking the mean gives:
    #   A·z̄' + D = 0  ⟹  D = -A·z̄'
    # where z̄' = mean(x'² + y'²) = mean(x²+y²) - mx² - my²
    #
    # Original equation: a·z + b·x + c·y + d = 0
    #   a = A
    #   b = B - 2·A·mx
    #   c = C - 2·A·my
    #   d = D - a·(mx²+my²) - b·mx - c·my
    #     = -A·z̄' - a·(mx²+my²) - b·mx - c·my
    #     = -a·(mean(x²+y²) - mx² - my²) - a·(mx²+my²) - b·mx - c·my
    #     = -a·mean(x²+y²) - b·mx - c·my
    a = A_coeff
    b = B_coeff - 2.0 * a * mx
    c = C_coeff - 2.0 * a * my
    z_orig_mean = np.mean(x_orig * x_orig + y_orig * y_orig)
    d = -a * z_orig_mean - b * mx - c * my

    # Circle parameters from  a·(x²+y²) + b·x + c·y + d = 0
    cx = -b / (2.0 * a)
    cy = -c / (2.0 * a)
    radius_sq = (b * b + c * c) / (4.0 * a * a) - d / a
    radius = np.sqrt(max(radius_sq, 0.0))

    # RMSE
    distances = np.sqrt((x_orig - cx) ** 2 + (y_orig - cy) ** 2)
    rmse = float(np.sqrt(np.mean((distances - radius) ** 2)))

    return FittedCircle(cx=float(cx), cy=float(cy), radius=float(radius), rmse=rmse)
