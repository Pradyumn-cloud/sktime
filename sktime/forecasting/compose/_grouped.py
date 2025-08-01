# copyright: sktime developers, BSD-3-Clause License (see LICENSE file)
"""Implements compositors for performing forecasting by group."""

from typing import Union

import pandas as pd

from sktime.base._meta import _HeterogenousMetaEstimator
from sktime.datatypes import ALL_TIME_SERIES_MTYPES, mtype_to_scitype
from sktime.forecasting.base import BaseForecaster
from sktime.forecasting.base._delegate import _DelegatedForecaster
from sktime.registry import coerce_scitype
from sktime.transformations.base import BaseTransformer

__author__ = ["fkiraly", "felipeangelimvieira"]
__all__ = ["ForecastByLevel", "GroupbyCategoryForecaster"]


class ForecastByLevel(_DelegatedForecaster):
    """Forecast by instance or panel.

    Used to apply multiple copies of ``forecaster`` by instance or by panel.

    If ``groupby="global"``, behaves like ``forecaster``.
    If ``groupby="local"``, fits a clone of ``forecaster`` per time series instance.
    If ``groupby="panel"``, fits a clone of ``forecaster`` per panel (first non-time
    level).

    The fitted forecasters can be accessed in the ``forecasters_`` attribute,
    if more than one clone is fitted, otherwise in the ``forecaster_`` attribute.

    Parameters
    ----------
    forecaster : sktime forecaster used in ForecastByLevel
        A "blueprint" forecaster, state does not change when ``fit`` is called.
    groupby : str, one of ["local", "global", "panel"], optional, default="local"
        level on which data are grouped to fit clones of ``forecaster``
        "local" = unit/instance level, one reduced model per lowest hierarchy level
        "global" = top level, one reduced model overall, on pooled data ignoring levels
        "panel" = second lowest level, one reduced model per panel level (-2)
        if there are 2 or less levels, "global" and "panel" result in the same
        if there is only 1 level (single time series), all three settings agree

    Attributes
    ----------
    forecaster_ : sktime forecaster, present only if ``groupby`` is "global"
        clone of ``forecaster`` used for fitting and forecasting
    forecasters_ : pd.DataFrame of sktime forecaster, present otherwise
        entries are clones of ``forecaster`` used for fitting and forecasting

    Examples
    --------
    >>> from sktime.forecasting.naive import NaiveForecaster
    >>> from sktime.forecasting.compose import ForecastByLevel
    >>> from sktime.utils._testing.hierarchical import _make_hierarchical
    >>> y = _make_hierarchical()
    >>> f = ForecastByLevel(NaiveForecaster(), groupby="local")
    >>> f.fit(y)
    ForecastByLevel(...)
    >>> fitted_forecasters = f.forecasters_
    >>> fitted_forecasters_alt = f.get_fitted_params()["forecasters"]
    """

    _tags = {
        "authors": ["fkiraly"],
        "requires-fh-in-fit": False,
        "capability:missing_values": True,
        "scitype:y": "both",
        "y_inner_mtype": ALL_TIME_SERIES_MTYPES,
        "X_inner_mtype": ALL_TIME_SERIES_MTYPES,
        "fit_is_empty": False,
        # CI and test flags
        # -----------------
        "tests:core": True,  # should tests be triggered by framework changes?
    }

    # attribute for _DelegatedForecaster, which then delegates
    #     all non-overridden methods are same as of getattr(self, _delegate_name)
    #     see further details in _DelegatedForecaster docstring
    _delegate_name = "forecaster_"

    def __init__(self, forecaster, groupby="local"):
        self.forecaster = forecaster
        self.groupby = groupby

        self.forecaster_ = forecaster.clone()

        super().__init__()

        self._set_delegated_tags(self.forecaster_)
        self.set_tags(**{"fit_is_empty": False})

        if groupby == "local":
            scitypes = ["Series"]
        elif groupby == "global":
            scitypes = ["Series", "Panel", "Hierarchical"]
        elif groupby == "panel":
            scitypes = ["Series", "Panel"]
        else:
            raise ValueError(
                "groupby in ForecastByLevel must be one of"
                ' "local", "global", "panel", '
                f"but found {groupby}"
            )

        mtypes = [x for x in ALL_TIME_SERIES_MTYPES if mtype_to_scitype(x) in scitypes]

        # this ensures that we convert in the inner estimator
        # but vectorization/broadcasting happens at the level of groupby
        self.set_tags(**{"y_inner_mtype": mtypes})
        self.set_tags(**{"X_inner_mtype": mtypes})

    @classmethod
    def get_test_params(cls, parameter_set="default"):
        """Return testing parameter settings for the estimator.

        Parameters
        ----------
        parameter_set : str, default="default"
            Name of the set of test parameters to return, for use in tests. If no
            special parameters are defined for a value, will return ``"default"`` set.

        Returns
        -------
        params : dict or list of dict
        """
        from sktime.forecasting.naive import NaiveForecaster

        groupbys = ["local", "panel", "global"]

        f = NaiveForecaster()

        params = [{"forecaster": f, "groupby": g} for g in groupbys]

        return params


class GroupbyCategoryForecaster(BaseForecaster, _HeterogenousMetaEstimator):
    """Choosing a global forecaster based on category or cluster of time series.

    Programmatic generalization of "cluster then apply forecaster" approach,
    or the Syntetos/Boylan heuristic to apply forecaster by categories
    smooth, erratic, intermittent, lumpy.

    Applies a series-to-primitives transformer on a given time series. Series are
    grouped by the generated value from the transformer, and the corresponding
    forecaster is used to predict the time series.

    Different from ``TransformSelectForecaster``, this compositor passes all timeseries
    of a given category to the forecaster, instead of passing only one at a time.

    Parameters
    ----------
    forecasters : dict[sktime forecasters]
        dict of forecasters with the key corresponding to categories generated
        by the given transformer and the value corresponding to a sktime forecaster.

    transformer : sktime transformer or clusterer, default = ADICVTransformer()
        A series-to-primitives sktime transformer that generates a value
        which can be used to quantify a choice of forecaster for the time series.

        If a clusterer is used, it must support cluster assignment,
        i.e, have the ``capability:predict`` tag.

        Note: To ensure correct functionality, the transformer must store the
        generated category in the first column of the returned values when
        the transform() or fit_transform() functions are called.

    fallback_forecaster : sktime forecaster | None, Optional
        A fallback forecaster that will be used if the category generated by
        the transformer does not match any of the given forecasters.

    Raises
    ------
    AssertionError: If a valid transformer (an instance of BaseTransformer)
    is not passed or if valid forecasters (instances of BaseForecaster) are not given.

    Examples
    --------
    This example showcases how the GroupbyCategoryForecaster can be utilized to select
    appropriate forecasters on the basis of the time series category determined by
    the ADICVTransformer:

    >>> from sktime.forecasting.compose import GroupbyCategoryForecaster
    >>> from sktime.forecasting.croston import Croston
    >>> from sktime.forecasting.trend import PolynomialTrendForecaster
    >>> from sktime.forecasting.naive import NaiveForecaster
    >>> from sktime.transformations.series.adi_cv import ADICVTransformer

    Importing the methods which can generate data of specific categories
    depending on their variance and average demand intervals.

    >>> from sktime.transformations.series.tests.test_adi_cv import (
    ...     _generate_erratic_series)

    The forecaster is defined which accepts a dictionary of forecasters,
    a transformer and optionally a fallback_forecaster

    >>> group_forecaster = GroupbyCategoryForecaster(
    ...     forecasters =
    ...         {"smooth": NaiveForecaster(),
    ...         "erratic": Croston(),
    ...         "intermittent": PolynomialTrendForecaster()},
    ...     transformer=ADICVTransformer(features=["class"]))

    >>> generated_data = _generate_erratic_series()

    The fit function firstly passes the data through the given transformer
    to generate a given category. This category can be seen by the variable
    self.category_.

    >>> group_forecaster = group_forecaster.fit(generated_data, fh=50)
    >>> #print(f"The chosen category is: {group_forecaster.category}")

    >>> # Print out the predicted value over the given forecasting horizon!
    >>> # print(group_forecaster.predict(fh=50, X=None))
    """

    _tags = {
        "y_inner_mtype": [
            "pd.DataFrame",
            "pd-multiindex",
            "pd_multiindex_hier",
        ],
        "X_inner_mtype": [
            "pd.DataFrame",
            "pd-multiindex",
            "pd_multiindex_hier",
        ],
        "scitype:y": "both",
        "ignores-exogeneous-X": False,
        "requires-fh-in-fit": False,
        "enforce_index_type": None,
        "authors": ["felipeangelimvieira", "shlok191"],
        "maintainers": ["felipeangelimvieira"],
        "python_version": None,
        "visual_block_kind": "parallel",
    }

    def __init__(
        self,
        forecasters,
        transformer=None,
        fallback_forecaster=None,
    ):
        # saving arguments to object storage
        if transformer is not None:
            self.transformer = transformer

        else:
            from sktime.transformations.series.adi_cv import ADICVTransformer

            self.transformer = ADICVTransformer(features=["class"])

        self.forecasters = forecasters
        self.fallback_forecaster = fallback_forecaster

        self.transformer_ = coerce_scitype(self.transformer, "transformer").clone()

        super().__init__()

        # validating passed arguments
        assert isinstance(self.transformer_, BaseTransformer)

        for forecaster in forecasters.values():
            assert isinstance(forecaster, BaseForecaster)

        # All checks OK!

        # Assigning all capabilities on the basis of the capabilities
        # of the passed forecasters
        true_if_all_tags = {
            "ignores-exogeneous-X": True,
            "X-y-must-have-same-index": True,
            "enforce_index_type": True,
            "capability:missing_values": True,
            "capability:insample": True,
            "capability:pred_int": True,
            "capability:pred_int:insample": True,
        }

        # Extrapolating values for flags that should be True if they are
        # True for all of the given forecasters!
        for tag in true_if_all_tags.keys():
            # Checking the equivalent forecaster tags
            true_for_all = True

            for forecaster in self.forecasters.values():
                # Fetching the forecaster tags
                forecaster_tags = forecaster.get_tags()

                if tag not in forecaster_tags or forecaster_tags[tag] is False:
                    true_for_all = False
                    break

            # Perform this check for the fallback forecaster too
            if fallback_forecaster is not None and (
                tag not in fallback_forecaster.get_tags()
                or fallback_forecaster.get_tags()[tag] is False
            ):
                true_for_all = False

            true_if_all_tags[tag] = true_for_all

        # Extrapolating values for flags that should be True if they are
        # True for any of the given forecasters!
        true_if_any_tags = {
            "requires-fh-in-fit": True,
            "X-y-must-have-same-index": True,
        }

        # Create a list of forecasters
        forecasters = list(self.forecasters.items())

        if self.fallback_forecaster is not None:
            forecasters.append(("", self.fallback_forecaster))

        # Update the tags by iterating through all tags
        for tag in true_if_any_tags:
            self._anytagis_then_set(tag, True, False, forecasters)

        # Update the tags
        self.set_tags(**true_if_all_tags)

        # Finally, dynamically adding implementation of probabilistic
        # functions depending on the tags set.
        if self.get_tags()["capability:pred_int"]:
            self._predict_interval = _predict_interval
            self._predict_var = _predict_var
            self._predict_proba = _predict_proba

    @property
    def _steps(self):
        return [self._coerce_estimator_tuple(self.transformer)] + self._forecasters

    @property
    def steps_(self):
        return [self._coerce_estimator_tuple(self.transformer_)] + self._forecasters

    def _fit(self, y, X=None, fh=None):
        """Fit forecaster to training data.

        private _fit containing the core logic, called from fit

        For the _fit function to work as intended, the transformer
        must generate and store the extrapolated category in the
        first column.

        Writes to self:
            Sets fitted model attributes ending in "_".

        Parameters
        ----------
        y : Pd.Series
            The target time series to which we fit the data.

        fh : ForecastingHorizon | None, optional (default=None)
            The forecasting horizon with the steps ahead to predict.

        X : Pd.Series | None, optional (default=None)
            No exogenous variables are used for this.

        Returns
        -------
        self : reference to self

        Raises
        ------
        ValueError: If the extrapolated category has no provided forecaster
        and if there is no fallback forecaster provided to the object!

        Example:

        If the passed transformer is an ADICVTransformer(), and the generated
        series is a lumpy series; however, if there is no key matching "lumpy"
        in the forecasters parameter, the fallback_forecaster will be used.
        Additionally, if the fallback_forecaster is None, a ValueError will be thrown.
        """
        # passing time series through the provided transformer!

        self.category_ = self.transformer_.fit_transform(X=y, y=X).iloc[:, 0]
        self.forecasters_ = {}

        if y.index.nlevels == 1:
            # Handle case where y is a DataFrame without panel
            self.grouped_by_category_ = [(self.category_.values[0], None)]
        else:
            self.grouped_by_category_ = self.category_.groupby(self.category_)

        for category, group in self.grouped_by_category_:
            # check if we have an available forecaster
            if category not in self.forecasters:
                if self.fallback_forecaster is None:
                    raise ValueError(
                        "Forecaster not provided for given"
                        + f"time series of type {self.category_}"
                        + "and no fallback forecaster provided to use for this case."
                    )

                # Adopt the fallback forecaster if possible
                else:
                    chosen_forecaster_ = self.fallback_forecaster.clone()

            else:
                chosen_forecaster_ = self.forecasters[category].clone()

            y_category = self._loc_group(y, group)

            X_category = None
            if X is not None:
                X_category = self._loc_group(X, group)

            # fitting the forecaster!
            chosen_forecaster_.fit(y=y_category, X=X_category, fh=fh)

            self.forecasters_[category] = chosen_forecaster_

        return self

    def _predict(self, fh, X):
        """Forecast time series at future horizon.

        private _predict containing the core logic, called from predict

        State required:
            Requires state to be "fitted".

        Accesses in self:
            Fitted model attributes ending in "_"
            self.cutoff

        Parameters
        ----------
        fh : guaranteed to be ForecastingHorizon or None, optional (default=None)
            The forecasting horizon with the steps ahead to to predict.
            If not passed in _fit, guaranteed to be passed here

        X : sktime time series object, optional (default=None)
            guaranteed to be of an mtype in self.get_tag("X_inner_mtype")
            Exogeneous time series for the forecast

        Returns
        -------
        y_pred : sktime time series object
            should be of the same type as seen in _fit, as in "y_inner_mtype" tag
            Point predictions
        """
        # Obtain the prediction values for the given horizon.

        return self._iterate_predict_method_over_categories("predict", X=X, fh=fh)

    def _update(self, y, X=None, update_params=True):
        """Update time series to incremental training data.

        Does not update the extrapolated category from the given
        transformer, and thus the chosen forecaster remains the same.

        State required:
            Requires state to be "fitted".

        Accesses in self:
            Fitted model attributes ending in "_"
            self.cutoff

        Writes to self:
            Sets fitted model attributes ending in "_", if update_params=True.
            Does not write to self if update_params=False.

        Parameters
        ----------
        y : sktime time series object
            guaranteed to be of an mtype in self.get_tag("y_inner_mtype")
            Time series with which to update the forecaster.
            if self.get_tag("scitype:y")=="univariate":
                guaranteed to have a single column/variable
            if self.get_tag("scitype:y")=="multivariate":
                guaranteed to have 2 or more columns
            if self.get_tag("scitype:y")=="both": no restrictions apply
        X :  sktime time series object, optional (default=None)
            guaranteed to be of an mtype in self.get_tag("X_inner_mtype")
            Exogeneous time series for the forecast
        update_params : bool, optional (default=True)
            whether model parameters should be updated

        Returns
        -------
        self : reference to self
        """
        for category, group in self.grouped_by_category_:
            y_category = self._loc_group(y, group)
            X_category = self._loc_group(X, group)
            self.forecasters_[category].update(
                y=y_category, X=X_category, update_params=update_params
            )
        return self

    @classmethod
    def get_test_params(cls, parameter_set="default"):
        """Return testing parameter settings for the estimator.

        Parameters
        ----------
        parameter_set : str, default="default"
            Name of the set of test parameters to return, for use in tests. If no
            special parameters are defined for a value, will return `"default"` set.
            There are currently no reserved values for forecasters.

        Returns
        -------
        params : dict or list of dict, default = {}
            Parameters to create testing instances of the class
            Each dict are parameters to construct an "interesting" test instance, i.e.,
            `MyClass(**params)` or `MyClass(**params[i])` creates a valid test instance.
            `create_test_instance` uses the first (or only) dictionary in `params`
        """
        from sktime.clustering.dbscan import TimeSeriesDBSCAN
        from sktime.forecasting.croston import Croston
        from sktime.forecasting.naive import NaiveForecaster
        from sktime.forecasting.trend import PolynomialTrendForecaster
        from sktime.transformations.series.adi_cv import ADICVTransformer

        param1 = {
            "forecasters": {
                "smooth": NaiveForecaster(),
                "erratic": PolynomialTrendForecaster(),
                "intermittent": Croston(),
                "lumpy": NaiveForecaster(),
            },
            "transformer": ADICVTransformer(features=["class"]),
            "fallback_forecaster": None,
        }

        # Attempting to utilize the fallback forecaster
        param2 = {
            "forecasters": {},
            "transformer": ADICVTransformer(features=["class"]),
            "fallback_forecaster": Croston(),
        }

        # use with clusterer
        param3 = {
            "forecasters": {},
            "transformer": TimeSeriesDBSCAN.create_test_instance(),
            "fallback_forecaster": Croston(),
        }

        params = [param1, param2, param3]
        return params

    def _iterate_predict_method_over_categories(
        self, methodname: str, X=None, **kwargs
    ):
        """
        Iterate over the forecasters and call the given method on each one.

        This method helps to avoid code duplication when implementing the
        predict, predict_interval, predict_var, and predict_proba methods.

        Parameters
        ----------
        methodname : str
            The name of the method to call on each forecaster.
        X : pd.DataFrame, optional (default=None)
            The exogenous variables to use for the forecast.
        **kwargs : dict
            Additional keyword arguments to pass to the method.

        Returns
        -------
        pd.DataFrame
            The predicted values given methodname.
        """
        y_preds = []
        for category, group in self.grouped_by_category_:
            X_category = X
            if X_category is not None:
                X_category = self._loc_group(X, group)
            else:
                X_category = None

            forecaster = self.forecasters_[category]
            y_pred = getattr(forecaster, methodname)(X=X_category, **kwargs)
            y_preds.append(y_pred)
        y_preds = pd.concat(y_preds, axis=0).sort_index()
        return y_preds

    @property
    def _forecasters(self):
        """Provides an internal list of the forecasters available.

        Each list item is a tuple of the format (category, forecaster)
        where the category for which the respective forecaster is chosen
        and the forecaster itself as the values for each tuple.

        Returns
        -------
        forecasters : list[tuple[str, strsktime forecasters]]
            The list of forecasters which is returned. Also includes the
            fallback forecaster with the category: "fallback_forecaster"
        """
        return list(self.forecasters.items()) + [
            ("fallback_forecaster", self.fallback_forecaster)
        ]

    @_forecasters.setter
    def _forecasters(self, new_forecasters):
        """Provide new values for the forecasters.

        Parameters
        ----------
        new_forecasters : list[tuple[str, strsktime forecasters]]
            The list of new forecasters to update the object's forecasters with
        """
        # Accepting in possible new forecasters
        for category, forecaster in new_forecasters:
            # We assign this in a different way
            if category != "fallback_forecaster":
                self.forecasters[category] = forecaster

            else:
                self.fallback_forecaster = forecaster

    def _loc_group(self, df: pd.DataFrame, group: Union[pd.DataFrame, None]):
        """
        Return the indexes of the given dataframe that match the given group.

        The case where the group is None is used to handle pd.DataFrame mtypes that
        do not have a panel level.

        Parameters
        ----------
        df : pd.DataFrame
            The dataframe to locate the group in.
        group : pd.DataFrame or None
            The group to locate in the dataframe.

        Returns
        -------
        pd.DataFrame
            The indexes of the dataframe that match the given group.
        """
        if df is None or group is None:
            return df
        return df.loc[df.index.droplevel(-1).map(lambda x: x in group.index),]


# Function implementations that will be added dynamically
# if the conditions are met. explained further above!
def _predict_interval(self, fh, X, coverage):
    """Compute/return prediction quantiles for a forecast.

    private _predict_interval containing the core logic,
        called from predict_interval and possibly predict_quantiles

    State required:
        Requires state to be "fitted".

    Accesses in self:
        Fitted model attributes ending in "_"
        self.cutoff

    Parameters
    ----------
    fh : guaranteed to be ForecastingHorizon
        The forecasting horizon with the steps ahead to to predict.
    X :  sktime time series object, optional (default=None)
        guaranteed to be of an mtype in self.get_tag("X_inner_mtype")
        Exogeneous time series for the forecast
    coverage : list of float (guaranteed not None and floats in [0,1] interval)
        nominal coverage(s) of predictive interval(s)

    Returns
    -------
    pred_int : pd.DataFrame
        Column has multi-index: first level is variable name from y in fit,
            second level coverage fractions for which intervals were computed.
                in the same order as in input `coverage`.
            Third level is string "lower" or "upper", for lower/upper interval end.
        Row index is fh, with additional (upper) levels equal to instance levels,
            from y seen in fit, if y_inner_mtype is Panel or Hierarchical.
        Entries are forecasts of lower/upper interval end,
            for var in col index, at nominal coverage in second col index,
            lower/upper depending on third col index, for the row index.
            Upper/lower interval end forecasts are equivalent to
            quantile forecasts at alpha = 0.5 - c/2, 0.5 + c/2 for c in coverage.
    """
    return self._iterate_predict_method_over_categories(
        "predict_interval", X=X, fh=fh, coverage=coverage
    )


def _predict_var(self, fh, X=None, cov=False):
    """Forecast variance at future horizon.

    private _predict_var containing the core logic, called from predict_var

    Parameters
    ----------
    fh : guaranteed to be ForecastingHorizon or None, optional (default=None)
        The forecasting horizon with the steps ahead to to predict.
        If not passed in _fit, guaranteed to be passed here
    X :  sktime time series object, optional (default=None)
        guaranteed to be of an mtype in self.get_tag("X_inner_mtype")
        Exogeneous time series for the forecast
    cov : bool, optional (default=False)
        if True, computes covariance matrix forecast.
        if False, computes marginal variance forecasts.

    Returns
    -------
    pred_var : pd.DataFrame, format dependent on `cov` variable
        If cov=False:
            Column names are exactly those of `y` passed in `fit`/`update`.
                For nameless formats, column index will be a RangeIndex.
            Row index is fh, with additional levels equal to instance levels,
                from y seen in fit, if y_inner_mtype is Panel or Hierarchical.
            Entries are variance forecasts, for var in col index.
            A variance forecast for given variable and fh index is a predicted
                variance for that variable and index, given observed data.
        If cov=True:
            Column index is a multiindex: 1st level is variable names (as above)
                2nd level is fh.
            Row index is fh, with additional levels equal to instance levels,
                from y seen in fit, if y_inner_mtype is Panel or Hierarchical.
            Entries are (co-)variance forecasts, for var in col index, and
                covariance between time index in row and col.
            Note: no covariance forecasts are returned between different variables.
    """
    return self._iterate_predict_method_over_categories(
        "predict_var", X=X, fh=fh, cov=cov
    )


def _predict_proba(self, fh, X, marginal=True):
    """Compute/return fully probabilistic forecasts.

    private _predict_proba containing the core logic, called from predict_proba

    Parameters
    ----------
    fh : int, list, np.array or ForecastingHorizon (not optional)
        The forecasting horizon encoding the time stamps to forecast at.
        if has not been passed in fit, must be passed, not optional
    X : sktime time series object, optional (default=None)
            Exogeneous time series for the forecast
        Should be of same scitype (Series, Panel, or Hierarchical) as y in fit
        if self.get_tag("X-y-must-have-same-index"),
            X.index must contain fh.index and y.index both
    marginal : bool, optional (default=True)
        whether returned distribution is marginal by time index

    Returns
    -------
    pred_dist : sktime BaseDistribution
        predictive distribution
        if marginal=True, will be marginal distribution by time point
        if marginal=False and implemented by method, will be joint
    """
    return self._iterate_predict_method_over_categories(
        "predict_proba", X=X, fh=fh, marginal=marginal
    )
