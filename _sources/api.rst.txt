API Reference
=============

This is the reference for every public interface. Except :py:func:`pytest.mark.vcr_delete_on_fail` (which is available
as a pytest marker), everything else needs to be imported from the ``pytest_vcr_delete_on_fail`` module.

.. py:module:: pytest.mark
.. py:decorator:: vcr_delete_on_fail
.. py:decorator:: vcr_delete_on_fail(target, delete_default, skip)

   The pytest marker used to specify which cassette(s) will be deleted on failure.

   .. py:currentmodule:: pytest_vcr_delete_on_fail
   .. This current module directive is needed to not make the module name of ValidTarget appear.

   :param target: the cassette(s) to delete
   :type target: :py:data:`ValidTarget`
   :param bool delete_default: whether to delete the default cassette. *Default:* ``True`` if no ``target`` is
    specified, ``False`` otherwise
   :param bool skip: whether to skip deletion of the target cassette(s). *Default:* ``False``

.. py:module:: pytest_vcr_delete_on_fail

.. py:data:: ValidTarget

   The type used by the ``target`` argument of :py:func:`pytest.mark.vcr_delete_on_fail`.

   :type: *Union[None, str, List[ValidTarget], Callable[[_pytest.python.Function], ValidTarget]]*

    This type is mainly used for type checking; it's recursively defined as follow:

    .. code-block:: python

        from typing import TypeVar, Callable, List
        from _pytest.python import Function

        ValidTarget = TypeVar(
            "ValidTarget",  # The name of the type
            None,  # It can be None: which means that no cassette will be deleted
            str,  # It can be a string: which will be interpreted as a path
            List["ValidTarget"],  # It can be a List of ValidTarget
            Callable[[Function], "ValidTarget"],  # It can be a function that returns ValidTarget
        )

    It allows for nested structures of ``List[ValidTarget]`` and ``Callable[[Function], ValidTarget]``. All of
    these are valid examples:

    .. code-block:: python

        def function_a(item: Function) -> List[str]:
            return ["c"]

        def function_b(item: Function) -> List[Union[str, Callable[[Function], List[str]]]]:
            return ["d", function_a]

        ["cassette.yaml"]
        ["cassette.yaml", None, ["a", "b"]]
        [function_a, [function_b]]


.. py:function:: delete_on_fail(cassettes, skip)

   Deletes the target cassette(s) if an Exception is raised inside this context manger code block.

   :param Optional[List[str]] cassettes: the cassette(s) to delete
   :param bool skip: whether to skip deletion of the target cassette(s). *Default:* ``False``


.. py:function:: vcr_and_dof(vcr, cassette, skip_delete, additional_delete, **kwargs)

   A convenient thin wrapper around both delete_on_fail and VCR().use_cassette: it allows to record a cassette and delete it on failure with a single context manager.

   :param VCR vcr: the ``vcr.VCR`` instance used for ``use_cassette``
   :param str cassette: the cassette to record and delete in case of failure
   :param bool skip_delete: whether to skip deletion of the target cassette(s). *Default:* ``False``
   :param List[str] additional_delete: other cassettes to delete in case of failure. *Default:* ``[]``
   :param Any kwargs: every additional named parameter will be passed to ``use_cassette``.  *Default:* ``None``


.. py:function:: get_default_cassette_path(item)

   | Return the default cassette full path given the test ``Function``.
   | Follow the convention: ``./cassettes/{module-name}/{test-class-if-any.}{test_name}.yaml``

   :param item: the ``Function`` instance that represent the current test
   :type item: _pytest.python.Function
   :return: the path of the default cassette
   :rtype: str


.. py:function:: has_class_scoped_setup_failed(item)

   Return ``True`` if test has failed because of a class scoped fixture in the setup phase.

   :param item: the ``Function`` instance that represent the current test
   :type item: _pytest.python.Function
   :return: whether the class scoped setup failed
   :rtype: bool


.. py:function:: has_class_scoped_teardown_failed(item)

   Return ``True`` if test has failed because of a class scoped fixture in the teardown phase.

   :param item: the ``Function`` instance that represent the current test
   :type item: _pytest.python.Function
   :return: whether the class scoped teardown failed
   :rtype: bool
