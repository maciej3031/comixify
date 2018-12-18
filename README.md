Repository with code for the "Comixify: Transform video into a comics" paper, that can be faound here:
https://arxiv.org/abs/1812.03473

In this paper, we propose a solution to transform a video into a comics. We approach this task using a
neural style algorithm based on Generative Adversarial Networks (GANs). Several recent works in
the field of Neural Style Transfer showed that producing an image in the style of another image is
feasible. In this paper, we build up on these works and extend the existing set of style transfer use
cases with a working application of video comixification. To that end, we train an end-to-end solution
that transforms input video into a comics in two stages. In the first stage, we propose a state-of-the-art
keyframes extraction algorithm that selects a subset of frames from the video to provide the most
comprehensive video context and we filter those frames using image aesthetic estimation engine. In
the second stage, the style of selected keyframes is transferred into a comics. To provide the most
aesthetically compelling results, we selected the most state-of-the art style transfer solution and based
on that implement our own ComixGAN framework. The final contribution of our work is a Web-based
working application of video comixification available at http://comixify.ii.pw.edu.pl
