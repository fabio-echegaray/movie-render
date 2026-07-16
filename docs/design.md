# MovieRender - Design Notes

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Module Breakdown](#module-breakdown)
  - [Configuration Module](#configuration-module)
  - [Render Module](#render-module)
  - [Overlays Module](#overlays-module)
  - [Layouts Module](#layouts-module)
  - [Panel Module](#panel-module)
  - [Scripts Module](#scripts-module)
  - [Plugins Module](#plugins-module)
- [FileOps Integration](#fileops-integration)
- [Class Diagrams](#class-diagrams)
- [Communication Diagrams](#communication-diagrams)
- [Dependencies](#dependencies)

---

## Overview

**MovieRender** is a Python package for rendering microscopy data into movies (MP4), static panels (PDF) and volumetric files (OpenVDB, VTK) using declarative configuration files. It reads microscopy image files via the sister project [FileOps](https://github.com/fabio-echegaray/fileops), applies various layouts and overlays (scale bars, timestamps, ROIs, arrows, etc.), and produces publication-ready video and image outputs.

---

## Architecture

The package follows a layered architecture with clear separation of functionality:

```
User CLI (Typer)
    |
    v
Scripts Layer  (orchestration, CLI commands)
    |
    v
Layouts Layer  (figure/axes setup, overlay composition)
    |
    +---> Render Layer  (frame-by-frame rendering, image pipelines)
    |
    +---> Overlays Layer  (visual annotations on plots)
    |
    v
Config Layer   (NamedTuples for movie/panel configuration)
    |
    v
FileOps Integration  (image loading, config parsing, plugin bridge)
```

The system uses a **plugin architecture** to bridge with FileOps: MovieRender registers header reader plugins that FileOps discovers at runtime via Python entry points.

---

## Module Breakdown

### Configuration Module

**Location:** `movierender/config/`

Contains two `NamedTuple` classes that hold all parameters needed for rendering:

| Class         | Purpose                    | Key Fields                                                                                        |
| ------------- | -------------------------- | ------------------------------------------------------------------------------------------------- |
| `ConfigMovie` | Movie rendering parameters | `image_file`, `fps`, `bitrate`, `layout`, `zstack`, `zstack_fn`, `overlays`, `channels`, `frames` |
| `ConfigPanel` | Panel rendering parameters | `image_file`, `layout`, `max_columns`, `width`, `height`, `multipage`, `fontsize`, `overlays`     |

These are produced by the FileOps plugin system when parsing `.cfg` files.

---

### Render Module

**Location:** `movierender/render/`

The core rendering engine.

| Class                                                  | Purpose                                                                                                                                                                                               |
| ------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `SequentialMovieRenderer` (aliased as `MovieRenderer`) | Main renderer. Manages a matplotlib figure, iterates through frames, renders each frame by executing image pipelines and overlay plots, then assembles frames into an MP4 video using moviepy/ffmpeg. |
| `ImagePipeline` (base)                                 | Abstract base for image processing pipelines. Uses `__radd__` to compose with `MovieRenderer` via the `+=` operator. FIXME: this functionality is slightly more intricate that what you're describing here. The addition on the right allows to add overlays, image pipelines and renderers in an 'algebraic' way; much akin to ggplot. Can you update these references to__radd__ where it corresponds, and create a sub-section inside this one specifically describing this functionality? |
| `SingleImage`                                          | Pipeline that retrieves and displays a single channel from the image file.                                                                                                                            |
| `CompositeRGBImage`                                    | Pipeline that composites multiple channels into an RGB image with configurable colors and intensity scaling.                                                                                          |
| `NullImage`                                            | Placeholder pipeline that renders a blank (1x1 black) image. Used for empty grid cells.                                                                                                               |
| `PipelineException`                                    | Custom exception for pipeline errors.                                                                                                                                                                 |

**Key relationships:**

- `MovieRenderer` holds a list of `ImagePipeline` instances and `Overlay` instances
- `ImagePipeline.__radd__` enables the syntax `renderer += SingleImage(...)`
- Each frame is rendered by calling `ImagePipeline.__call__()`, then `Overlay.plot()` for each overlay

---

### Overlays Module

**Location:** `movierender/overlays/`

Visual annotations rendered on top of images.

| Class            | Purpose                                                                                                                                                         |
| ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Overlay` (base) | Base class for all overlays. Supports `__radd__` for composition with `MovieRenderer`. Provides `plot()` method and `configuration` property for serialization. |
| `ScaleBar`       | Renders a scale bar with optional label (e.g., "50 um").                                                                                                        |
| `Timestamp`      | Renders a time stamp in `hh:mm:ss` format with optional frame number.                                                                                           |
| `Text`           | Renders arbitrary text at a specified position.                                                                                                                 |
| `ImagejROI`      | Renders ImageJ ROI rectangles from `.roi` files.                                                                                                                |
| `Arrow`          | Renders an arrow annotation with configurable position, angle, length, and color.                                                                               |
| `Position`       | Renders particle positions and trajectories with fading trail effect.                                                                                           |
| `DataTimeseries` | Renders time series data plots (e.g., fluorescence over time).                                                                                                  |
| `ImageHistogram` | Renders an inset histogram of image intensities.                                                                                                                |
| `Treatment`      | Renders experimental treatment labels with colored dot indicators.                                                                                              |
| `PixelTools`     | Utility class for coordinate conversions (ratio to pixels, ratio to micrometers).                                                                               |

---

### Layouts Module

**Location:** `movierender/layouts/`

Manages figure creation, axes layout, and overlay placement for movies.

| Class                         | Purpose                                                                                                                       |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `BaseLayoutComposer`          | Abstract base. Creates the matplotlib figure, manages pending overlays, handles parallel rendering via `ProcessPoolExecutor`. |
| `LayoutCompositeComposer`     | Renders all channels as a single composite RGB image. Used for `layout = "twoch-comp"`.                                       |
| `LayoutChannelColumnComposer` | Renders each channel in a separate subplot arranged in columns. Used for `layout = "two-ch"` or `"two-col"`.                  |
| `LayoutZStackColumnComposer`  | Renders each z-slice in a separate subplot. Used for `layout = "z-N-col"`.                                                    |

**Helper:** `channel_configuration()` transforms channel render parameters into a dictionary with color, intensity, and rescale settings.

---

### Panel Module

**Location:** `movierender/layouts/panel/`

Renders static PDF panels (montages of images).

| Function/Module           | Purpose                                                                                                                                |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `render_static_montage()` | Main entry point. Creates a DataFrame of (channel, z, frame) combinations, selects layout, and renders via seaborn `FacetGrid` to PDF. |
| `_time_array.plotimg()`   | Renders a single cell in a time-array layout: loads image, applies channel coloring, overlays scale bar, timestamp, and histogram.     |
| `_z_array.plotimg()`      | Renders a single cell in a z-array layout: shows individual z-slices with overlays.                                                    |

---

### Scripts Module

**Location:** `movierender/scripts/`

CLI commands built with [Typer](https://typer.tiangolo.com/).

| Command                  | Function                        | Description                                                 |
| ------------------------ | ------------------------------- | ----------------------------------------------------------- |
| `movierender movie`      | `render_movie_cmd`              | Render a movie from a config file                           |
| `movierender panel`      | `render_panel_cmd`              | Render a static panel from a config file                    |
| `movierender file`       | `render_configuration_file_cmd` | Render all (movies, panels, projections) from a config file |
| `movierender folder`     | `render_folder_cmd`             | Render all config files in a directory                      |
| `movierender projection` | `render_projection_cmd`         | Render z-projections to TIFF files                          |

Entry point defined in `pyproject.toml`: `movierender = "movierender.scripts:render.app"`

---

### Plugins Module

**Location:** `movierender/plugins/`

Bridges MovieRender with FileOps via the plugin system.

| Class                            | Purpose                                                                                                                                                 |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `MovieHeaderReaderPlugin`        | Extends FileOps `HeaderReaderPlugin`. Parses `[MOVIE]` sections from config files into `ConfigMovie` objects. Discovers and processes overlay sections. |
| `PanelHeaderReaderPlugin`        | Extends FileOps `HeaderReaderPlugin`. Parses `[PANEL]` sections from config files into `ConfigPanel` objects.                                           |
| `ArrowOverlayHeaderReaderPlugin` | Extends FileOps `HeaderReaderPlugin`. Parses `[OVERLAY]` sections of type `arrow` into `Arrow` overlay instances.                                       |
| `OverlayPlugin`                  | Extends FileOps `BaseFileOpsPlugin`. Wraps an `Overlay` class for plugin-based instantiation.                                                           |

---

## FileOps Integration

MovieRender depends heavily on the [FileOps](https://github.com/fabio-echegaray/fileops) sister project. The integration works through:

### 1. Python Entry Points

Defined in `pyproject.toml`:

```toml
[project.entry-points.'fileops.plugins.config.types']
movie = 'movierender.config:ConfigMovie'
panel = 'movierender.config:ConfigPanel'

[project.entry-points.'fileops.plugins.config.header_readers']
movie_header_reader = 'movierender.plugins.fileops:MovieHeaderReaderPlugin'
panel_header_reader = 'movierender.plugins.fileops:PanelHeaderReaderPlugin'
arrow_overlay_header_reader = 'movierender.plugins.fileops:ArrowOverlayHeaderReaderPlugin'
```

### 2. Key FileOps APIs Used

| FileOps Module                                  | Used By                                                           | Purpose                                             |
| ----------------------------------------------- | ----------------------------------------------------------------- | --------------------------------------------------- |
| `fileops.image.ImageFile`                       | `MovieRenderer`, `SingleImage`, `CompositeRGBImage`, `PixelTools` | Image file abstraction (frames, channels, z-stacks) |
| `fileops.image.MetadataImage`                   | `SingleImage`, `ImageHistogram`                                   | Single image with metadata                          |
| `fileops.image.ops.ZProjection`                 | `ImagePipeline`                                                   | Z-projection enumeration                            |
| `fileops.image.exceptions.FrameNotFoundError`   | `MovieRenderer`, panel layouts                                    | Exception for missing frames                        |
| `fileops.export.config.read_config`             | Scripts                                                           | Parse `.cfg` files via plugin system                |
| `fileops.export.config.ConfigCopyright`         | Panel layout                                                      | Copyright metadata                                  |
| `fileops.export.config_channel_section`         | Header readers                                                    | Channel config override processing                  |
| `fileops.export.config_sections`                | Header readers                                                    | Section override processing                         |
| `fileops.plugins.HeaderReaderPlugin`            | Plugin bridge classes                                             | Base class for config section readers               |
| `fileops.plugins.base_plugin.BaseFileOpsPlugin` | `OverlayPlugin`                                                   | Base class for FileOps plugins                      |
| `fileops.logger.get_logger`                     | All modules                                                       | Logging                                             |
| `fileops.pathutils.ensure_dir`                  | `MovieRenderer`                                                   | Directory creation                                  |

### 3. Plugin Discovery Flow

1. At import time, `movierender/__init__.py` loads overlay type plugins via `entry_points(group='movierender.plugins.overlays')`
2. When `fileops.export.config.read_config()` is called, FileOps iterates its registered `header_reader_plugins`
3. FileOps finds `MovieHeaderReaderPlugin`, `PanelHeaderReaderPlugin`, and `ArrowOverlayHeaderReaderPlugin` from MovieRender's entry points
4. Each plugin's `has_valid_header()` is called to check if the config file contains relevant sections
5. Each plugin's `process()` parses the sections and returns typed configuration objects

---

## Class Diagrams

### MovieRender Class Diagram

FIXME: move ConfigModule closer to plugins to avoid arrows going over boxes.
FIXME: when possible, avoid arrows to go over boxes. Improve paths of arrows to clearly indicate they go out of a box by adding a bit of line perpendicular to the side of the box where the arrow comes out.
FIXME: ImagePipeline throws PipelineException; shouldn't the arrow be the other way around? Give your reasoning if you still think it's correct.
![MovieRender Class Diagram](figs/class_diagram_movierender.svg)

Shows the internal class hierarchy: configuration types, overlay classes, render engine, layout composers, pipeline classes, and plugin bridge classes.

### FileOps Integration Diagram

FIXME: some boxes are overlapping! Please correct this! Give them enough space to be entirely legible.
FIXME: when possible, avoid arrows to go over boxes. Improve paths of arrows to clearly indicate they go out of a box by adding a bit of line perpendicular to the side of the box where the arrow comes out.
![FileOps Integration Diagram](figs/class_diagram_fileops_integration.svg)

Shows how MovieRender integrates with FileOps: plugin registration via entry points, image loading, config parsing, and the bridge classes that connect the two packages.

---

## Communication Diagrams

### Movie Rendering Flow

FIXME: here, ConfigMovie is not being used. Also, since this is a data structure and not a proper class, it makes little sense to add it in the diagram. Remove this and any other data structures that you find in vertical lanes.
![Movie Rendering Communication Diagram](figs/communication_diagram_movie_rendering.svg)

End-to-end sequence: CLI invocation -> config parsing via FileOps plugins -> layout composer selection -> MovieRenderer creation -> frame-by-frame rendering (image pipeline + overlays) -> video assembly.

### Panel Rendering Flow

FIXME: here, ConfigPanel is not being used. Also, since this is a data structure and not a proper class, it makes little sense to add it in the diagram. Remove this and any other data structures that you find in vertical lanes.
![Panel Rendering Communication Diagram](figs/communication_diagram_panel_rendering.svg)

End-to-end sequence: CLI invocation -> config parsing -> `render_static_montage()` -> seaborn FacetGrid creation -> `plotimg()` for each cell (image loading, overlays, display) -> PDF export.

### FileOps Plugin System

FIXME: here, ConfigMovie is not being used. Also, since this is a data structure and not a proper class, it makes little sense to add it in the diagram. Remove this and any other data structures that you find in vertical lanes.
![FileOps Plugin Communication Diagram](figs/communication_diagram_fileops_plugin.svg)

Shows the plugin lifecycle: registration at import time, config file parsing via plugin registry, and overlay resolution during rendering.

---

## Dependencies

| Package                 | Purpose                                          |
| ----------------------- | ------------------------------------------------ |
| `imgfileops >= 0.3.0`   | Sister project for image file handling           |
| `matplotlib >= 3.2.0`   | Plotting and figure rendering                    |
| `moviepy >= 1.0.3, < 2` | Video assembly from frames                       |
| `numpy >= 1.16.0`       | Array operations                                 |
| `pandas >= 2`           | Data manipulation                                |
| `scikit-image ~= 0.24`  | Image processing (exposure, color)               |
| `seaborn ~= 0.13`       | Statistical visualization (FacetGrid for panels) |
| `typer >= 0.9.0`        | CLI framework                                    |
| `roifile`               | ImageJ ROI file reading                          |

---
