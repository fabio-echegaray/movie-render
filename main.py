import matplotlib.pyplot as plt
from movierender.render import MovieRenderer
from movierender import overlays as ovl
from movierender.render.pipelines import CompositeRGBImage

alexa_488 = [.29, 1., 0]
alexa_594 = [1., .61, 0]
alexa_647 = [.83, .28, .28]
hoechst_33342 = [0, .57, 1.]
red = [1, 0, 0]
green = [0, 1, 0]
blue = [0, 0, 1]

filename = "/Users/Fabio/data/lab/cycles/MAX_Sas6-GFP_Sqh-mCh_WT_PE_20210211.mvd2 - Series 4 - Zmax.tif"
fig = plt.figure(frameon=False, figsize=(10, 10))
movren = MovieRenderer(file=filename,
                       fig=fig,
                       fps=15,
                       # show_axis=True,
                       bitrate="10M",
                       fontdict={'size': 12}) + \
         ovl.ScaleBar(um=10, lw=3, xy=(1, 2)) + \
         ovl.Timestamp(xy=(1, 52), string_format="mm:ss", va='center') + \
         CompositeRGBImage(channeldict={
             'Sqh-mCherry': {
                 'id':        0,
                 'color':     red,
                 'rescale':   True,
                 'intensity': 0.5
                 },
             'Sas6-GFP':    {
                 'id':        1,
                 'color':     green,
                 'rescale':   True,
                 'intensity': 0.5
                 },
             })
movren.render(filename=filename + ".mp4", test=True)
