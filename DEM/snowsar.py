from osgeo import gdal
from collections import defaultdict
import glob
import os
import matplotlib.pyplot as plt
import datetime as dt
import numpy as np
import cv2

"""
Copolar Phase Difference (CPD) and Snow-depth Analysis Code for Module 13: Advanced Image Analysis
Author: Sayantan Majumdar
Email: s.majumdar@student.utwente.nl
Student number: s6038174
Project Group: 8
Python-Version: 3.6
"""


def read_c2_matrices(dir, pattern = '*.tif'):

    """
    Read images available in <Sensor>_DDMonYY_Mat format exported from C2 matrix
    :param dir: Image directory
    :param pattern: Image file pattern. Default format is tif
    :return: Dictionary of images keyed by dates.
    """
    print('Reading files...')
    image_dict = defaultdict(lambda: [])
    dir += os.sep + pattern
    for files in glob.glob(dir):
        date = files[files.find('_') + 1: files.rfind('_')]
        date = dt.datetime.strptime(date, '%d%b%y')
        image_dict[date].append(gdal.Open(files))
    return image_dict


def calc_cpd(real_band, imag_band):

    """
    Calculate copolar phase difference (CPD)
    :param real_band: Real component of C12 in C2 matrix
    :param imag_band: Imaginary component of C12 in C2 matrix
    :return: CPD numpy array
    """
    return np.rad2deg(np.arctan2(imag_band, real_band))


def get_rmse(x, y):

    """
    Calculate RMSE
    :param x: Numpy array
    :param y: Numpy array
    :return: RMSE
    """
    mse = np.mean((x - y) ** 2)
    return np.sqrt(mse)


def calc_snow_depth(image_dict, freq = 9650E+6):

    """
    Calculate snow depth
    :param dir: Image directory
    :param freq: Radar frequency. Default 9560 MHz is set for X-band datasets
    :return: CPD and Snow-depth dictionaries keyed by dates.
    """
    print('Calculating snow depth...')
    cpd_dict = {}
    snow_depth = {}
    rmse_cpd_dict = {}
    for k, v in image_dict.items():
        cpd = []
        print('Calculating CPD for ' + str(k).split()[0] + '...')
        for images in v:
            v = calc_cpd(images.GetRasterBand(2).ReadAsArray(),
                                          images.GetRasterBand(3).ReadAsArray())
            cpd.append(cv2.blur(v, (63, 51)))
        rmse_cpd_dict[k] = get_rmse(cpd[0], cpd[1])
        cpd_dict[k] = (cpd[0] + cpd[1])/2
        snow_depth[k] = np.abs(-(3E+8)/freq * cpd_dict[k]/(4*np.pi*0.02))
    print('Calculation complete!')
    return cpd_dict, snow_depth, rmse_cpd_dict


def mean_var(value_dict, snow_depth = False):

    """
    Calculate mean and variance of the images
    :param value_dict: Dictionary of CPD or snow-depth values
    :param snow_depth: Calculation for snow depth
    :return: Mean, Mean + Sigma, Mean - Sigma dictionaries
    """
    avg = {}
    var1 = {}
    var2 = {}
    print('Calculating average...')
    for k in sorted(value_dict.keys()):
        value_dict[k] = value_dict[k][~np.isnan(value_dict[k])]
        avg[k] = np.mean(value_dict[k])
        var1[k] = avg[k] + np.sqrt(np.var(value_dict[k]))
        var2[k] = avg[k] - np.sqrt(np.var(value_dict[k]))
        if snow_depth:
            var2[k] = np.abs(var2[k])
    return avg, var1, var2


def plot_graphs(cpd_dict, sd_dict):

    """
    Plot CPD and Snow-depth graphs
    :param cpd_dict: CPD dictionary
    :param sd_dict: Snow-depth dictionary
    :return: None
    """
    avg_cpd, var_cpd1, var_cpd2 = mean_var(cpd_dict)
    avg_sd, var_sd1, var_sd2 = mean_var(sd_dict, True)
    dates = list(avg_cpd.keys())
    dates = [str(d).split()[0] for d in dates]
    plt.plot(dates, avg_cpd.values(), 'go-', label = 'mean')
    plt.plot(dates, var_cpd1.values(), 'ro-', label = 'mean+sigma')
    plt.plot(dates, var_cpd2.values(), 'bo-', label = 'mean-sigma')
    plt.xlabel('Dates')
    plt.ylabel('CPD (Degrees)')
    plt.legend()
    plt.title('Temporal variations of CPD')
    plt.show()
    plt.plot(dates, avg_sd.values(), 'go-', label = 'mean')
    plt.plot(dates, var_sd1.values(), 'ro-', label = 'mean+sigma')
    plt.plot(dates, var_sd2.values(), 'bo-', label = 'mean-sigma')
    plt.xlabel('Dates')
    plt.ylabel('Snow-depth (m)')
    plt.legend()
    plt.title('Temporal variations of Snow-depth')
    plt.show()


def plot_rmse(rmse):

    """
    Plot TDX, TSX CPD RMSE graphs
    :param rmse: RMSE numpy array
    :return: None
    """
    dates = list(rmse.keys())
    dates = [str(d).split()[0] for d in dates]
    values = []
    for k in sorted(rmse.keys()):
        values.append(rmse[k])
    plt.title('CPD RMSE')
    plt.plot(dates, values)
    plt.show()


def write_data(cpd_dict, snow_dict, image_dict):

    """
    Write outputs for CPD and Snow-depth
    :param cpd_dict: CPD dictionary
    :param snow_dict: Snow depth dictionary
    :param image_dict: Input image dictionary
    :return: None
    """
    print('\nWriting outputs...')
    if not os.path.exists('Maps'):
        os.mkdir('Maps')
    driver = gdal.GetDriverByName("GTiff")
    for k in cpd_dict.keys():
        outfile = 'Maps' + os.sep + str(k).split()[0] + '_' + 'CPD_SD' + '.tif'
        outdata = driver.CreateCopy(outfile, image_dict[k][0])
        outdata.GetRasterBand(2).WriteArray(cpd_dict[k])
        outdata.GetRasterBand(3).WriteArray(snow_dict[k])
        outdata.FlushCache()
    print('All Maps created!')


# Driver Code
image_dict = read_c2_matrices(r'C:\Users\s6038174\Downloads\ITC\SAYANTAN\shashi kumar\Exported')
cpd_dict, sd_dict, rmse_cpd_dict = calc_snow_depth(image_dict)

plt.title('CPD for 08Jun17')
plt.imshow(cpd_dict[dt.datetime.strptime('08Jun17','%d%b%y')])
plt.colorbar()
plt.show()
plt.imshow(sd_dict[dt.datetime.strptime('08Jun17','%d%b%y')])
plt.title('Snow-depth for 08Jun17')
plt.colorbar()
plt.show()
#plot_rmse(rmse_cpd_dict)
print(rmse_cpd_dict)
plot_graphs(cpd_dict, sd_dict)

write_data(cpd_dict, sd_dict, image_dict)