import pandas as pd
import requests

yt_urls = {'pulp_fiction': 'https://www.youtube.com/watch?v=pvAhRcUofDk'}
base_comixify_url = 'https://comixify.ii.pw.edu.pl'

frames_modes = [0, 1]
rl_modes = [0, 1]
image_assessment_modes = [0, 1]
style_transfer_modes = [0, 1, 2]

results = {'clip_name': [],
           'clip_yt_url': [],
           'media_url': [],
           'frames_mode': [],
           'rl_mode': [],
           'image_assessment_mode': [],
           'style_transfer_mode': []}

for clip_name in yt_urls.keys():
    for f_mode in frames_modes:
        for rl_model in rl_modes:
            for iam_mode in image_assessment_modes:
                for st_mode in style_transfer_modes:
                    r = requests.post(base_comixify_url + '/comixify/from_yt/',
                                      data={'url': yt_urls[clip_name],
                                            'frames_mode': f_mode,
                                            'rl_mode': rl_model,
                                            'image_assessment_mode': iam_mode,
                                            'style_transfer_mode': st_mode})

                    media_url = base_comixify_url + r.json()['comic']

                    results['clip_name'].append(clip_name)
                    results['clip_yt_url'].append(yt_urls[clip_name])
                    results['media_url'].append(media_url)
                    results['frames_mode'].append(f_mode)
                    results['rl_mode'].append(rl_model)
                    results['image_assessment_mode'].append(iam_mode)
                    results['style_transfer_mode'].append(st_mode)

df = pd.DataFrame(results)
df.to_csv('yt_comix_media_urls')
