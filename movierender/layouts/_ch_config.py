import numpy as np


def channel_configuration(channel_render_parameters):
    ch_config = dict()
    for cix, ch_cfg in channel_render_parameters.items():
        ch_config[ch_cfg['name']] = {
            'id':        cix,
            'color':     ch_cfg['color'][1:] if (
                    isinstance(ch_cfg['color'], tuple) and
                    len(ch_cfg['color']) > 3
            ) else ch_cfg['color'],
            'intensity': float(ch_cfg['intensity']) if 'intensity' in ch_cfg else 1.0
        }
        if np.any(['rescale' in k for k in ch_cfg.keys()]):
            ch_config[ch_cfg['name']].update({
                'rescale':     ch_cfg['rescale'].lower() in ['true', 'yes']
                               if 'rescale' in ch_cfg else True
            })
            if 'rescale_min' in ch_cfg:
                ch_config[ch_cfg['name']].update({'rescale_min': float(ch_cfg['rescale_min'])})
            if 'rescale_max' in ch_cfg:
                ch_config[ch_cfg['name']].update({'rescale_max': float(ch_cfg['rescale_max'])})

        elif np.any(['gamma' in k for k in ch_cfg.keys()]):
            ch_config[ch_cfg['name']].update({
                'gamma_value': float(ch_cfg['gamma_value']) if 'gamma_value' in ch_cfg else 1.0,
                'gamma_gain':  float(ch_cfg['gamma_gain']) if 'gamma_gain' in ch_cfg else 1.0
            })
    return ch_config
