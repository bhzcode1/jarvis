from config.settings import Settings, validate_runtime_settings


def test_validate_runtime_settings_detects_bad_values() -> None:
    settings = Settings(
        channels=0,
        sample_rate=4000,
        recording_duration_seconds=0,
        tts_volume=1.5,
        ai_temperature=3.0,
        ai_max_tokens=0,
        wake_word_enabled=True,
        porcupine_access_key=None,
        system_control_enabled=True,
        system_shutdown_delay_seconds=1,
    )

    warnings = validate_runtime_settings(settings=settings)
    assert any("CHANNELS must be >= 1" in item for item in warnings)
    assert any("SAMPLE_RATE is very low" in item for item in warnings)
    assert any("RECORDING_DURATION_SECONDS must be greater than 0" in item for item in warnings)
    assert any("TTS_VOLUME should be between 0.0 and 1.0" in item for item in warnings)
    assert any("AI_TEMPERATURE should be between 0.0 and 2.0" in item for item in warnings)
    assert any("AI_MAX_TOKENS must be greater than 0" in item for item in warnings)
    assert any("Wake word is enabled but PORCUPINE_ACCESS_KEY is missing" in item for item in warnings)
    assert any("SYSTEM_SHUTDOWN_DELAY_SECONDS should be at least 5" in item for item in warnings)
