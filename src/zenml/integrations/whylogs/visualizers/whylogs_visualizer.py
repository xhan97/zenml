#  Copyright (c) ZenML GmbH 2022. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at:
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
#  or implied. See the License for the specific language governing
#  permissions and limitations under the License.
"""Implementation of the whylogs visualizer step."""

import tempfile
from typing import Any, List, Optional
import webbrowser

from whylogs.core import DatasetProfileView  # type: ignore
from whylogs.viz import NotebookProfileVisualizer

from zenml.environment import Environment
from zenml.logger import get_logger
from zenml.post_execution import StepView
from zenml.utils.enum_utils import StrEnum
from zenml.visualizers import BaseStepVisualizer

logger = get_logger(__name__)


class WhylogsPlots(StrEnum):
    """All supported whylogs plot types."""

    DISTRIBUTION = "plot_distribution"
    MISSING_VALUES = "plot_missing_values"
    UNIQUENESS = "plot_uniqueness"
    DATA_TYPES = "plot_data_types"
    STRING_LENGTH = "plot_string_length"
    TOKEN_LENGTH = "plot_token_length"
    CHAR_POS = "plot_char_pos"
    STRING = "plot_string"


class WhylogsVisualizer(BaseStepVisualizer):
    """The implementation of a Whylogs Visualizer."""

    def visualize(
        self,
        object: StepView,
        plots: Optional[List[WhylogsPlots]] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Visualize all whylogs dataset profiles present as outputs in the step view.

        Args:
            object: StepView fetched from run.get_step().
            plots: optional list of whylogs plots to visualize. Defaults to
                using all available plot types if not set
            *args: additional positional arguments to pass to the visualize
                method
            **kwargs: additional keyword arguments to pass to the visualize
                method
        """
        whylogs_artifact_datatype = (
            f"{DatasetProfileView.__module__}.{DatasetProfileView.__name__}"
        )
        for artifact_name, artifact_view in object.outputs.items():
            # filter out anything but whylogs dataset profile artifacts
            if artifact_view.data_type == whylogs_artifact_datatype:
                profile = artifact_view.read()
                # whylogs doesn't currently support visualizing multiple
                # non-related profiles side-by-side, so we open them in
                # separate viewers for now
                self.visualize_profile(artifact_name, profile, plots)

    # @staticmethod
    # def _get_plot_method(
    #     visualizer: ProfileVisualizer, plot: WhylogsPlots
    # ) -> Any:
    #     """Get the Whylogs ProfileVisualizer plot method.

    #     This will be the one corresponding to a WhylogsPlots enum value.

    #     Args:
    #         visualizer: a ProfileVisualizer instance
    #         plot: a WhylogsPlots enum value

    #     Raises:
    #         ValueError: if the supplied WhylogsPlots enum value does not
    #             correspond to a valid ProfileVisualizer plot method

    #     Returns:
    #         The ProfileVisualizer plot method corresponding to the input
    #         WhylogsPlots enum value
    #     """
    #     plot_method = getattr(visualizer, plot, None)
    #     if plot_method is None:
    #         nl = "\n"
    #         raise ValueError(
    #             f"Invalid whylogs plot type: {plot} \n\n"
    #             f"Valid and supported options are: {nl}- "
    #             f'{f"{nl}- ".join(WhylogsPlots.names())}'
    #         )
    #     return plot_method

    def visualize_profile(
        self,
        name: str,
        profile: DatasetProfileView,
        plots: Optional[List[WhylogsPlots]] = None,
    ) -> None:
        """Generate a visualization of a whylogs dataset profile.

        Args:
            name: name identifying the profile if multiple profiles are
                displayed at the same time
            profile: whylogs DatasetProfile to visualize
            plots: optional list of whylogs plots to visualize. Defaults to
                using all available plot types if not set
        """
        visualization = NotebookProfileVisualizer()
        visualization.set_profiles(target_profile_view=profile, reference_profile_view=profile)
        rendered_html = visualization.summary_drift_report()

        if Environment.in_notebook():
            rendered_html

            # if not plots:
            #     # default to using all plots if none are supplied
            #     plots = list(WhylogsPlots)

            # for column in sorted(list(profile.get_columns().keys())):
            #     for plot in plots:
            #         visualizer = ProfileVisualizer()
            #         visualizer.set_profiles([profile])
            #         plot_method = self._get_plot_method(visualizer, plot)
            #         display(plot_method(column))
        else:
            logger.warning(
                "The magic functions are only usable in a Jupyter notebook."
            )
            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".html", encoding="utf-8"
            ) as f:
                f.write(rendered_html.data)
                url = f"file:///{f.name}"
            logger.info("Opening %s in a new browser.." % f.name)
            webbrowser.open(url, new=2)
