import numpy as np
from scipy.special import softmax, expit

P_PRIOR = 0.5

def softplus(x):
    '''stable version of log(1 + exp(x))'''
    c = (x > 20) * 1.
    return np.log1p(np.exp(x * (1-c)) * (1-c)) + x * c


def log_likelihood(alpha, beta, L, z):
    """ p(l=z|z, \alpha, \beta)
    Args:
        alpha: ndarray of shape (n_experts).
        beta: ndarray of shape (n_problems).
        L: ndarray of shape (n_problems, n_experts).
        z: ndarray of shape (n_problems).
    Returns:
        ndarray of shape (n_problems,)
    Tips:
        See page 7 of seminar, the second formula for details
    """

    alpha_beta_product = (alpha[:, np.newaxis] * beta[np.newaxis, :]).T
    
    mask = L == z[:, np.newaxis]

    return (
        -softplus(-alpha_beta_product) * mask.astype(float) +
        -softplus(alpha_beta_product) * (~mask).astype(float)
    )

def posterior(alpha, beta, L):
    """ Posterior over true labels z p(z|l, \alpha, \beta)
    Args:
        alpha: ndarray of shape (n_experts).
        beta: ndarray of shape (n_problems).
        L: ndarray of shape (n_problems, n_experts).
    Returns:
        ndarray of shape (2, n_problems)
        (2 -- for z = 0 and for z = 1, n_problems -- for each problem in data)
    Tip:
        You may use function log_likelihood here
        See page 7 of seminar, the last formula for details
    """
    gamma_0 = (
        np.log(P_PRIOR) +
        log_likelihood(alpha, beta, L, np.zeros(L.shape[0])).sum(axis=1)
    )
    gamma_1 = (
        np.log(P_PRIOR) +
        log_likelihood(alpha, beta, L, np.ones(L.shape[0])).sum(axis=1)
    )
    
    gamma = np.stack([gamma_0.T, gamma_1.T], axis=1)

    return softmax(gamma, axis=1).T


def alpha_grad_lb(alpha, beta, L, q):
    """ Gradient of lower bound wrt alpha
    Args:
        alpha: ndarray of shape (n_experts).
        beta: ndarray of shape (n_problems).
        L: ndarray of shape (n_problems, n_experts).
        q: ndarray of shape (2, n_problems).
    Returns:
        ndarray of shape (n_experts,)
    Tips:
        See pages 8-9 of seminar for details
    """
    alpha_beta = (alpha[:, np.newaxis] * beta[np.newaxis, :]).T
    mask = (L == 0)
    
    # 2000 x 20
    t0 = mask * expit(-alpha_beta) - (~mask).astype(float) * expit(alpha_beta)
    t1 = (~mask).astype(float) * expit(-alpha_beta) - mask * expit(alpha_beta)

    # 2000 x 20
    tq0 = t0 * q[0, :][:, np.newaxis]
    tq1 = t1 * q[1, :][:, np.newaxis]

    # 2 x 2000 x 20 --> 20
    tqb = (np.stack([tq0, tq1]) * beta[:, np.newaxis]).sum(axis=(0, 1))

    return tqb
    

def logbeta_grad_lb(alpha, beta, L, q):
    """ Gradient of lower bound wrt alpha
    Args:
        alpha: ndarray of shape (n_experts).
        beta: ndarray of shape (n_problems).
        L: ndarray of shape (n_problems, n_experts).
        q: ndarray of shape (2, n_problems).
    Returns:
        ndarray of shape (n_problems,)
    Tips:
        See pages 8-9 of seminar for details
    """
    alpha_beta = (alpha[:, np.newaxis] * beta[np.newaxis, :]).T
    mask = (L == 0)
    
    # 2000 x 20
    t0 = mask * expit(-alpha_beta) - (~mask).astype(float) * expit(alpha_beta)
    t1 = (~mask).astype(float) * expit(-alpha_beta) - mask * expit(alpha_beta)

    # 2000 x 20
    tq0 = t0 * q[0, :][:, np.newaxis]
    tq1 = t1 * q[1, :][:, np.newaxis]

    print()
    # 2 x 2000 x 20 --> 2000
    tqa = (np.stack([tq0, tq1]) * alpha[np.newaxis, :]).sum(axis=(0, 2))

    return tqa * beta


def lower_bound(alpha, beta, L, q):
    """ Lower bound
    Args:
        alpha: ndarray of shape (n_experts).
        beta: ndarray of shape (n_problems).
        L: ndarray of shape (n_problems, n_experts).
        q: ndarray of shape (2, n_problems).
    Returns:
        single value, number
    Tips:
        You may use function log_likelihood here
        See page 8 of seminar, the fourth formula for details
    """
    mask = L == 0

    llh_0 = (
        (log_likelihood(alpha, beta, L, np.zeros(L.shape[0]))
        * mask.astype(float)).sum(axis=1)
        * q[0, :]
        - np.log(q[0, :])
    ).sum()

    print(q[0, :].shape)

    llh_1 = (
        (log_likelihood(alpha, beta, L, np.ones(L.shape[0]))
        * (~mask).astype(float)).sum(axis=1)
        * q[1, :]
        - np.log(q[1, :])
    ).sum()
    
    return llh_1 + llh_0
