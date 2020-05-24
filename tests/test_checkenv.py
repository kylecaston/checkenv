from checkenv import CheckEnv

def test_basic():
    instance = CheckEnv()
    instance.load_spec_file()
    print(instance)

    assert isinstance(instance, CheckEnv)
