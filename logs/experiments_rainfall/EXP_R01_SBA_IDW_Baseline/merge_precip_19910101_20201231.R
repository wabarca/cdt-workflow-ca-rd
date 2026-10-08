suppressPackageStartupMessages({
  library(CDT)
  library(ncdf4)
})

merging.options(powerWeightIDW = 2.0)

res <- cdtMergingPrecipCMD(
  time.step = "daily",
  dates = list(from = 'range', pars = list(start = "19910101", end = "20201231")),
  station.data = list(file = "data/stations/daily_precip_cdt.csv", sep = ',', na.strings = '-99'),
  netcdf.data = list(dir = "data/satellite/chirps_daily_nc", format = "chirps_%s%s%s.nc", varid = "precip", ilon = 1, ilat = 2),
  merge.method = list(method = "SBA", nrun = 1, pass = c(1.0)),
  interp.method = list(method = "idw", nmin = 6, nmax = 16, maxdist = 1.5, use.block = FALSE, vargrd = FALSE, vgm.model = c("Sph", "Exp", "Gau")),
  auxvar = list(dem = FALSE, slope = FALSE, aspect = FALSE, lon = FALSE, lat = FALSE),
  dem.data = list(file = "data/topography/dem_srtm_elevation.nc", varid = "dem", ilon = 1, ilat = 2),
  grid = list(from = 'data', pars = NULL),
  RnoR = list(use = FALSE, wet = 1.0, smooth = TRUE),
  blank = list(data = TRUE, shapefile = "data/gis/study_area_boundary.shp"),
  output = list(dir = "D:/Workspace/CDT-8.0/output/experiments_rainfall/EXP_R01_SBA_IDW_Baseline", format = "rr_mrg_%s%s%s.nc"),
  precision = list(from.data = TRUE, prec = 'short'),
  GUI = FALSE
)

