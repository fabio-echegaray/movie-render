from movierender.overlays import Overlay
import matplotlib.pyplot as plt


class Treatment(Overlay):
    def plot(self, ax, xy=(0, 0), lw=1, fontdict=None, expdict=None, **kwargs):
        assert expdict is not None, "Experiment label parameters needed to apply this overlay."

        x0, y0 = xy
        r = self._renderer.fig.canvas.get_renderer()

        # get dimensions of the dot
        dot = plt.scatter(x0, y0, s=fontdict['size'] ** 2, c=None, lw=0)
        bb = dot.get_paths()[0].get_extents(transform=ax.transData)

        for name, settings in expdict.items():
            if self._renderer.frame in settings['on']:
                ax.scatter(x0, y0, s=fontdict['size'] ** 2, c=settings['color'], lw=lw)
            else:
                ax.scatter(x0, y0, s=fontdict['size'] ** 2, facecolor='black', edgecolor='w', lw=lw, hatch='//////')

            _x = 10 * bb.width / self._renderer.pix_per_um
            plt.annotate(f'{name}',  # this is the text
                         (x0, y0),  # this is the point to label
                         textcoords="offset points",  # how to position the text
                         xytext=(_x, 0),  # distance from text to points (x,y)
                         ha='left',  # horizontal alignment can be left, right or center
                         va='center_baseline',  # vertical can be center, top, bottom, baseline, center_baseline
                         c='white')

            y0 -= 1.5 * bb.height / self._renderer.pix_per_um
