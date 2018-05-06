'''Model misc utilities.

'''

import logging
import math

logger = logging.getLogger('cortex.arch' + __name__)

try:
    import thundersvmScikit as svm
    use_thundersvm = True
except ImportError:
    from sklearn import svm
    logger.warning('Using sklearn SVM. This will be SLOW. Install thundersvm and add to your PYTHONPATH')
    use_thundersvm = False
import torch
import torch.functional as F


def log_sum_exp(x, axis=None):
    x_max = torch.max(x, axis)[0]
    y = torch.log((torch.exp(x - x_max)).sum(axis)) + x_max
    return y


def cross_correlation(X, remove_diagonal=False):
    X_s = X / X.std(0)
    X_m = X_s - X_s.mean(0)
    b, dim = X_m.size()
    correlations = (X_m.unsqueeze(2).expand(b, dim, dim) * X_m.unsqueeze(1).expand(b, dim, dim)).sum(0) / float(b)
    if remove_diagonal:
        Id = torch.eye(dim)
        Id = torch.autograd.Variable(Id.cuda(), requires_grad=False)
        correlations -= Id

    return correlations


def perform_svc(X, Y, clf=None):
    if clf is None:
        if use_thundersvm:
            clf = svm.SVC(kernel=0, verbose=True)
        else:
            clf = svm.LinearSVC()
        clf.fit(X, Y)

    Y_hat = clf.predict(X)

    return clf, Y_hat


def ms_ssim(X_a, X_b, window_size=11, size_average=True, C1=0.01**2, C2=0.03**2):
    '''
    Taken from Po-Hsun-Su/pytorch-ssim
    '''

    channel = X_a.size(1)

    def gaussian(sigma=1.5):
        gauss = torch.Tensor([math.exp(-(x - window_size // 2) ** 2 / float(2 * sigma ** 2)) for x in range(window_size)])
        return gauss / gauss.sum()

    def create_window():
        _1D_window = gaussian(window_size).unsqueeze(1)
        _2D_window = _1D_window.mm(_1D_window.t()).float().unsqueeze(0).unsqueeze(0)
        window = torch.Tensor(_2D_window.expand(channel, 1, window_size, window_size).contiguous())
        return window.cuda()

    window = create_window()

    mu1 = torch.nn.functional.conv2d(X_a, window, padding=window_size//2, groups=channel)
    mu2 = torch.nn.functional.conv2d(X_b, window, padding=window_size//2, groups=channel)

    mu1_sq = mu1.pow(2)
    mu2_sq = mu2.pow(2)
    mu1_mu2 = mu1*mu2

    sigma1_sq = torch.nn.functional.conv2d(X_a * X_a, window, padding=window_size//2, groups=channel) - mu1_sq
    sigma2_sq = torch.nn.functional.conv2d(X_b * X_b, window, padding=window_size//2, groups=channel) - mu2_sq
    sigma12 = torch.nn.functional.conv2d(X_a * X_b, window, padding=window_size//2, groups=channel) - mu1_mu2

    ssim_map = ((2*mu1_mu2 + C1)*(2*sigma12 + C2))/((mu1_sq + mu2_sq + C1)*(sigma1_sq + sigma2_sq + C2))

    if size_average:
        return ssim_map.mean()
    else:
        return ssim_map.mean(1).mean(1).mean(1)