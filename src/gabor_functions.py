import numpy as np

# All implementation of this file come from the
# great explanation of Peter Kovesi.
#
# For more information, see:
# http://www.peterkovesi.com/matlabfns/index.html


def get_gabor_kernel(ksize, sigma, theta, lambd, gamma, psi, ktype=np.float):
    '''
    Returns Gabor filter coefficients.
    Implementation by: Cristiano Nunes <cfgnunes@gmail.com>.

    ksize: Size of the filter returned.
    sigma: Standard deviation of the gaussian envelope.
    theta: Orientation of the normal to the
           parallel stripes of a Gabor function.
    lambd: Wavelength of the sinusoidal factor.
    gamma: Spatial aspect ratio.
    psi: Phase offset.
    ktype: Type of filter coefficients (e.g. np.float).
    '''

    costheta = np.cos(theta)
    sintheta = np.sin(theta)

    width, height = ksize
    half_width = int(width / 2)
    half_height = int(height / 2)

    # Kernel matrix
    kernel = np.zeros((height, width), ktype)

    const_x = -0.5 / (sigma ** 2)
    const_y = -0.5 / ((float(sigma) / gamma) ** 2)
    const_scale = np.pi * 2.0 / lambd

    for i in range(height):
        for j in range(width):
            # Use symmetric references
            y, x = i - half_height, j - half_width

            # Rotate the filter
            xr = x * costheta + y * sintheta
            yr = -x * sintheta + y * costheta

            # Gabor equation
            value = np.exp(const_x * xr * xr + const_y * yr * yr) * \
                np.cos(const_scale * xr + psi)

            kernel.itemset(i, j, value)

    return kernel


def get_log_gabor_kernel(ksize, f0, theta0, sigma_over_f, sigma_theta0,
                         ktype=np.float):
    '''
    Returns Log-Gabor filter coefficients.
    Implementation by: Cristiano Nunes <cfgnunes@gmail.com>.

    ksize: Size of the filter returned.
    f0: The center frequency of the filter.
    theta0: Orientation angle of the filter.
    sigma_over_f: Scale bandwidth (sigma_f / f0)
    sigma_theta: Angular bandwidth.
    ktype: Type of filter coefficients (e.g. np.float).
    '''

    cols, rows = ksize

    # Creating the matrix kernel
    array_cols = np.arange(-cols / 2, cols / 2, dtype=ktype)
    array_rows = np.arange(-rows / 2, rows / 2, dtype=ktype)
    x, y = np.meshgrid(
        array_cols / np.min((cols, rows)), array_rows / np.min((cols, rows)))

    # Matrix values contain "normalized" radius
    # values ranging from 0 at the centre to
    # 0.5 at the boundary.

    radius = np.hypot(x, y)

    # Get rid of the 0 radius value in the middle
    # so that taking the log of the radius will
    # not cause trouble.

    radius.itemset(int(rows / 2), int(cols / 2), 1.0)

    # Log-Gabor equation: radial component.
    lg_radial_numerator = -(np.log(radius / f0)) ** 2
    lg_radial_denominator = 2 * np.log(sigma_over_f) ** 2
    lg_radial = np.exp(lg_radial_numerator / lg_radial_denominator)

    # Set the value at the 0 frequency point of the filter back to zero
    # (undo the radius fudge).
    lg_radial.itemset(int(rows / 2), int(cols / 2), 0.0)

    # Matrix values contain polar angle.
    theta = np.arctan2(-y, x)

    sintheta = np.sin(theta)
    costheta = np.cos(theta)

    angl = theta0
    sinangl = np.sin(angl)
    cosangl = np.cos(angl)

    # For each point in the filter matrix
    # calculate the angular distance from the
    # specified filter orientation.
    # To overcome the angular wrap-around problem
    # sine difference and cosine difference values are
    # first computed and then the atan2 function
    # is used to determine angular distance.

    ds = sintheta * cosangl - costheta * sinangl  # Difference in sine.
    dc = costheta * cosangl + sintheta * sinangl  # Difference in cosine.
    dtheta = abs(np.arctan2(ds, dc))  # Absolute angular distance.

    # Log-Gabor equation: angular component
    lg_angular = np.exp((-dtheta ** 2) / (2 * sigma_theta0 ** 2))

    # Construct a low-pass filter that is as large as possible,
    # yet falls away to zero at the boundaries.
    lp = _low_pass_filter(ksize, 0.45, 15, ktype)

    # Final result
    kernel = lg_radial * lg_angular * lp

    return kernel


def _low_pass_filter(fsize, cutoff, n, ktype=np.float):
    '''
    Returns a low-pass butterworth filter.
    Implementation by: Cristiano Nunes <cfgnunes@gmail.com>.

    fsize: Size of the filter returned.
    cutoff: is the cutoff frequency of the filter (0.0 to 0.5).
    n: the order of the filter,
       the higher n is the sharper the transition is.
    ktype: Type of filter coefficients (e.g. np.float).
    '''

    if cutoff < 0 or cutoff > 0.5:
        raise Exception("Cutoff frequency must be between 0 and 0.5.")

    if n < 1:
        raise Exception('n must be an integer >= 1.')

    cols, rows = fsize

    # Creating the matrix filter
    array_cols = np.arange(-cols / 2, cols / 2, dtype=ktype)
    array_rows = np.arange(-rows / 2, rows / 2, dtype=ktype)
    x, y = np.meshgrid(array_cols / cols, array_rows / rows)

    # A matrix with every pixel = radius relative to centre.
    radius = np.hypot(x, y)

    # Filter
    f = 1.0 / (1.0 + (radius / cutoff) ** (2 * n))

    return f


def get_gabor_filterbank(ksize, n_scales, n_orientations, min_sigma=1.0,
                         scale_factor=3, gamma=1.0, psi=np.pi * 0.5,
                         ktype=np.float):
    '''
    Returns a Gabor filter bank.
    Implementation by: Cristiano Nunes <cfgnunes@gmail.com>.

    ksize: Size of the filters.
    n_scales: Number of scales.
    n_orientations: Number of orientations.
    min_sigma: Sigma of smallest scale filter
    scale_factor: Scaling factor between successive filters
    gamma: Spatial aspect ratio of filters.
    psi: Phase offset of filters.
    ktype: Type of filter coefficients (e.g. np.float).
    '''

    filters = []

    for scale in range(n_scales):
        for orientation in range(n_orientations):
            sigma = min_sigma + scale
            lambd = sigma * scale_factor
            theta = 2 * np.pi * (orientation / float(n_orientations))

            f = get_gabor_kernel(
                ksize, sigma, theta, lambd, gamma, psi, ktype)
            filters.append(f)

    return filters


def get_log_gabor_filterbank(ksize, n_scales, n_orientations,
                             min_wavelength=3, scale_factor=1.6,
                             sigma_over_f=0.75, sigma_theta=1,
                             ktype=np.float):
    '''
    Returns a Log-Gabor filter bank.
    Implementation by: Cristiano Nunes <cfgnunes@gmail.com>.

    ksize: Size of the filters.
    n_scales: Number of scales.
    n_orientations: Number of orientations.
    min_wavelength: Wavelength of smallest scale filter
    scale_factor: Scaling factor between successive filters
    sigma_over_f: Scale bandwidth (sigma_f / f0)
    sigma_theta: Angular bandwidth
    ktype: Type of filter coefficients (e.g. np.float).
    '''

    filters = []

    for scale in range(n_scales):
        for orientation in range(n_orientations):
            wavelength = min_wavelength * scale_factor ** scale
            f0 = 1.0 / wavelength
            theta0 = 2 * np.pi * (orientation / float(n_orientations))

            f = get_log_gabor_kernel(
                ksize, f0, theta0, sigma_over_f, sigma_theta, ktype)
            filters.append(f)

    return filters
