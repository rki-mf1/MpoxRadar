from pathosonar.logging import LoggingConfigurator


def test_remove_log():
    # Initialize logger
    LOGGER = LoggingConfigurator()
    LOGGER.remove_logger_config()


def test_set_debug():
    # Initialize logger
    LOGGER = LoggingConfigurator(debug=False)

    assert LOGGER.debug is False

    LOGGER.set_debug_mode(debug=True)

    assert LOGGER.debug is True
