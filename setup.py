import setuptools

# with open("README.md", "r") as fh:
#     long_description = fh.read()

setuptools.setup(
    name='movierender',
    version='0.1',
    scripts=[],
    author="Fabio Echegaray",
    author_email="fabio.echegaray@gmail.com",
    description="A package for rendering images and overlay data to video. "
                "Originally designed for microscope data.",
    # long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fabio-echegaray/movie-render",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        ],
    )
