import matplotlib.pyplot as plt
from movierender.render import MovieRenderer
from movierender import overlays as ovl
from movierender.render.pipelines import CompositeRGBImage

red = [1, 0, 0]
blue = [0, 0, 1]

channel_conf = {
    'eb3': {
        'id': 0,
        'color': red,
        'intensity': 0.7
    },
    'tubulin': {
        'id': 1,
        'color': blue,
        'intensity': 0.8
    },
}

fig = plt.figure(frameon=False, figsize=(5, 5))
movren = MovieRenderer(file="test.czi",
                       fig=fig,
                       fps=10,
                       bitrate="4M",
                       fontdict={'size': 12}) + \
         CompositeRGBImage(channeldict=channel_conf) + \
         ovl.ScaleBar(um=10, lw=3, xy=(1, 2)) + \
         ovl.Timestamp(xy=(1, 30), string_format="mm:ss", va='center') + \
         ovl.Treatment(xy=(25, 30), expdict={
             'test': {
                 'on': list(range(20, 50)),
                 'color': 'red'
             },
             'turbo': {
                 'on': list(range(10, 30)),
                 'color': 'red'
             },
         })

movren.render()
