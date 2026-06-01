def test_package_imports_and_has_version():
    import build

    assert hasattr(build, "__version__")
    assert isinstance(build.__version__, str)
    assert build.__version__
