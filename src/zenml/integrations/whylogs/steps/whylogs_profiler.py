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
"""Implementation of the whylogs profiler step."""

import datetime
from typing import Dict, Optional, Type, cast

import pandas as pd
from whylogs.core import DatasetProfileView  # type: ignore
from zenml.integrations.whylogs.data_validators.whylogs_data_validator import (
    WhylogsDataValidator,
)
from zenml.integrations.whylogs.whylabs_step_decorator import enable_whylabs
from zenml.steps.base_step import BaseStep

from zenml.steps.step_interfaces.base_analyzer_step import (
    BaseAnalyzerConfig,
    BaseAnalyzerStep,
)
from zenml.steps.utils import (
    INSTANCE_CONFIGURATION,
    PARAM_CREATED_BY_FUNCTIONAL_API,
    PARAM_ENABLE_CACHE,
    clone_step,
)


class WhylogsProfilerConfig(BaseAnalyzerConfig):
    """Config class for the WhylogsProfiler step.

    Attributes:
        dataset_timestamp: timestamp to associate with the generated
            dataset profile (Optional). The current time is used if not
            supplied.
    """

    dataset_timestamp: Optional[datetime.datetime]


class WhylogsProfilerStep(BaseAnalyzerStep):
    """Generates a whylogs data profile from a given pd.DataFrame."""

    @staticmethod
    def entrypoint(  # type: ignore[override]
        dataset: pd.DataFrame,
        config: WhylogsProfilerConfig,
    ) -> DatasetProfileView:
        """Main entrypoint function for the whylogs profiler.

        Args:
            dataset: pd.DataFrame, the given dataset
            config: the configuration of the step

        Returns:
            whylogs profile with statistics generated for the input dataset
        """
        data_validator = cast(
            WhylogsDataValidator,
            WhylogsDataValidator.get_active_data_validator(),
        )
        return data_validator.data_profiling(
            dataset, dataset_timestamp=config.dataset_timestamp
        )


def whylogs_profiler_step(
    step_name: str,
    dataset_timestamp: Optional[datetime.datetime] = None,
    log_to_whylabs: bool = False,
    dataset_id: Optional[str] = None,
) -> BaseStep:
    """Shortcut function to create a new instance of the WhylogsProfilerStep step.

    The returned WhylogsProfilerStep can be used in a pipeline to generate a
    whylogs DatasetProfileView from a given pd.DataFrame and save it as an
    artifact.

    Args:
        step_name: The name of the step
        dataset_timestamp: Timestamp to associate with the generated
            dataset profile (Optional). The current time is used if not
            supplied.
        log_to_whylabs: Set to True to enable logging to Whylabs. This is the
            same as adding the `enable_whylabs` decorator to your step.
        dataset_id: Optional dataset ID to use to upload the profile to Whylabs.

    Returns:
        a WhylogsProfilerStep step instance
    """
    step: Type[BaseStep] = clone_step(WhylogsProfilerStep, step_name)

    if log_to_whylabs:
        step = enable_whylabs(dataset_id=dataset_id)(step)

    return step(
        config=WhylogsProfilerConfig(
            dataset_timestamp=dataset_timestamp,
        )
    )
