"""Extension template for early time series classifiers.

Purpose of this implementation template:
    quick implementation of new estimators following the template
    NOT a concrete class to import! This is NOT a base class or concrete class!
    This is to be used as a "fill-in" coding template.

How to use this implementation template to implement a new estimator:
- make a copy of the template in a suitable location, give it a descriptive name.
- work through all the "todo" comments below
- fill in code for mandatory methods, and optionally for optional methods
- you can add more private methods, but do not override BaseEstimator's private methods
    an easy way to be safe is to prefix your methods with "_custom"
- change docstrings for functions and the file
- ensure interface compatibility by sktime.utils.estimator_checks.check_estimator
- once complete: use as a local library, or contribute to sktime via PR
- more details:
  https://www.sktime.net/en/stable/developer_guide/add_estimators.html

Mandatory methods to implement:
    fitting                 - _fit(self, X, y)
    predicting classes      - _predict(self, X)
    updating predictions    - _update_predict(self, X)
    performance metrics     - _score(X, y)

Optional methods to implement:
    data conversion and capabilities tags - _tags
    fitted parameter inspection           - _get_fitted_params()
    predicting class probabilities        - _predict_proba(self, X)
    updating probability predictions      - _update_predict_proba(self, X)

Testing - required for sktime test framework and check_estimator usage:
    get default parameters for test instance(s) - get_test_params()

copyright: sktime developers, BSD-3-Clause License (see LICENSE file)
"""

# todo: write an informative docstring for the file or module, remove the above
# todo: add an appropriate copyright notice for your estimator
#       estimators contributed to sktime should have the copyright notice at the top
#       estimators of your own do not need to have permissive or BSD-3 copyright

# todo: uncomment the following line, enter authors' GitHub IDs
# __author__ = [authorGitHubID, anotherAuthorGitHubID]

from sktime.classification.early_classification import BaseEarlyClassifier

# todo: add any necessary imports here


class MyEarlyTimeSeriesClassifier(BaseEarlyClassifier):
    """Custom early time series classifier. todo: write docstring.

    todo: describe your custom early time series classifier here

    Parameters
    ----------
    parama : int
        descriptive explanation of parama
    paramb : string, optional (default='default')
        descriptive explanation of paramb
    paramc : boolean, optional (default=MyOtherEstimator(foo=42))
        descriptive explanation of paramc
    """

    # optional todo: override base class estimator default tags here if necessary
    # these are the default values, only add if different to these.
    _tags = {
        "X_inner_mtype": "numpy3D",  # which type do _fit/_predict accept, usually
        # this is either "numpy3D" or "nested_univ" (nested pd.DataFrame). Other
        # types are allowable, see datatypes/panel/_registry.py for options.
        "capability:multivariate": False,
        "capability:unequal_length": False,
        "capability:missing_values": False,
        "capability:train_estimate": False,
        "capability:feature_importance": False,
        "capability:contractable": False,
        "capability:multithreading": False,
    }

    # todo: add any hyper-parameters and components to constructor
    def __init__(self, parama, paramb="default", paramc=None):
        # estimators should precede parameters
        #  if estimators have default values, set None and initialize below

        # todo: write any hyper-parameters and components to self
        self.parama = parama
        self.paramb = paramb
        # IMPORTANT: the self.params should never be overwritten or mutated from now on
        # for handling defaults etc, write to other attributes, e.g., self._paramc
        self.paramc = paramc

        # leave this as is
        super().__init__()

        # todo: optional, parameter checking logic (if applicable) should happen here
        # if writes derived values to self, should *not* overwrite self.paramc etc
        # instead, write to self._paramc, self._newparam (starting with _)
        # example of handling conditional parameters or mutable defaults:
        if self.paramc is None:
            from sktime.somewhere import MyOtherEstimator

            self._paramc = MyOtherEstimator(foo=42)
        else:
            # estimators should be cloned to avoid side effects
            self._paramc = paramc.clone()

        # todo: if tags of estimator depend on component tags, set these here
        #  only needed if estimator is a composite
        #  tags set in the constructor apply to the object and override the class
        #
        # example 1: conditional setting of a tag
        # if est.foo == 42:
        #   self.set_tags(handles-missing-data=True)
        # example 2: cloning tags from component
        #   self.clone_tags(est2, ["enforce_index_type", "handles-missing-data"])

    # todo: implement this, mandatory
    def _fit(self, X, y):
        """Fit early time series classifier to training data.

        core logic

        Parameters
        ----------
        X : Training data of type self.get_tag("X_inner_mtype")
        y : array-like, shape = [n_instances] - the class labels

        Returns
        -------
        self : reference to self.

        State change
        ------------
        creates fitted model (attributes ending in "_")
        """

        # implement here
        # IMPORTANT: avoid side effects to X, y
        #
        # Note: when interfacing a model that has fit, with parameters
        #   that are not data (X, y) or data-like,
        #   but model parameters, *don't* add as arguments to fit, but treat as follows:
        #   1. pass to constructor,  2. write to self in constructor,
        #   3. read from self in _fit,  4. pass to interfaced_model.fit in _fit

    # todo: implement this, mandatory
    def _predict(self, X):
        """Predict labels for sequences in X.

        core logic

        This method should update state_info with any values necessary to make future
        decisions. It is recommended that the previous time stamp used for each case
        should be stored in the state_info. The number of rows in state_info after the
        method has been called should match the number of input rows.

        Parameters
        ----------
        X : data not used in training, of type self.get_tag("X_inner_mtype")

        Returns
        -------
        y : predictions of labels for X, np.ndarray
        decisions : decisions on whether the prediction is sage, np.ndarray
        """

        # implement here
        # IMPORTANT: avoid side effects to X

        # At the end of the method, state_info should be updated to reflect the current
        # state in the early classifiers decision-making process on the safety of
        # predictions for cases in X.
        # i.e. the number of consecutive 'safe' decisions required to return a final
        # decision to use the returned predictions.

    # todo: implement this, mandatory
    def _update_predict(self, X):
        """Update labels for sequences in X using a larger series length.

        core logic

        Uses information from previous decisions stored in state_info. This method
        should update state_info with any values necessary to make future decisions.
        It is recommended that the previous time stamp used for each case should be
        stored in the state_info. The number of rows in state_info after the method has
        been called should match the number of input rows.

        Parameters
        ----------
        X : data not used in training, of type self.get_tag("X_inner_mtype")

        Returns
        -------
        y : predictions of labels for X, np.ndarray
        decisions : decisions on whether the prediction is sage, np.ndarray
        """

        # implement here
        # IMPORTANT: update the number of rows in state_info to math the cases in
        #            X at the beginning of the method.
        # IMPORTANT: avoid side effects to X

        # At the end of the method, state_info should be updated to reflect the current
        # state in the early classifiers decision-making process on the safety of
        # predictions for cases in X.
        # i.e. the number of consecutive 'safe' decisions required to return a final
        # decision to use the returned predictions.

    # todo: consider implementing this, optional
    # if you do not implement it, then the default _predict_proba will be  called.
    # the default simply calls predict and sets probas to 0 or 1.
    def _predict_proba(self, X):
        """Predicts labels probabilities for sequences in X.

        This method should update state_info with any values necessary to make future
        decisions. It is recommended that the previous time stamp used for each case
        should be stored in the state_info. The number of rows in state_info after the
        method has been called should match the number of input rows.

        Default behaviour is to call _predict and set the predicted class probability
        to 1, other class probabilities to 0. Override if better estimates are
        obtainable.

        Parameters
        ----------
        X : data to predict y with, of type self.get_tag("X_inner_mtype")

        Returns
        -------
        y : predictions of probabilities for class values of X, np.ndarray
        decisions : decisions on whether the prediction is sage, np.ndarray
        """

        # implement here
        # IMPORTANT: avoid side effects to X

        # At the end of the method, state_info should be updated to reflect the current
        # state in the early classifiers decision-making process on the safety of
        # predictions for cases in X.
        # i.e. the number of consecutive 'safe' decisions required to return a final
        # decision to use the returned predictions.

    # todo: consider implementing this, optional
    # if you do not implement it, then the default _update_predict_proba will be called.
    # the default simply calls predict and sets probas to 0 or 1.
    def _update_predict_proba(self, X):
        """Update labels probabilities for sequences in X using a larger series length.

        Uses information from previous decisions stored in state_info. This method
        should update state_info with any values necessary to make future decisions.
        It is recommended that the previous time stamp used for each case should be
        stored in the state_info. The number of rows in state_info after the method has
        been called should match the number of input rows.

        Default behaviour is to call _predict and set the predicted class probability
        to 1, other class probabilities to 0. Override if better estimates are
        obtainable.

        Parameters
        ----------
        X : data to predict y with, of type self.get_tag("X_inner_mtype")

        Returns
        -------
        y : predictions of probabilities for class values of X, np.ndarray
        decisions : decisions on whether the prediction is sage, np.ndarray
        """

        # implement here
        # IMPORTANT: update the number of rows in state_info to match the cases in
        #            X at the beginning of the method.
        # IMPORTANT: avoid side effects to X

        # At the end of the method, state_info should be updated to reflect the current
        # state in the early classifiers decision-making process on the safety of
        # predictions for cases in X.
        # i.e. the number of consecutive 'safe' decisions required to return a final
        # decision to use the returned predictions.

    # todo: implement this, mandatory
    def _score(self, X, y):
        """Scores predicted labels against ground truth labels on X.

        Parameters
        ----------
        X : data not used in training, of type self.get_tag("X_inner_mtype")
        y : array-like, shape = [n_instances] - the class labels

        Returns
        -------
        accuracy: the accuracy of the predictions at the series length when a decision
                  is made.
        earliness: how much of the series length was required to make a prediction as a
                   proportion of the full series length.
        harmonic mean: score balancing accuracy and earliness.
        """

        # implement here
        # IMPORTANT: avoid side effects to X, y

        # HM: (2 * accuracy * (1 - earliness)) / (accuracy + (1 - earliness))

    # todo: consider implementing this, optional
    # implement only if different from default:
    #   default retrieves all self attributes ending in "_"
    #   and returns them with keys that have the "_" removed
    # if not implementing, delete the method
    #   avoid overriding get_fitted_params
    def _get_fitted_params(self):
        """Get fitted parameters.

        private _get_fitted_params, called from get_fitted_params

        State required:
            Requires state to be "fitted".

        Returns
        -------
        fitted_params : dict with str keys
            fitted parameters, keyed by names of fitted parameter
        """
        # implement here
        #
        # when this function is reached, it is already guaranteed that self is fitted
        #   this does not need to be checked separately
        #
        # parameters of components should follow the sklearn convention:
        #   separate component name from parameter name by double-underscore
        #   e.g., componentname__paramname

    # todo: return default parameters, so that a test instance can be created
    #   required for automated unit and integration testing of estimator
    @classmethod
    def get_test_params(cls, parameter_set="default"):
        """Return testing parameter settings for the estimator.

        Parameters
        ----------
        parameter_set : str, default="default"
            Name of the set of test parameters to return, for use in tests. If no
            special parameters are defined for a value, will return `"default"` set.
            Reserved values for classifiers:
                "results_comparison" - used for identity testing in some classifiers
                    should contain parameter settings comparable to "TSC bakeoff"

        Returns
        -------
        params : dict or list of dict, default = {}
            Parameters to create testing instances of the class
            Each dict are parameters to construct an "interesting" test instance, i.e.,
            `MyClass(**params)` or `MyClass(**params[i])` creates a valid test instance.
            `create_test_instance` uses the first (or only) dictionary in `params`
        """

        # todo: set the testing parameters for the estimators
        # Testing parameters can be dictionary or list of dictionaries
        #
        # this can, if required, use:
        #   class properties (e.g., inherited); parent class test case
        #   imported objects such as estimators from sktime or sklearn
        # important: all such imports should be *inside get_test_params*, not at the top
        #            since imports are used only at testing time
        #
        # The parameter_set argument is not used for most automated, module level tests.
        #   It can be used in custom, estimator specific tests, for "special" settings.
        #   For classification, this is also used in tests for reference settings,
        #       such as published in benchmarking studies, or for identity testing.
        # A parameter dictionary must be returned *for all values* of parameter_set,
        #   i.e., "parameter_set not available" errors should never be raised.
        #
        # A good parameter set should primarily satisfy two criteria,
        #   1. Chosen set of parameters should have a low testing time,
        #      ideally in the magnitude of few seconds for the entire test suite.
        #       This is vital for the cases where default values result in
        #       "big" models which not only increases test time but also
        #       run into the risk of test workers crashing.
        #   2. There should be a minimum two such parameter sets with different
        #      sets of values to ensure a wide range of code coverage is provided.
        #
        # example 1: specify params as dictionary
        # any number of params can be specified
        # params = {"est": value0, "parama": value1, "paramb": value2}
        #
        # example 2: specify params as list of dictionary
        # note: Only first dictionary will be used by create_test_instance
        # params = [{"est": value1, "parama": value2},
        #           {"est": value3, "parama": value4}]
        #
        # example 3: parameter set depending on param_set value
        #   note: only needed if a separate parameter set is needed in tests
        # if parameter_set == "special_param_set":
        #     params = {"est": value1, "parama": value2}
        #     return params
        #
        # # "default" params
        # params = {"est": value3, "parama": value4}
        # return params
