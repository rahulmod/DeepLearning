#Calls ready-made R function for the Holt-Winter method in a time series
import rpy2.robjects as ro
ro.r('data(input)')
ro.r('x <-HoltWinters(input)')